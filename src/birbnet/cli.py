import locale
import logging
from inspect import cleandoc
from pathlib import Path
from statistics import mean, median
from typing import Optional

import jsonlines
import orjson
import typer
from humanize import naturalsize
from rich.progress import track

from . import config, validate
from .config import DEFAULTS
from .crawler import BirbCrawler
from .exceptions import MisconfiguredException


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
    typer.echo(
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
    # TODO: write out other stats such as output location
    typer.echo(f"Retrieved {crawler.crawled_count} users from Twitter.")


@app.command()
def crawl_stats(
    path: Path = typer.Argument(
        ...,
        file_okay=False,
        exists=True,
        readable=True,
        help="Path to crawler run output for deriving stats for.",
    ),
    limit: Optional[int] = typer.Option(
        None,
        help="Number of retrieved users to limit stats to be calculated for.",
    ),
):
    all_user_ids = set()
    edge_counts = []
    crawled_paths = list(path.glob("*.json"))[:limit]
    size = 0
    for user_file in track(crawled_paths):
        with jsonlines.open(user_file, "r", loads=orjson.loads) as reader:
            user_ids = [user["id"] for user in reader]
        edge_counts.append(len(user_ids))
        all_user_ids.update(user_ids)
        size += user_file.stat().st_size
    typer.echo(f"Users crawled: {len(edge_counts):>10n}")
    typer.echo(f"Nodes:         {len(all_user_ids):>10n}")
    typer.echo(f"Edges:         {sum(edge_counts):>10n}")
    typer.echo(f"Mean edges:    {round(mean(edge_counts)):>10n}")
    typer.echo(f"Median edges:  {median(edge_counts):>10n}")
    typer.echo(f"Size on disk:  {naturalsize(size):>10}")


@app.command()
def get_config():
    settings = [val for val in config.__dict__ if val.isupper()]
    padding_len = max(len(val) for val in settings) + 4
    results = []
    for setting in settings:
        value = getattr(config, setting)
        item = f"{setting:{padding_len}}{str(value)}"
        results.append(item)
    typer.echo("\n".join(results))
