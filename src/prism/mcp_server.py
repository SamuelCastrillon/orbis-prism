# Servidor MCP para Orbis Prism (SDK oficial: https://github.com/modelcontextprotocol/python-sdk).
# Expone el tool prism_search para buscar en la API indexada de Hytale.
# Compatible con mcp>=1.0 (v1.x usa FastMCP; v2 usa MCPServer).
# Transporte: stdio (por defecto) o streamable-http (útil para Docker).

import json

from mcp.server.fastmcp import FastMCP

from . import config
from . import search


def _run_search(query: str, version: str = "release", limit: int = 30) -> str:
    """
    Ejecuta búsqueda FTS5 mediante la capa de acceso (search.search_api).
    Devuelve JSON string (misma estructura que CLI --json) o dict de error.
    """
    if version not in config.VALID_SERVER_VERSIONS:
        version = "release"
    results, err = search.search_api(None, version, query.strip(), limit=limit)
    if err is not None:
        return json.dumps(err, ensure_ascii=False)
    return json.dumps({
        "version": version,
        "term": query.strip(),
        "count": len(results),
        "results": results,
    }, ensure_ascii=False)


def _register_tools(app: FastMCP) -> None:
    """Registra el tool prism_search en la instancia FastMCP dada."""

    @app.tool()
    def prism_search(
        query: str,
        version: str = "release",
        limit: int = 30,
    ) -> str:
        """Search the indexed Hytale API (FTS5). Returns matching methods/classes with file_path for source code.
        Use a single word or quoted phrase; multiple terms: term1 AND term2."""
        if not query or not str(query).strip():
            return json.dumps({"error": "missing_query", "message": "query is required"}, ensure_ascii=False)
        limit = max(1, min(int(limit), 500)) if limit is not None else 30
        return _run_search(query, version=version, limit=limit)


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
