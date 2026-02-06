# Esquema SQLite e índice FTS5 para la API de Hytale (clases y métodos).

import sqlite3
from pathlib import Path


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Abre una conexión a la base de datos; crea el archivo y directorio si no existen."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """
    Crea las tablas normales (classes, methods) y la tabla virtual FTS5
    para búsqueda full-text. Idempotente: borra y recrea las tablas si ya existen.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            package TEXT NOT NULL,
            class_name TEXT NOT NULL,
            kind TEXT NOT NULL,
            file_path TEXT NOT NULL,
            UNIQUE(package, class_name)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS methods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            method TEXT NOT NULL,
            returns TEXT NOT NULL,
            params TEXT NOT NULL,
            is_static INTEGER NOT NULL DEFAULT 0,
            annotation TEXT,
            FOREIGN KEY (class_id) REFERENCES classes(id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_methods_class_id ON methods(class_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_classes_package ON classes(package)")

    # Tabla FTS5 para búsqueda por símbolo/texto (paquete, clase, método, etc.)
    conn.execute("DROP TABLE IF EXISTS api_fts")
    conn.execute("""
        CREATE VIRTUAL TABLE api_fts USING fts5(
            package,
            class_name,
            kind,
            method_name,
            returns,
            params,
            tokenize='unicode61'
        )
    """)
    conn.commit()


def clear_tables(conn: sqlite3.Connection) -> None:
    """Vacía las tablas de datos (classes, methods, api_fts) para reindexar desde cero."""
    conn.execute("DELETE FROM api_fts")
    conn.execute("DELETE FROM methods")
    conn.execute("DELETE FROM classes")
    conn.commit()


def insert_class(conn: sqlite3.Connection, package: str, class_name: str, kind: str, file_path: str) -> int:
    """Inserta una clase y devuelve su id. Si ya existe (package, class_name), devuelve el id existente."""
    cur = conn.execute(
        "INSERT OR IGNORE INTO classes (package, class_name, kind, file_path) VALUES (?, ?, ?, ?)",
        (package, class_name, kind, file_path),
    )
    if cur.lastrowid and cur.lastrowid > 0:
        return cur.lastrowid
    row = conn.execute(
        "SELECT id FROM classes WHERE package = ? AND class_name = ?",
        (package, class_name),
    ).fetchone()
    return row["id"] if row else 0


def insert_method(
    conn: sqlite3.Connection,
    class_id: int,
    method: str,
    returns: str,
    params: str,
    is_static: bool,
    annotation: str | None,
) -> None:
    """Inserta un método y su fila en api_fts para búsqueda."""
    conn.execute(
        "INSERT INTO methods (class_id, method, returns, params, is_static, annotation) VALUES (?, ?, ?, ?, ?, ?)",
        (class_id, method, returns, params, 1 if is_static else 0, annotation),
    )


def insert_fts_row(
    conn: sqlite3.Connection,
    package: str,
    class_name: str,
    kind: str,
    method_name: str,
    returns: str,
    params: str,
) -> None:
    """Inserta una fila en la tabla FTS5 para que sea buscable."""
    conn.execute(
        "INSERT INTO api_fts (package, class_name, kind, method_name, returns, params) VALUES (?, ?, ?, ?, ?, ?)",
        (package, class_name, kind, method_name, returns, params),
    )


def get_stats(conn: sqlite3.Connection) -> tuple[int, int]:
    """Devuelve (número de clases, número de métodos)."""
    classes = conn.execute("SELECT COUNT(*) AS n FROM classes").fetchone()["n"]
    methods = conn.execute("SELECT COUNT(*) AS n FROM methods").fetchone()["n"]
    return classes, methods


def search_fts(
    conn: sqlite3.Connection,
    query_term: str,
    limit: int = 50,
) -> list[sqlite3.Row]:
    """
    Busca en la tabla FTS5 api_fts. query_term se pasa a MATCH (sintaxis FTS5).
    JOIN con classes para incluir file_path (ruta relativa al directorio descompilado).
    Devuelve lista de filas (package, class_name, kind, method_name, returns, params, file_path).
    Puede lanzar sqlite3.OperationalError si la sintaxis FTS5 es inválida.
    """
    if not query_term or not query_term.strip():
        return []
    term = query_term.strip()
    cur = conn.execute(
        """SELECT api_fts.package, api_fts.class_name, api_fts.kind, api_fts.method_name,
           api_fts.returns, api_fts.params, c.file_path
           FROM api_fts JOIN classes c ON c.package = api_fts.package AND c.class_name = api_fts.class_name
           WHERE api_fts MATCH ? LIMIT ?""",
        (term, limit),
    )
    return cur.fetchall()
