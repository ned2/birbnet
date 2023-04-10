import os
from pathlib import Path

from . import config


class RunDataset:
    def __init__(self, run_id: str | None = None, output_dir_path: os.PathLike = None):
        self.run_id = run_id or ""            
        self.output_dir_path = output_dir_path or config.DATA_PATH

    def get_user_path(self, file_name):
        return self.output_dir_path / self.run_id / "users" / file_name

    @property
    def users_path(self):
        return self.output_dir_path / self.run_id / "users"

    @property
    def crawl_stats_path(self):
        return self.output_dir_path / self.run_id / "crawl_stats.parquet"

    @property
    def edges_path(self):
        return self.output_dir_path / self.run_id / "edges.parquet"


def get_user_id_from_path(user_path: os.PathLike) -> str:
    return Path(user_path).name.split("_")[0]
