# MCP server for Orbis Prism (official SDK: https://github.com/modelcontextprotocol# Exposes prism_* tools; uses application layer + infrastructure adapters.

import json

from mcp.server.fastmcp import FastMCP

from .. import i18n
from ..application import (
    get_class as app_get_class,
    get_context_list as app_get_context_list,
    get_index_stats as app_get_index_stats,
    get_method as app_get_method,
    list_classes as app_list_classes,
    read_source as app_read_source,
    search_api as app_search_api,
)
from ..domain.constants import normalize_version
from ..infrastructure.file_config import FileConfigProvider
from ..infrastructure.sqlite_repository import SqliteIndexRepository

_config_provider = FileConfigProvider()
_index_repository = SqliteIndexRepository()


def _run_search(
    query: str,
    version: str = "release",
    limit: int = 30,
    package_prefix: str | None = None,
    kind: str | None = None,
    unique_classes: bool = False,
) -> str:
    version = normalize_version(version)
    results, err = app_search_api(
        _config_provider,
        _index_repository,
        None,
        version,
        query.strip(),
        limit=limit,
        package_prefix=package_prefix or None,
        kind=kind or None,
        unique_classes=unique_classes,
        t=i18n.t,
    )
    if err is not None:
        return json.dumps(err, ensure_ascii=False)
    return json.dumps({
        "version": version,
        "term": query.strip(),
        "count": len(results),
        "results": results,
    }, ensure_ascii=False)


def _parse_fqcn(fqcn: str) -> tuple[str, str] | None:
    s = (fqcn or "").strip()
    if not s or "." not in s:
        return None
    idx = s.rfind(".")
    return (s[:idx], s[idx + 1 :])


def _run_get_class(
    version: str,
    package: str | None = None,
    class_name: str | None = None,
    fqcn: str | None = None,
) -> str:
    version = normalize_version(version)
    p = (package or "").strip()
    c = (class_name or "").strip()
    if (fqcn or "").strip():
        parsed = _parse_fqcn(fqcn)
        if parsed:
            p, c = parsed
    if not p or not c:
        return json.dumps({"error": "missing_params", "message": "Provide package and class_name, or fqcn (e.g. com.hypixel.hytale.server.GameManager)."}, ensure_ascii=False)
    data, err = app_get_class(_config_provider, _index_repository, None, version, p, c)
    if err is not None:
        return json.dumps(err, ensure_ascii=False)
    return json.dumps({"version": version, **data}, ensure_ascii=False)


def _run_list_classes(
    version: str,
    package_prefix: str,
    prefix_match: bool = True,
    limit: int = 100,
    offset: int = 0,
) -> str:
    version = normalize_version(version)
    p = (package_prefix or "").strip()
    if not p:
        return json.dumps({"error": "missing_param", "message": "package_prefix is required"}, ensure_ascii=False)
    limit = max(1, min(int(limit), 500)) if limit is not None else 100
    offset = max(0, int(offset)) if offset is not None else 0
    classes, err = app_list_classes(_config_provider, _index_repository, None, version, p, prefix_match=prefix_match, limit=limit, offset=offset)
    if err is not None:
        return json.dumps(err, ensure_ascii=False)
    return json.dumps({
        "version": version,
        "package_prefix": p,
        "prefix_match": prefix_match,
        "count": len(classes),
        "classes": classes,
    }, ensure_ascii=False)


def _run_context_list() -> str:
    ctx = app_get_context_list(_config_provider, None)
    return json.dumps(ctx, ensure_ascii=False)


def _run_index_stats(version: str | None) -> str:
    if version and str(version).strip():
        version = normalize_version(version)
    data, err = app_get_index_stats(_config_provider, _index_repository, None, version)
    if err is not None:
        return json.dumps(err, ensure_ascii=False)
    return json.dumps(data, ensure_ascii=False)


def _run_fts_help() -> str:
    return (
        "FTS5 search syntax (prism_search):\n"
        "- Single word: matches that token.\n"
        "- Quoted phrase: \"exact phrase\" matches the exact phrase.\n"
        "- AND: term1 AND term2 (both must appear).\n"
        "- OR: term1 OR term2 (either can appear).\n"
        "- Prefix: term* matches tokens that start with 'term'.\n"
        "Examples: GameManager, \"getPlayer\" AND server, spawn OR despawn."
    )


