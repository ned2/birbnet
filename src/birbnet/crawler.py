import json
import logging
import os
from datetime import datetime
from functools import cache
from pathlib import Path
from typing import Literal

import jsonlines
import requests
from pyrate_limiter import Duration, Limiter, RequestRate

from . import config
from .exceptions import MisconfiguredException

EDGE_TYPES = ["following", "followers"]
MAX_RESULTS = 1000
Edge = Literal[*EDGE_TYPES]

logger = logging.getLogger(__package__)
limiter = Limiter(RequestRate(15, 15 * Duration.MINUTE))
api_requests = 0


class BirbCrawler:
    """Class for crawling followers or following users given an initial user."""

    def __init__(
        self, edge: Edge, seed_user_id: str | None = None, depth: int = 3
    ) -> None:
        """Initialise a BirbCrawler instance.

        Arguments:
        edge -- specifies crawl direction: "following" or "followers"

        Keyword Arguments:
        seed_user_id -- user to start crawl at. if None uses BIRBNET_SEED_USER_ID.
        depth        -- crawl depth to stop at in the connected user graph
        """
        self.edge = edge
        self.seed_user_id = seed_user_id or config.SEED_USER_ID
        self.depth = depth
        self.crawled_count = 0
        self.request_count = 0

        if not self.seed_user_id:
            raise MisconfiguredException(
                "BIRBNET_SEED_USER_ID environment variable must be set if "
                "`seed_user_id` is `None`"
            )
        if not edge in EDGE_TYPES:
            raise MisconfiguredException(f"`edge` must be one of: {EDGE_TYPES}")

    @property
    def run_id(self) -> str:
        """String identifier for a run of the crawler."""
        date = datetime.now().strftime("%Y%m%d")
        return f"{self.seed_user_id}_{date}"

    # TODO: add cache
    # UserFetcher.get_users needs to be cached independently of the UserFetcher
    # instance (otherwise cache)
    def crawl(self, user_ids=None, current_depth=0) -> None:
        """Perform a crawl of specified users, or start with seed user."""
        if current_depth == self.depth:
            return
        if user_ids is None:
            user_ids = [self.seed_user_id]
        new_depth = current_depth + 1
        logger.info("Crawler at depth %d", new_depth)
        for user_id in user_ids:
            new_users = get_users(user_id, self.edge, run_id=self.run_id)
            logger.info(
                "Depth %d: retrieved %d users for user %s",
                new_depth,
                len(new_users),
                user_id,
            )
            self.crawled_count += len(new_users)
            new_user_ids = [user["id"] for user in new_users]
            self.crawl(user_ids=new_user_ids, current_depth=new_depth)


@cache
def get_users(user_id, edge, run_id=None):
    user_fetcher = UserFetcher(user_id, edge, run_id=run_id)
    users = user_fetcher.get_users()
    user_fetcher.write_users(users)
    return users


class UserFetcher:
    def __init__(
        self,
        user_id: str,
        edge: Edge,
        run_id: str | None = None,
        output_dir_path: os.PathLike | str | None = None,
    ):
        self.user_id = user_id
        self.edge = edge
        self.run_id = run_id
        self.output_dir_path = output_dir_path or config.DATA_PATH

    @property
    def request_url(self) -> str:
        return f"https://api.twitter.com/2/users/{self.user_id}/{self.edge}"

    @property
    def output_path(self) -> Path:
        file_name = f"{self.user_id}_{self.edge}.json"
        if self.run_id:
            return self.output_dir_path / self.run_id / file_name
        return self.output_dir_path / file_name

    @limiter.ratelimit("follow-lookup", delay=True)
    def get_follows_request(
        self, pagination_token: str | None = None, max_results: int = MAX_RESULTS
    ) -> dict:
        global api_requests
        user_fields = [
            "created_at",
            "description",
            "entities",
            "id",
            "location",
            "name",
            "pinned_tweet_id",
            "profile_image_url",
            "protected",
            "public_metrics",
            "url",
            "username",
            "verified",
            "withheld",
        ]
        params = {
            "max_results": max_results,
            "pagination_token": pagination_token,
            "user.fields": ",".join(user_fields),
        }
        response = requests.get(
            self.request_url, headers=create_headers(), params=params
        )
        api_requests += 1
        logger.info("Requests made: %d", api_requests)
        response.raise_for_status()
        return response.json()

    def get_users(
        self, stop_at: int | None = None, max_results: int = MAX_RESULTS
    ) -> dict:
        users = []
        pagination_token = None
        max_results = max_results if stop_at is None else min(max_results, stop_at)
        while True:
            response = self.get_follows_request(
                pagination_token=pagination_token, max_results=max_results
            )
            users.extend(response["data"])
            pagination_token = response["meta"].get("next_token")
            if pagination_token is None:
                break
            if stop_at is not None and len(users) >= stop_at:
                break
        return users

    def write_users(self, users: dict) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with jsonlines.open(self.output_path, "w") as writer:
            writer.write_all(users)


def create_headers() -> dict:
    if config.BEARER_TOKEN is None:
        raise MisconfiguredException("BEARER_TOKEN environment variable not set.")
    return {"Authorization": f"Bearer {config.BEARER_TOKEN}"}
