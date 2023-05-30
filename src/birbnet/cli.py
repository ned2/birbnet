import locale
import logging
from inspect import cleandoc
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

from . import config, http_utils, data_utils, validate
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
    run_id: str = typer.Argument(
        ...,
        help="ID used to track this run for saving output and resuming",
    ),
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
):
    """Run the crawler starting at a specific user ID."""
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
    crawler.crawl()
    print(f"Retrieved {crawler.crawled_count} users from Twitter.")


@app.command()
def make_db(
    run_id: str = typer.Argument(
        ...,
        help="Run ID of dataset to transform and create a DB from.",
    ),
    table_name: str = typer.Option("users", "--table-name"),
):
    """Create a DuckDB database with cleaned & transformed results from a crawl."""
    run_dataset = data_utils.RunDataset(run_id)
    run_dataset.make_db(table_name)
    print(f"Successfully made and wrote database to {run_dataset.db_path}")


@app.command()
def crawl_stats(
    run_id: str = typer.Argument(
        ...,
        help="Run ID of dataset to generate stats for.",
    ),
    write_edges: bool = typer.Option(False, "--write-edges"),
):
    """Calculate and print statistics about the output of a target crawl."""
    run_dataset = data_utils.RunDataset(run_id)
    crawled_paths = run_dataset.users_path.glob("*.json")
    all_user_ids = set()
    edges = []
    edge_counts = []
    node_counts = []
    size = 0
    for user_file in track(list(crawled_paths)):
        with jsonlines.open(user_file, "r", loads=orjson.loads) as reader:
            user_ids = [int(user["id"]) for user in reader]
        if write_edges:
            source_user_id = data_utils.get_user_id_from_path(user_file)
            edges.extend([(source_user_id, user_id) for user_id in user_ids])
        edge_counts.append(len(user_ids))
        prev_node_count = len(all_user_ids)
        all_user_ids.update(user_ids)
        new_node_count = len(all_user_ids) - prev_node_count
        node_counts.append(new_node_count)
        size += user_file.stat().st_size
    # print stats output
    print(f"Users crawled: {len(edge_counts):>12n}")
    print(f"Nodes:         {len(all_user_ids):>12n}")
    print(f"Edges:         {sum(edge_counts):>12n}")
    print(f"Mean edges:    {round(mean(edge_counts)):>12n}")
    print(f"Median edges:  {median(edge_counts):>12n}")
    print(f"Size on disk:  {naturalsize(size):>12}")

    # write output files
    stats_df = pd.DataFrame({"nodes_counts": node_counts, "edge_counts": edge_counts})
    stats_df.to_parquet(
        run_dataset.crawl_stats_path, compression="snappy", engine="pyarrow"
    )
    if write_edges:
        edges_df = pd.DataFrame(edges, columns=["source", "target"])
        edges_df.to_parquet(
            run_dataset.edges_path, compression="snappy", engine="pyarrow"
        )


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
    """Use to Twitter API to retrieve details about a target user from their ID."""
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


@app.command()
def get_config():
    """Display the current configuration of Birbnet."""
    settings = [val for val in config.__dict__ if val.isupper()]
    padding_len = max(len(val) for val in settings) + 4
    results = []
    for setting in settings:
        value = getattr(config, setting)
        item = f"{setting:{padding_len}}{str(value)}"
        results.append(item)
    print("\n".join(results))
