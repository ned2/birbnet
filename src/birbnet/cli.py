from pathlib import Path
from typing import Optional

import typer

from . import birb
from . import config


app = typer.Typer()


def user_id_callback(value: str):
    if not value.isdigit():
        raise typer.BadParameter("User ID must be be a string of integers.")
    return value


@app.command()
def get_followers(
    user_id: Optional[str] = typer.Argument(
        config.SEED_USER_ID,
        callback=user_id_callback,
        help="The Twitter ID of the user to query",
    ),
    max_results: int = typer.Option(
        config.MAX_FOLLOW_RESULTS, help="Maximum number of results to be returned"
    ),
    output: Path = typer.Option(
        config.DATA_PATH / "followers.jsonl",
        dir_okay=False,
        writable=True,
        help="File to write results to.",
    ),
):
    users = birb.get_followers(user_id, max_results=max_results)
    typer.echo(f"Retrieved {len(users)}")

    
@app.command()
def get_following(
    user_id: Optional[str] = typer.Argument(
        config.SEED_USER_ID,
        callback=user_id_callback,
        help="The Twitter ID of the user to get followers of",
    ),
    max_results: int = typer.Option(
        config.MAX_FOLLOW_RESULTS, help="Maximum number of results to be returned"
    ),
    output: Path = typer.Option(
        config.DATA_PATH / "following.jsonl",
        dir_okay=False,
        writable=True,
        help="File to write results to.",
    ),
):
    users = birb.get_followers(user_id, max_results=max_results)
    typer.echo(f"Retrieved {len(users)}")
