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


def get_followers(user_id, max_results=config.MAX_FOLLOW_RESULTS):
    url = f"https://api.twitter.com/2/users/{user_id}/followers"
    func = partial(get_follows_request, url, max_results=max_results)
    return get_all_results(func, max_results)


def get_following(user_id, max_results=config.MAX_FOLLOW_RESULTS):
    url = f"https://api.twitter.com/2/users/{user_id}/following"
    func = partial(get_follows_request, url, max_results=max_results)
    return get_all_results(func, max_results)


def get_all_results(func, max_results):
    results = []
    pagination_token = None
    while True:
        response = func(pagination_token=pagination_token)
        results.extend(response["data"])
        pagination_token = response["meta"].get("next_token")
        if pagination_token is None or len(results) >= max_results:
            break
    return results


def get_follows_request(
    url, pagination_token=None, max_results=config.MAX_FOLLOW_RESULTS
):
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
