# Servidor MCP para Orbis Prism (SDK oficial: https://github.com/modelcontextprotocol/python-sdk).
# Expone el tool prism_search para buscar en la API indexada de Hytale.
# Compatible con mcp>=1.0 (v1.x usa FastMCP; v2 usa MCPServer).
# Transporte: stdio (por defecto) o streamable-http (útil para Docker).

import json

from mcp.server.fastmcp import FastMCP

from . import config
from . import db
from . import search


def _run_search(
    query: str,
    version: str = "release",
    limit: int = 30,
    package_prefix: str | None = None,
    kind: str | None = None,
) -> str:
    """
    Ejecuta búsqueda FTS5 mediante la capa de acceso (search.search_api).
    package_prefix y kind son filtros opcionales. Devuelve JSON string o dict de error.
    """
    if version not in config.VALID_SERVER_VERSIONS:
        version = "release"
    results, err = search.search_api(
        None,
        version,
        query.strip(),
        limit=limit,
        package_prefix=package_prefix or None,
        kind=kind or None,
    )
    if err is not None:
        return json.dumps(err, ensure_ascii=False)
    return json.dumps({
        "version": version,
        "term": query.strip(),
        "count": len(results),
        "results": results,
    }, ensure_ascii=False)


def _run_get_class(version: str, package: str, class_name: str) -> str:
    """Devuelve la clase exacta (package, class_name, kind, file_path) y todos sus métodos. JSON o error."""
    if version not in config.VALID_SERVER_VERSIONS:
        version = "release"
    if not (package or "").strip() or not (class_name or "").strip():
        return json.dumps({"error": "missing_params", "message": "package and class_name are required"}, ensure_ascii=False)
    root = config.get_project_root()
    db_path = config.get_db_path(root, version)
    if not db_path.is_file():
        return json.dumps({"error": "no_db", "message": f"Database for version {version} does not exist."}, ensure_ascii=False)
    with db.connection(db_path) as conn:
        data = db.get_class_and_methods(conn, package.strip(), class_name.strip())
    if data is None:
        return json.dumps({"error": "not_found", "message": f"Class {package}.{class_name} not found."}, ensure_ascii=False)
    return json.dumps({"version": version, **data}, ensure_ascii=False)


def _run_list_classes(version: str, package_prefix: str, prefix_match: bool = True) -> str:
    """Lista clases por paquete exacto o por prefijo. JSON: version, package_prefix, prefix_match, classes."""
    if version not in config.VALID_SERVER_VERSIONS:
        version = "release"
    p = (package_prefix or "").strip()
    if not p:
        return json.dumps({"error": "missing_param", "message": "package_prefix is required"}, ensure_ascii=False)
    root = config.get_project_root()
    db_path = config.get_db_path(root, version)
    if not db_path.is_file():
        return json.dumps({"error": "no_db", "message": f"Database for version {version} does not exist."}, ensure_ascii=False)
    with db.connection(db_path) as conn:
        classes = db.list_classes(conn, p, prefix_match=prefix_match)
    return json.dumps({
        "version": version,
        "package_prefix": p,
        "prefix_match": prefix_match,
        "count": len(classes),
        "classes": classes,
    }, ensure_ascii=False)


def _run_context_list() -> str:
    """Devuelve versiones indexadas y versión activa. JSON: indexed, active."""
    root = config.get_project_root()
    cfg = config.load_config(root)
    active = cfg.get(config.CONFIG_KEY_ACTIVE_SERVER) or "release"
    indexed = [
        v for v in config.VALID_SERVER_VERSIONS
        if config.get_db_path(root, v).is_file()
    ]
    return json.dumps({"indexed": indexed, "active": active}, ensure_ascii=False)


def _run_index_stats(version: str | None) -> str:
    """Devuelve número de clases y métodos para la versión (o activa). JSON o error."""
    root = config.get_project_root()
    if version is not None and version not in config.VALID_SERVER_VERSIONS:
        version = "release"
    db_path = config.get_db_path(root, version)
    if not db_path.is_file():
        return json.dumps({
            "error": "no_db",
            "message": f"Database for version {version or 'active'} does not exist. Run prism index first.",
        }, ensure_ascii=False)
    resolved_version = version
    if resolved_version is None:
        cfg = config.load_config(root)
        resolved_version = cfg.get(config.CONFIG_KEY_ACTIVE_SERVER) or "release"
    with db.connection(db_path) as conn:
        classes, methods = db.get_stats(conn)
    return json.dumps({
        "version": resolved_version,
        "classes": classes,
        "methods": methods,
    }, ensure_ascii=False)


