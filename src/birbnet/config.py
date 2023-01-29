import os
from pathlib import Path

from pydantic.dataclasses import dataclass

BEARER_TOKEN = os.getenv("BIRBNET_TWITTER_BEARER_TOKEN")

TWITTER_API_KEY = os.getenv("BIRBNET_TWITTER_API_KEY")

TWITTER_API_SECRET_KEY = os.getenv("BIRBNET_TWITTER_API_SECRET_KEY")

SEED_USER_ID = os.getenv("BIRBNET_TWITTER_USER_ID")

DATA_PATH = Path(os.getenv("BIRBNET_DATA_PATH", Path.home() / "birbnet_data"))


@dataclass
class Defaults:
    crawler_depth: int = 3
    crawler_max_results: int = 1000


DEFAULTS = Defaults()
