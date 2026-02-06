# Servidor MCP para Orbis Prism (SDK oficial: https://github.com/modelcontextprotocol/python-sdk).
# Expone el tool prism_search para buscar en la API indexada de Hytale.
# Compatible con mcp>=1.0 (v1.x usa FastMCP; v2 usa MCPServer).

import json
import sqlite3

from mcp.server.fastmcp import FastMCP

from . import config
from . import db
from . import i18n


def _run_search(query: str, version: str = "release", limit: int = 30) -> str:
    """
    Ejecuta búsqueda FTS5 y devuelve JSON string (misma estructura que CLI --json).
    En error FTS5 devuelve mensaje de error + sugerencia.
    """
    root = config.get_project_root()
    if version not in config.VALID_SERVER_VERSIONS:
        version = "release"
    db_path = config.get_db_path(root, version)
    if not db_path.is_file():
        return json.dumps({
            "error": "no_db",
            "message": i18n.t("cli.query.no_db", version=version),
        }, ensure_ascii=False)
    try:
        conn = db.get_connection(db_path)
        rows = db.search_fts(conn, query.strip(), limit=limit)
        conn.close()
    except sqlite3.OperationalError as e:
        err_msg = str(e).lower()
        if "fts5" in err_msg or "syntax" in err_msg:
            return json.dumps({
                "error": "fts5_syntax",
                "message": str(e),
                "hint": i18n.t("cli.query.fts5_help"),
            }, ensure_ascii=False)
        return json.dumps({"error": "db", "message": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": "db", "message": str(e)}, ensure_ascii=False)
    results = [
        {
            "package": r["package"],
            "class_name": r["class_name"],
            "kind": r["kind"],
            "method_name": r["method_name"],
            "returns": r["returns"],
            "params": r["params"],
            "file_path": r["file_path"],
        }
        for r in rows
    ]
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
    mcp.run()
