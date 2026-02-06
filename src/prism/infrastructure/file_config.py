# ConfigProvider implementation using .prism.json and environment.

from pathlib import Path

from . import config_impl


class FileConfigProvider:
    """Implements ConfigProvider using the existing config module."""

    def get_project_root(self) -> Path:
        return config_impl.get_project_root()

    def get_db_path(self, root: Path | None, version: str | None) -> Path:
        return config_impl.get_db_path(root, version)

    def get_decompiled_dir(self, root: Path | None, version: str) -> Path:
        return config_impl.get_decompiled_dir(root, version)

    def load_config(self, root: Path | None) -> dict:
        return config_impl.load_config(root)
