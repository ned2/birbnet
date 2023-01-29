import json
from datetime import datetime
from typing import Self

from pydantic.dataclasses import dataclass


@dataclass
class User:
    id: str
    description: str
    created_at: datetime
    name: str
    location: str | None
    username: str
    verified: bool
    protected: bool
    followers_count: int
    following_count: int
    tweet_count: int
    listed_count: int
    urls: list[str]
    mentions: list[str]
    profile_image_url: str

    @classmethod
    def from_json(cls, json_str: dict) -> Self:
        data = json.loads(json_str)
        urls = list(
            {
                url.get("expanded_url", url["url"])
                for url in data.get("entities", {}).get("url", {}).get("urls", [])
            }
            | {
                url.get("expanded_url", url["url"])
                for url in data.get("entities", {})
                .get("description", {})
                .get("urls", [])
            }
        )
        mentions = list(
            {
                mention["username"]
                for mention in data.get("entities", {})
                .get("description", {})
                .get("mentions", [])
            }
        )
        return cls(
            id=data["id"],
            description=data["description"],
            created_at=data["created_at"],
            name=data["name"],
            location=data.get("location"),
            username=data["username"],
            verified=data["verified"],
            protected=data["protected"],
            followers_count=data["public_metrics"]["followers_count"],
            following_count=data["public_metrics"]["following_count"],
            tweet_count=data["public_metrics"]["tweet_count"],
            listed_count=data["public_metrics"]["listed_count"],
            urls=urls,
            mentions=mentions,
            profile_image_url=data["profile_image_url"],
        )
