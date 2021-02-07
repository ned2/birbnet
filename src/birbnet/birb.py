import os
import json
from functools import partial

import jsonlines
import requests
from ratelimit import limits, sleep_and_retry

from . import config
from .exceptions import MisconfiguredException


FIFTEEN_MINUTES = 900


# traverse graph:
# parameters: depth to proceed from seed
# start at seed
# for each person seed follows:
#   get their following list and write to disk
#   depth++


def create_headers():
    if config.BEARER_TOKEN is None:
        raise MisconfiguredException("BEARER_TOKEN environment variable not set.")
    return {"Authorization": f"Bearer {config.BEARER_TOKEN}"}


class BirbGraph:
    def __init__(self, edge_type):
        self.edge_type = edge_type

    def set_user(self, user_id):
        self.user_id = user_id

    @property
    def follow_url(self):
        return f"https://api.twitter.com/2/users/{self.user_id}/{self.edge_type}"

    @property
    def output_path(self):
        return config.DATA_PATH / self.edge_type / f"{self.user_id}.jsonl"

    def write_users(self, users):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with jsonlines.open(self.output_path, "w") as writer:
            writer.write_all(users)

    def get_users(self, stop_at=None):
        users = []
        pagination_token = None
        max_results = config.MAX_RESULTS if stop_at is None else stop_at
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

    # @sleep_and_retry
    # @limits(calls=15, period=FIFTEEN_MINUTES)
    def get_follows_request(self, pagination_token=None, max_results=None):
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
            self.follow_url, headers=create_headers(), params=params
        )
        response.raise_for_status()
        return response.json()
