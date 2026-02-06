# API extractor from decompiled Java code (regex). Feeds SQLite + FTS5.

import re
from pathlib import Path

from . import config_impl
from . import db

# Files processed between each commit to reduce transaction size and memory
BATCH_COMMIT_FILES = 1000

# Same regex as Server/Scripts/generate_api_context.py
RE_PACKAGE = re.compile(r"package\s+([\w\.]+);")
RE_CLASS = re.compile(r"public\s+(class|interface|record|enum)\s+(\w+)")
RE_METHOD = re.compile(
    r"(@\w+\s+)?public\s+(static\s+)?([\w\<\>\[\]\.]+)\s+(\w+)\s*\(([^\)]*)\)"
)


def _extract_from_java(content: str, file_path: str) -> list[tuple[str, str, str, list[dict]]]:
    """
    Extract from a Java file: package, class_name, kind and list of methods.
    Returns a list of tuples (package, class_name, kind, methods) per class/interface/record/enum.
    file_path is used to store in the DB (relative or absolute).
    """
    pkg_match = RE_PACKAGE.search(content)
    if not pkg_match:
        return []
    pkg = pkg_match.group(1)

    result = []
    for class_match in RE_CLASS.finditer(content):
        c_type = class_match.group(1)
        c_name = class_match.group(2)
        methods = []
        for m in RE_METHOD.finditer(content):
            annotation = m.group(1).strip() if m.group(1) else None
            is_static = m.group(2) is not None
            ret_type = m.group(3)
            m_name = m.group(4)
            params = m.group(5).strip()
            if m_name != c_name:  # Exclude constructor
                methods.append({
                    "method": m_name,
                    "returns": ret_type,
                    "params": params,
                    "is_static": is_static,
                    "annotation": annotation,
                })
        result.append((pkg, c_name, c_type, methods))
    return result


def run_index(root: Path | None = None, version: str = "release") -> tuple[bool, str | tuple[int, int]]:
    """
    Walk workspace/decompiled/<version>, extract classes and methods with regex,
    and fill prism_api_<version>.db. Returns (True, (num_classes, num_methods));
    (False, "no_decompiled") if no code; (False, "db_error") if DB fails.
    """
    root = root or config_impl.get_project_root()
    decompiled_dir = config_impl.get_decompiled_dir(root, version)
    if not decompiled_dir.is_dir():
        return (False, "no_decompiled")
    java_files = list(decompiled_dir.rglob("*.java"))
    if not java_files:
        return (False, "no_decompiled")

    db_path = config_impl.get_db_path(root, version)
    try:
        with db.connection(db_path) as conn:
            db.init_schema(conn)
            db.clear_tables(conn)
            files_processed = 0
            for jpath in java_files:
                try:
                    content = jpath.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                # Relative path to decompiled directory for storage
                try:
                    rel_path = jpath.relative_to(decompiled_dir)
                except ValueError:
                    rel_path = jpath
                file_path_str = str(rel_path).replace("\\", "/")
                for pkg, class_name, kind, methods in _extract_from_java(content, file_path_str):
                    class_id = db.insert_class(conn, pkg, class_name, kind, file_path_str)
                    for m in methods:
                        db.insert_method(
                            conn,
                            class_id,
                            m["method"],
                            m["returns"],
                            m["params"],
                            m["is_static"],
                            m["annotation"],
                        )
                        db.insert_fts_row(
                            conn,
                            pkg,
                            class_name,
                            kind,
                            m["method"],
                            m["returns"],
                            m["params"],
                        )
                files_processed += 1
                if files_processed % BATCH_COMMIT_FILES == 0:
                    conn.commit()
            conn.commit()
            stats = db.get_stats(conn)
        return (True, stats)
    except Exception:
        return (False, "db_error")
