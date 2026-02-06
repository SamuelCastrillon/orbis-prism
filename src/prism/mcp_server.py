# Servidor MCP para Orbis Prism (SDK oficial: https://github.com/modelcontextprotocol/python-sdk).
# Expone el tool prism_search para buscar en la API indexada de Hytale.
# Compatible con mcp>=1.0 (v1.x usa FastMCP; v2 usa MCPServer).

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


# Servidor MCP (FastMCP en v1.x del SDK)
mcp = FastMCP("orbis-prism")


@mcp.tool()
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


def run() -> None:
    """Arranca el servidor MCP por stdio (bloquea hasta que el cliente desconecte)."""
    try:
        mcp.run()
    except KeyboardInterrupt:
        pass  # Salida limpia al cerrar (Ctrl+C o cliente desconecta)
