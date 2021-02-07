from pathlib import Path
from typing import Optional

import jsonlines
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
    stop_at: int = typer.Option(None, help="Maximum number of results to be returned")
):
    output_path = config.DATA_PATH / "followers" / f"{user_id}.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    users = birb.get_followers(user_id, stop_at=stop_at)
    with jsonlines.open(output_path, "w") as writer:
        writer.write_all(users)
    typer.echo(f"Retrieved and wrote {len(users)} to {output_path}.")


@app.command()
def get_following(
    user_id: Optional[str] = typer.Argument(
        config.SEED_USER_ID,
        callback=user_id_callback,
        help="The Twitter ID of the user to get followers of",
    ),
    stop_at: int = typer.Option(None, help="Maximum number of results to be returned")
):
    output_path = config.DATA_PATH / "following" / f"{user_id}.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    users = birb.get_following(user_id, stop_at=stop_at)
    with jsonlines.open(output_path, "w") as writer:
        writer.write_all(users)

    typer.echo(f"Retrieved and wrote {len(users)} to {output_path}.")
