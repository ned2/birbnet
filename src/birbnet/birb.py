import os
import json
from functools import partial

import requests

from . import config
from .exceptions import MisconfiguredException


def create_headers():
    if config.BEARER_TOKEN is None:
        raise MisconfiguredException("BEARER_TOKEN environment variable not set.")
    return {"Authorization": f"Bearer {config.BEARER_TOKEN}"}


def get_followers(user_id, stop_at=None):
    url = f"https://api.twitter.com/2/users/{user_id}/followers"
    func = partial(get_follows_request, url, max_results=config.MAX_RESULTS)
    return get_all_results(func, stop_at)


def get_following(user_id, stop_at=None):
    url = f"https://api.twitter.com/2/users/{user_id}/following"
    func = partial(get_follows_request, url, max_results=config.MAX_RESULTS)
    return get_all_results(func, stop_at)


def get_all_results(func, stop_at):
    results = []
    pagination_token = None
    while True:
        response = func(pagination_token=pagination_token)
        results.extend(response["data"])
        pagination_token = response["meta"].get("next_token")
        if pagination_token is None:
            break
        if stop_at is not None and len(results) >= stop_at:
            break
    return results


def get_follows_request(url, pagination_token=None, max_results=None):
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
    response = requests.get(url, headers=create_headers(), params=params)
    response.raise_for_status()
    return response.json()
