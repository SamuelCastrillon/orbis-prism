# Use cases: get class, get method, list classes, index stats, context list.

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..ports import ConfigProvider, IndexRepository


def get_class(
    config_provider: "ConfigProvider",
    index_repository: "IndexRepository",
    root: Path | None,
    version: str,
    package: str,
    class_name: str,
) -> tuple[dict | None, dict | None]:
    """Return (class_data, None) or (None, error_dict)."""
    from ..domain.constants import normalize_version

    root = root or config_provider.get_project_root()
    version = normalize_version(version)
    db_path = config_provider.get_db_path(root, version)
    if not db_path.is_file():
        return (None, {"error": "no_db", "message": f"Database for version {version} does not exist."})
    data = index_repository.get_class_and_methods(db_path, package, class_name)
    if data is None:
        return (None, {"error": "not_found", "message": f"Class {package}.{class_name} not found."})
    return (data, None)


def get_method(
    config_provider: "ConfigProvider",
    index_repository: "IndexRepository",
    root: Path | None,
    version: str,
    package: str,
    class_name: str,
    method_name: str,
) -> tuple[dict | None, dict | None]:
    """Return (data, None) or (None, error_dict)."""
    from ..domain.constants import normalize_version

    root = root or config_provider.get_project_root()
    version = normalize_version(version)
    db_path = config_provider.get_db_path(root, version)
    if not db_path.is_file():
        return (None, {"error": "no_db", "message": f"Database for version {version} does not exist."})
    data = index_repository.get_method(db_path, package, class_name, method_name)
    if data is None:
        return (None, {"error": "not_found", "message": f"Class {package}.{class_name} not found."})
    return (data, None)


def list_classes(
    config_provider: "ConfigProvider",
    index_repository: "IndexRepository",
    root: Path | None,
    version: str,
    package_prefix: str,
    prefix_match: bool = True,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[dict] | None, dict | None]:
    """Return (classes_list, None) or (None, error_dict)."""
    from ..domain.constants import normalize_version

    root = root or config_provider.get_project_root()
    version = normalize_version(version)
    db_path = config_provider.get_db_path(root, version)
    if not db_path.is_file():
        return (None, {"error": "no_db", "message": f"Database for version {version} does not exist."})
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    classes = index_repository.list_classes(db_path, package_prefix, prefix_match=prefix_match, limit=limit, offset=offset)
    return (classes, None)


def get_index_stats(
    config_provider: "ConfigProvider",
    index_repository: "IndexRepository",
    root: Path | None,
    version: str | None,
) -> tuple[dict | None, dict | None]:
    """Return ({"version", "classes", "methods"}, None) or (None, error_dict)."""
    from ..infrastructure import config_impl as _config
    from ..domain.constants import normalize_version

    root = root or config_provider.get_project_root()
    cfg = config_provider.load_config(root)
    resolved_version = version
    if resolved_version is None:
        resolved_version = cfg.get(_config.CONFIG_KEY_ACTIVE_SERVER) or "release"
    resolved_version = normalize_version(resolved_version)
    db_path = config_provider.get_db_path(root, resolved_version)
    if not db_path.is_file():
        return (None, {"error": "no_db", "message": f"Database for version {resolved_version or 'active'} does not exist. Run prism index first."})
    classes, methods = index_repository.get_stats(db_path)
    return ({"version": resolved_version, "classes": classes, "methods": methods}, None)


def get_context_list(config_provider: "ConfigProvider", root: Path | None) -> dict:
    """Return {"indexed": [...], "active": "release"|"prerelease"}."""
    from ..infrastructure import config_impl as _config
    from ..domain.constants import VALID_SERVER_VERSIONS

    root = root or config_provider.get_project_root()
    cfg = config_provider.load_config(root)
    active = cfg.get(_config.CONFIG_KEY_ACTIVE_SERVER) or "release"
    indexed = [
        v for v in VALID_SERVER_VERSIONS
        if config_provider.get_db_path(root, v).is_file()
    ]
    return {"indexed": indexed, "active": active}
