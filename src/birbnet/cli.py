import locale
import logging
from inspect import cleandoc
from pathlib import Path
from statistics import mean, median
from typing import Optional

import jsonlines
import orjson
import pandas as pd
import requests
import typer
from humanize import naturalsize
from rich import print, print_json
from rich.progress import track

from . import config, http_utils, validate
from .config import DEFAULTS
from .crawler import BirbCrawler
from .exceptions import MisconfiguredException
from .models import USER_FIELDS, User


locale.setlocale(locale.LC_ALL, "")
logger = logging.getLogger(__package__)
app = typer.Typer()


def user_id_callback(value: str):
    try:
        validate.validate_user_id(value)
    except MisconfiguredException as error:
        raise typer.BadParameter(error.msg)
    return value


def edge_callback(value: str):
    try:
        validate.validate_edge(value)
    except MisconfiguredException as error:
        raise typer.BadParameter(error.msg)
    return value


@app.command()
def get_users(
    user_id: Optional[str] = typer.Option(
        config.SEED_USER_ID,
        callback=user_id_callback,
        help="The Twitter ID of the seed user to start the crawl at.",
    ),
    edge: str = typer.Option(
        "following",
        help="The direction of user relationships to crawl.",
        callback=edge_callback,
    ),
    depth: Optional[int] = typer.Option(
        DEFAULTS.crawler_depth,
        help="Crawl depth to stop at in the connected user graph.",
    ),
    run_id: Optional[str] = typer.Option(
        None,
        help="ID used to track this run for saving output and resuming",
    ),
):
    logger.setLevel(logging.INFO)
    print(
        cleandoc(
            f"""
            Running crawler with following settings:
            seed_user_id: {user_id}
            depth:        {depth}
            edge:         {edge}
            """
        )
    )
    crawler = BirbCrawler(user_id=user_id, edge=edge, depth=depth, run_id=run_id)
    # TODO: catch ctl-c etc and exit gracefully
    crawler.crawl()
    # TODO: write out other stats such as output location
    print(f"Retrieved {crawler.crawled_count} users from Twitter.")


@app.command()
def crawl_stats(
    path: Path = typer.Argument(
        ...,
        file_okay=False,
        exists=True,
        readable=True,
        help="Path to crawler run output for deriving stats for.",
    ),
    stats_path: Optional[Path] = typer.Option(
        None,
        help="If provided, writes granular of each user to supplied path as Parquet",
    ),
    limit: Optional[int] = typer.Option(
        None,
        help="Number of retrieved users to limit stats to be calculated for.",
    ),
):
    all_user_ids = set()
    edge_counts = []
    node_counts = []
    crawled_paths = list(path.glob("*.json"))[:limit]
    size = 0
    for user_file in track(crawled_paths):
        with jsonlines.open(user_file, "r", loads=orjson.loads) as reader:
            user_ids = [user["id"] for user in reader]
        edge_counts.append(len(user_ids))
        prev_node_count = len(all_user_ids)
        all_user_ids.update(user_ids)
        new_node_count = len(all_user_ids) - prev_node_count
        node_counts.append(new_node_count)
        size += user_file.stat().st_size
    if stats_path is not None:
        stats_df = pd.DataFrame(
            {"nodes_counts": node_counts, "edge_counts": edge_counts}
        )
        stats_df.to_parquet(stats_path, compression="snappy", engine="pyarrow")
    print(f"Users crawled: {len(edge_counts):>10n}")
    print(f"Nodes:         {len(all_user_ids):>10n}")
    print(f"Edges:         {sum(edge_counts):>10n}")
    print(f"Mean edges:    {round(mean(edge_counts)):>10n}")
    print(f"Median edges:  {median(edge_counts):>10n}")
    print(f"Size on disk:  {naturalsize(size):>10}")


@app.command()
def get_config():
    settings = [val for val in config.__dict__ if val.isupper()]
    padding_len = max(len(val) for val in settings) + 4
    results = []
    for setting in settings:
        value = getattr(config, setting)
        item = f"{setting:{padding_len}}{str(value)}"
        results.append(item)
    print("\n".join(results))


@app.command()
def id_lookup(
    user_id: str = typer.Argument(
        ...,
        callback=user_id_callback,
        help="The Twitter ID to lookup.",
    ),
    json: bool = typer.Option(
        False,
        help="Display JSON from API response instead of a cleaned User model.",
    ),
):
    response = requests.get(
        f"https://api.twitter.com/2/users/{user_id}",
        headers=http_utils.create_headers(),
        params=http_utils.prepare_params({"user.fields": USER_FIELDS}),
    )
    response.raise_for_status()
    data = response.json()
    if "data" not in data:
        print(f"Retrieving user with ID {user_id} failed. Response:")
        print_json(data)
    if json:
        print_json(data=response.json())
        return
    user = User.from_data(data["data"])
    print(user)
