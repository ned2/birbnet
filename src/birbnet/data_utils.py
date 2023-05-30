import os
from inspect import cleandoc
from pathlib import Path

import duckdb
from duckdb import DuckDBPyConnection

from . import config


class RunDataset:
    def __init__(
        self, run_id: str | None = None, output_dir_path: os.PathLike = None
    ) -> None:
        self.run_id = run_id or ""
        self.output_dir_path = output_dir_path or config.DATA_PATH

    @property
    def dataset_path(self) -> Path:
        return self.output_dir_path / self.run_id

    @property
    def users_path(self) -> Path:
        return self.dataset_path / "users"

    @property
    def db_path(self) -> Path:
        return self.dataset_path / "duck.db"

    @property
    def crawl_stats_path(self) -> Path:
        return self.dataset_path / "crawl_stats.parquet"

    @property
    def edges_path(self) -> Path:
        return self.dataset_path / "edges.parquet"

    @property
    def users_json_glob(self):
        return self.users_path / "*.json"

    def get_user_path(self, file_name: str) -> Path:
        return self.dataset_path / "users" / file_name

    def make_duckdb_conn(self) -> DuckDBPyConnection:
        return duckdb.connect(str(self.db_path))

    def make_db(self, table_name: str) -> None:
        create_table_sql = create_duckdb_table_sql(table_name, self.users_json_glob)
        conn = self.make_duckdb_conn()
        conn.sql(create_table_sql)
        conn.close()


def get_user_id_from_path(user_path: os.PathLike) -> int:
    return int(Path(user_path).name.split("_")[0])


def create_duckdb_table_sql(table_name: str, users_json_glob: Path | str) -> str:
    return cleandoc(
        f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT * FROM (
            SELECT row_number() OVER (PARTITION BY id) AS seqnum,
                   id,
                   username,
                   name,
                   created_at,
                   date_diff('day', created_at::DATE, current_date) AS account_age,
                   public_metrics.following_count AS following_count,
                   public_metrics.followers_count AS followers_count,
                   public_metrics.tweet_count AS tweet_count,
                   public_metrics.listed_count AS listed_count,
                   verified,
                   protected,
                   location,
                   list_distinct(
                       [url.expanded_url for url in entities.url.urls] +
                       [url.expanded_url for url in entities.description.urls]
                   ) AS urls,
            FROM read_ndjson(
                '{users_json_glob}',
                columns={{
                    id: UBIGINT,
                    name: VARCHAR,
                    username: VARCHAR,
                    created_at: TIMESTAMPTZ,
                    verified: BOOLEAN,
                    protected: BOOLEAN,
                    location: VARCHAR,
                    entities: 'STRUCT(
                        url STRUCT(urls STRUCT(expanded_url VARCHAR)[]),
                        description STRUCT(urls STRUCT(expanded_url VARCHAR)[])
                    )',
                    public_metrics: 'STRUCT(
                        following_count INTEGER,
                        followers_count INTEGER,
                        tweet_count INTEGER,
                        listed_count INTEGER
                    )'
                }}
            )
        )
        WHERE seqnum = 1
        """
    )