def _run_read_source(
    version: str,
    file_path: str,
    start_line: int | None = None,
    end_line: int | None = None,
) -> str:
    version = normalize_version(version)
    payload = app_read_source(_config_provider, None, version, file_path, start_line=start_line, end_line=end_line)
    if "error" in payload:
        return json.dumps({"error": payload["error"], "message": payload["message"]}, ensure_ascii=False)
    return json.dumps(payload, ensure_ascii=False)


def _run_get_method(version: str, package: str, class_name: str, method_name: str) -> str:
    version = normalize_version(version)
    if not (package or "").strip() or not (class_name or "").strip() or not (method_name or "").strip():
        return json.dumps({"error": "missing_params", "message": "package, class_name and method_name are required"}, ensure_ascii=False)
    data, err = app_get_method(_config_provider, _index_repository, None, version, package.strip(), class_name.strip(), method_name.strip())
    if err is not None:
        return json.dumps(err, ensure_ascii=False)
    return json.dumps({"version": version, **data}, ensure_ascii=False)


def _register_tools(app: FastMCP) -> None:
    """Register prism_* tools on the given FastMCP instance with localized descriptions."""

    def prism_search(
        query: str,
        version: str = "release",
        limit: int = 30,
        package_prefix: str | None = None,
        kind: str | None = None,
        unique_classes: bool = False,
    ) -> str:
        if not query or not str(query).strip():
            return json.dumps({"error": "missing_query", "message": "query is required"}, ensure_ascii=False)
        limit = max(1, min(int(limit), 500)) if limit is not None else 30
        return _run_search(query, version=version, limit=limit, package_prefix=package_prefix, kind=kind, unique_classes=unique_classes)

    prism_search.__doc__ = i18n.t("mcp.tools.prism_search.description")
    app.tool()(prism_search)

    def prism_get_class(
        version: str,
        package: str | None = None,
        class_name: str | None = None,
        fqcn: str | None = None,
    ) -> str:
        return _run_get_class(version, package=package, class_name=class_name, fqcn=fqcn)

    prism_get_class.__doc__ = i18n.t("mcp.tools.prism_get_class.description")
    app.tool()(prism_get_class)

    def prism_list_classes(
        version: str,
        package_prefix: str,
        prefix_match: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> str:
        return _run_list_classes(version, package_prefix, prefix_match, limit=limit, offset=offset)

    prism_list_classes.__doc__ = i18n.t("mcp.tools.prism_list_classes.description")
    app.tool()(prism_list_classes)

    def prism_context_list() -> str:
        return _run_context_list()

    prism_context_list.__doc__ = i18n.t("mcp.tools.prism_context_list.description")
    app.tool()(prism_context_list)

    def prism_index_stats(version: str | None = None) -> str:
        return _run_index_stats(version)

    prism_index_stats.__doc__ = i18n.t("mcp.tools.prism_index_stats.description")
    app.tool()(prism_index_stats)

    def prism_read_source(
        version: str,
        file_path: str,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> str:
        return _run_read_source(version, file_path, start_line=start_line, end_line=end_line)

    prism_read_source.__doc__ = i18n.t("mcp.tools.prism_read_source.description")
    app.tool()(prism_read_source)

    def prism_get_method(version: str, package: str, class_name: str, method_name: str) -> str:
        return _run_get_method(version, package, class_name, method_name)

    prism_get_method.__doc__ = i18n.t("mcp.tools.prism_get_method.description")
    app.tool()(prism_get_method)

    def prism_fts_help() -> str:
        return _run_fts_help()

    prism_fts_help.__doc__ = i18n.t("mcp.tools.prism_fts_help.description")
    app.tool()(prism_fts_help)


# Default instance for stdio (host/port unused)
mcp = FastMCP("orbis-prism")
_register_tools(mcp)


def run(
    transport: str = "stdio",
    host: str = "0.0.0.0",
    port: int = 8000,
) -> None:
    """
    Start the MCP server. Uses stdio transport by default.
    If transport is "streamable-http", listens on host:port (useful for Docker).
    """
    if transport == "streamable-http":
        app = FastMCP("orbis-prism", host=host, port=port)
        _register_tools(app)
        server_to_run = app
    else:
        server_to_run = mcp
    try:
        if transport == "streamable-http":
            server_to_run.run(transport="streamable-http")
        else:
            server_to_run.run()
    except KeyboardInterrupt:
        pass  # Clean exit on close (Ctrl+C or client disconnect)
