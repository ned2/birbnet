from pathlib import Path

import typer

from . import config
from .birb import BirbCrawler

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
    stop_at: int = typer.Option(None, help="Maximum number of results to be returned"),
):
    crawler = BirbCrawler(edge_type="followers")
    graph.set_user(user_id)
    users = graph.get_users(stop_at=stop_at)
    graph.write_users(users)
    typer.echo(f"Retrieved and wrote {len(users)} to {graph.output_path}.")


@app.command()
def get_following(
    user_id: Optional[str] = typer.Argument(
        config.SEED_USER_ID,
        callback=user_id_callback,
        help="The Twitter ID of the user to get followers of",
    ),
    stop_at: int = typer.Option(None, help="Maximum number of results to be returned"),
):
    crawler = BirbCrawler(edge_type="following")
    graph.set_user(user_id)
    users = graph.get_users(stop_at=stop_at)
    graph.write_users(users)
    typer.echo(f"Retrieved and wrote {len(users)} to {graph.output_path}.")


@app.command()
def get_users(
    user_id: str
    | None = typer.Argument(
        config.SEED_USER_ID,
        callback=user_id_callback,
        help="The Twitter ID of the seed user.",
    ),
    stop_at: int
    | None = typer.Option(None, help="Maximum number of results to be returned"),
):
    crawler = BirbCrawler(edge_type="following")
    graph.set_user(user_id)
    users = graph.get_users(stop_at=stop_at)
    graph.write_users(users)
    typer.echo(f"Retrieved and wrote {len(users)} to {graph.output_path}.")
