# API extractor from decompiled Java code (regex). Feeds SQLite + FTS5.

import re
import sys
from pathlib import Path

from tqdm import tqdm

from . import config_impl
from . import db

# Files processed between each commit to reduce transaction size and memory
BATCH_COMMIT_FILES = 1000

# Same regex as Server/Scripts/generate_api_context.py (but improved)
RE_PACKAGE = re.compile(r"package\s+([\w\.]+);")
RE_CLASS = re.compile(
    r"public\s+(?:abstract\s+|final\s+)?(class|interface|record|enum)\s+(\w+)"
    r"(?:\s+extends\s+([\w\<\>\.,\s]+?))?"
    r"(?:\s+implements\s+([\w\<\>\.,\s]+?))?"
    r"\s*\{"
)
RE_METHOD = re.compile(
    r"(@\w+\s+)?public\s+(?:abstract\s+|static\s+|final\s+|synchronized\s+|native\s+)*([\w\<\>\[\]\.]+)\s+(\w+)\s*\(([^\)]*)\)"
)


def _extract_from_java(content: str, file_path: str) -> list[tuple[str, str, str, list[dict], str | None, str | None]]:
    """
    Extract from a Java file: package, class_name, kind, methods, parent and interfaces.
    Uses bracket tracking to correctly attribute methods to inner/multiple classes.
    """
    pkg_match = RE_PACKAGE.search(content)
    if not pkg_match:
        return []
    pkg = pkg_match.group(1)

    classes_found = list(RE_CLASS.finditer(content))
    if not classes_found:
        return []

    final_results = []
    
    for class_match in classes_found:
        kind = class_match.group(1)
        name = class_match.group(2)
        parent = class_match.group(3).strip() if class_match.group(3) else None
        interfaces = class_match.group(4).strip() if class_match.group(4) else None
        
        # Clean generics from parent/interfaces for better indexing/linking
        if parent: parent = re.sub(r"\<.*?\>", "", parent).strip()
        if interfaces: interfaces = re.sub(r"\<.*?\>", "", interfaces).strip()

        start_search = class_match.end()
        
        # Find first '{' (which is actually part of the RE_CLASS match, but let's be careful)
        # Actually RE_CLASS ends at '{', so start_search is right after the '{'
        first_brace = class_match.end() - 1 # Position of '{'
        
        # Track braces to find closing '}'
        depth = 1
        end_search = -1
        for i in range(first_brace + 1, len(content)):
            if content[i] == '{': depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    end_search = i
                    break
        
        if end_search == -1: end_search = len(content)
        
        # Extract methods only within [first_brace, end_search]
        class_content = content[first_brace:end_search]
        methods = []
        for m in RE_METHOD.finditer(class_content):
            # RE_METHOD groups: 1:@Annotation, 2:Returns, 3:Name, 4:Params
            m_name = m.group(3)
            if m_name == name: continue # Constructor
            
            methods.append({
                "method": m_name,
                "returns": m.group(2),
                "params": m.group(4).strip(),
                "is_static": "static" in m.group(0),
                "annotation": m.group(1).strip() if m.group(1) else None,
            })
        
        final_results.append((pkg, name, kind, methods, parent, interfaces))
        
    return final_results


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
            for jpath in tqdm(java_files, unit=" files", desc="Indexing", file=sys.stderr, colour="green"):
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
                
                # Extract and insert
                results = _extract_from_java(content, file_path_str)
                for pkg, class_name, kind, methods, parent, interfaces in results:
                    class_id = db.insert_class(conn, pkg, class_name, kind, file_path_str, parent, interfaces)
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
    except Exception as e:
        import traceback
        traceback.print_exc() # Log to stderr for the agent/user to see
        return (False, "db_error")
