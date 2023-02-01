import logging
import os
from datetime import datetime
from functools import cache
from pathlib import Path

import jsonlines
import requests
from pyrate_limiter import Duration, Limiter, RequestRate

from . import config, validate
from .config import DEFAULTS
from .exceptions import MisconfiguredException
from .types import Edge

logger = logging.getLogger(__package__)

# 15 requests every 15 minutes plus some padding to add tolerance
limiter = Limiter(RequestRate(15, 15 * Duration.MINUTE + 10))
api_requests = 0


class BirbCrawler:
    """Class for crawling followers or following users given an initial user."""

    def __init__(
        self,
        edge: Edge,
        user_id: str | None = None,
        run_id: str | None = None,
        depth: int = DEFAULTS.crawler_depth,
    ) -> None:
        """Initialise a BirbCrawler instance.

        Arguments:
        edge       -- Specifies crawl direction: "following" or "followers".

        Keyword Arguments:
        user_id    -- User to start crawl at. if None uses BIRBNET_SEED_USER_ID.
        run_id     -- ID used to track this run for saving output and resuming.
        depth      -- Crawl depth to stop at in the connected user graph.
        """
        self.edge = edge
        self.user_id = user_id or config.SEED_USER_ID
        self.run_id = run_id
        self.depth = depth
        self.crawled_count = 0
        self.request_count = 0

        if self.run_id is None:
            date = datetime.now().strftime("%Y%m%d")
            self.run_id = f"{self.user_id}_{date}"
        validate.validate_user_id(self.user_id)
        validate.validate_edge(self.edge)

    def crawl(self, user_ids: list[str] | None = None, current_depth: int = 0) -> None:
        """Perform a crawl of specified users, or start with seed user."""
        if current_depth == self.depth:
            return
        if current_depth == 0:
            logger.info("Starting crawl with run ID: %s", self.run_id)
        if user_ids is None:
            user_ids = [self.user_id]
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
def get_users(user_id: str, edge: Edge, run_id: str | None = None):
    user_fetcher = UserFetcher(user_id, edge, run_id=run_id)
    users = user_fetcher.fetch_users()
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

    def fetch_users(
        self,
        resume: bool = True,
        stop_at: int | None = None,
        max_results: int = DEFAULTS.crawler_max_results,
    ) -> dict:
        if self.output_path.exists() and resume:
            return self.read_users()

        users = []
        pagination_token = None
        max_results = max_results if stop_at is None else min(max_results, stop_at)
        logger.info("Fetching %s for user %s", self.edge, self.user_id)
        while True:
            response = self.get_follows_request(
                pagination_token=pagination_token, max_results=max_results
            )
            if "data" not in response:
                logger.info("Failed to retrieve user %s.", self.user_id)
                break
            users.extend(response["data"])
            pagination_token = response["meta"].get("next_token")
            if pagination_token is None:
                break
            if stop_at is not None and len(users) >= stop_at:
                break
        return users

    @limiter.ratelimit("follow-lookup", delay=True)
    def get_follows_request(
        self,
        pagination_token: str | None = None,
        max_results: int = DEFAULTS.crawler_max_results,
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

    def write_users(self, users: dict, force: bool = False) -> None:
        if self.output_path.exists() and not force:
            logger.info("Skipping already retrieved data: %s", self.output_path.name)
            return
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with jsonlines.open(self.output_path, "w") as writer:
            writer.write_all(users)

    # TODO: check this works
    def read_users(self) -> dict:
        with jsonlines.open(self.output_path, "r") as reader:
            users = [user for user in reader]
        return users


def create_headers() -> dict:
    if config.BEARER_TOKEN is None:
        raise MisconfiguredException("BEARER_TOKEN environment variable not set.")
    return {"Authorization": f"Bearer {config.BEARER_TOKEN}"}
