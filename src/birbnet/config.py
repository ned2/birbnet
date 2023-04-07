import os
from pathlib import Path

from pydantic.dataclasses import dataclass

BEARER_TOKEN = os.getenv("BIRBNET_TWITTER_BEARER_TOKEN")

SEED_USER_ID = os.getenv("BIRBNET_TWITTER_USER_ID")

DATA_PATH = Path(os.getenv("BIRBNET_DATA_PATH", Path.home() / "birbnet_data"))


@dataclass
class Defaults:
    # maximum number of edges for crawler to follow
    crawler_depth: int = 3

    # number of users to return with each request to GET followers/ids endpoint.
    # maximum value is 1000. Reducing this will just serve to make your already
    # limited request quota for this endpoint less effective.
    crawler_max_results: int = 1000


DEFAULTS = Defaults()
