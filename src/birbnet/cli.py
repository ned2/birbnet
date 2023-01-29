from inspect import cleandoc
from pathlib import Path
from typing import Optional

import typer

from . import config, validate
from .config import DEFAULTS
from .crawler import BirbCrawler, Edge
from .types import Edge

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
        help="The Twitter ID of the seed user.",
    ),
    depth: Optional[int] = typer.Option(
        DEFAULTS.crawler_depth, help="Edge depth to crawl to."
    ),
    edge: str = typer.Option(
        "following",
        help="The direction of user relationships to crawl.",
        callback=edge_callback,
    ),
):
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
    crawler = BirbCrawler(seed_user_id=user_id, edge=edge, depth=depth)
    crawler.crawl()
    # TODO: write out other stats such as output location
    typer.echo(f"Retrieved and wrote {crawler.crawled_count}.")


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
