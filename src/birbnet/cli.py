import logging
from inspect import cleandoc
from typing import Optional

import typer

from . import config, validate
from .config import DEFAULTS
from .crawler import BirbCrawler
from .exceptions import MisconfiguredException

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
def get_config():
    settings = [val for val in config.__dict__ if val.isupper()]
    padding_len = max(len(val) for val in settings) + 4
    results = []
    for setting in settings:
        value = getattr(config, setting)
        item = f"{setting:{padding_len}}{str(value)}"
        results.append(item)
    typer.echo("\n".join(results))
