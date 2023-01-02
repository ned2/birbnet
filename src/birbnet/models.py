from dataclasses import dataclass
from datetime import datetime


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
    def from_json(cls, json: dict) -> Self:
        # TODO
        # union of entities.url.urls.expanded_url + entities.description.urls.expanded_url
        urls = []
        # union of entities.description.mentions
        mentions = []
        return cls(
            id=json["id"],
            description=json["description"],
            # TODO parse this
            created_at=json["created_at"],
            name=json["name"],
            location=json["location"],
            username=json.get("username"),
            verified=json["verified"],
            protected=json["protected"],
            followers_count=json["public_metrics"]["followers_count"],
            following_count=json["public_metrics"]["following_count"],
            tweet_count=json["public_metrics"]["tweet_count"],
            listed_count=json["public_metrics"]["listed_count"],
            urls=urls,
            mentions=mentions,
            profile_image_url=json["profile_image_url"],
        )