def _run_read_source(version: str, file_path: str) -> str:
    """Lee el contenido de un archivo Java descompilado. Valida path traversal."""
    if version not in config.VALID_SERVER_VERSIONS:
        version = "release"
    # Normalizar path: barras unificadas, sin segmentos vacíos ni ".."
    path_str = (file_path or "").strip().replace("\\", "/").lstrip("/")
    if not path_str:
        return json.dumps({"error": "missing_path", "message": "file_path is required"}, ensure_ascii=False)
    root = config.get_project_root()
    decompiled_dir = config.get_decompiled_dir(root, version).resolve()
    full_path = (decompiled_dir / path_str).resolve()
    if not full_path.is_relative_to(decompiled_dir):
        return json.dumps({"error": "invalid_path", "message": "file_path must be inside decompiled directory"}, ensure_ascii=False)
    if not full_path.is_file():
        return json.dumps({"error": "not_found", "message": f"File not found: {path_str}"}, ensure_ascii=False)
    try:
        content = full_path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return json.dumps({"error": "read_error", "message": str(e)}, ensure_ascii=False)
    return json.dumps({"content": content, "file_path": path_str, "version": version}, ensure_ascii=False)


def _register_tools(app: FastMCP) -> None:
    """Registra las tools prism_* en la instancia FastMCP dada."""

    @app.tool()
    def prism_search(
        query: str,
        version: str = "release",
        limit: int = 30,
        package_prefix: str | None = None,
        kind: str | None = None,
    ) -> str:
        """Search the indexed Hytale API (FTS5). Returns matching methods/classes with file_path for source code.
        Use a single word or quoted phrase; multiple terms: term1 AND term2.
        Optional: package_prefix to filter by package (e.g. com.hypixel.hytale.server); kind to filter by type (class, interface, record, enum)."""
        if not query or not str(query).strip():
            return json.dumps({"error": "missing_query", "message": "query is required"}, ensure_ascii=False)
        limit = max(1, min(int(limit), 500)) if limit is not None else 30
        return _run_search(query, version=version, limit=limit, package_prefix=package_prefix, kind=kind)

    @app.tool()
    def prism_get_class(version: str, package: str, class_name: str) -> str:
        """Get the exact class by package and class name with all its methods. Use for precise answers when you know the FQCN (e.g. com.hypixel.hytale.server.GameManager). Returns package, class_name, kind, file_path, and methods list (method, returns, params, is_static, annotation)."""
        return _run_get_class(version, package, class_name)

    @app.tool()
    def prism_list_classes(version: str, package_prefix: str, prefix_match: bool = True) -> str:
        """List all classes in a package. package_prefix is the full package (e.g. com.hypixel.hytale.server). If prefix_match is True, includes subpackages (e.g. com.hypixel.hytale.server.ui). Returns version, package_prefix, count, and classes (package, class_name, kind, file_path)."""
        return _run_list_classes(version, package_prefix, prefix_match)

    @app.tool()
    def prism_context_list() -> str:
        """List indexed server versions (release, prerelease) and the active context. Use to discover what is available before searching."""
        return _run_context_list()

    @app.tool()
    def prism_index_stats(version: str | None = None) -> str:
        """Return the number of indexed classes and methods for a version. If version is omitted, uses the active context."""
        return _run_index_stats(version)

    @app.tool()
    def prism_read_source(version: str, file_path: str) -> str:
        """Read the contents of a decompiled Java source file. file_path is the relative path from the decompiled directory (e.g. from prism_search result). Use version release or prerelease."""
        return _run_read_source(version, file_path)


# Instancia por defecto para stdio (host/port no se usan)
mcp = FastMCP("orbis-prism")
_register_tools(mcp)


def run(
    transport: str = "stdio",
    host: str = "0.0.0.0",
    port: int = 8000,
) -> None:
    """
    Arranca el servidor MCP. Por defecto usa transporte stdio.
    Si transport es "streamable-http", escucha en host:port (útil para Docker).
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
        pass  # Salida limpia al cerrar (Ctrl+C o cliente desconecta)
