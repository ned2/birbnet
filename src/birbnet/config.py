import os
from pathlib import Path

BEARER_TOKEN = os.getenv("BIRBNET_TWITTER_BEARER_TOKEN")

TWITTER_API_KEY = os.getenv("BIRBNET_TWITTER_API_KEY")

TWITTER_API_SECRET_KEY = os.getenv("BIRBNET_TWITTER_API_SECRET_KEY")

SEED_USER_ID = os.getenv("BIRBNET_TWITTER_USER_ID")

DATA_PATH = Path(os.getenv("BIRBNET_DATA_PATH", Path.home() / "birbnet_data"))
