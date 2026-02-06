# CLI Orbis Prism: subcomandos init, decompile, index, mcp, context, lang.

import json
import os
import sys
from pathlib import Path

import sqlite3

from . import config
from . import db
from . import decompile
from . import detection
from . import extractor
from . import i18n
from . import prune

# Flag para "todas las versiones" en build, decompile, index
VERSION_FLAG_ALL = ("--all", "-a")

# Flags para query
QUERY_JSON_FLAGS = ("--json", "-j")
QUERY_LIMIT_FLAGS = ("--limit", "-n")


def _parse_query_args(args: list[str]) -> tuple[str | None, str, int, bool]:
    """
    Parsea args del comando query (desde args[1]).
    Devuelve (query_term, version, limit, output_json).
    query_term None si no se dio término.
    """
    output_json = False
    limit = 30
    positionals = []
    i = 1
    while i < len(args):
        a = args[i]
        if a in QUERY_JSON_FLAGS:
            output_json = True
            i += 1
        elif a in QUERY_LIMIT_FLAGS:
            if i + 1 < len(args):
                try:
                    limit = int(args[i + 1])
                    limit = max(1, min(limit, 500))
                except ValueError:
                    pass
                i += 2
            else:
                i += 1
        elif a.startswith("-"):
            i += 1
        else:
            positionals.append(a)
            i += 1
    term = positionals[0] if positionals else None
    version = positionals[1] if len(positionals) > 1 else "release"
    if version not in config.VALID_SERVER_VERSIONS:
        version = "release"
    return (term, version, limit, output_json)


def _parse_version_arg(args: list[str], start_index: int) -> tuple[str | None, bool]:
    """
    Parsea argumento de versión. Devuelve (version, invalid).
    version: 'release' | 'prerelease' | None (todas). Sin argumento → default 'release'.
    invalid: True si el argumento no es válido.
    """
    if len(args) <= start_index:
        return ("release", False)
    a = args[start_index].strip().lower()
    if a in VERSION_FLAG_ALL:
        return (None, False)
    if a in config.VALID_SERVER_VERSIONS:
        return (a, False)
    return (None, True)


def _ensure_dirs(root: Path) -> None:
    """Asegura que existan workspace/server, decompiled, db y logs."""
    config.get_workspace_dir(root).mkdir(parents=True, exist_ok=True)
    (config.get_workspace_dir(root) / "server").mkdir(parents=True, exist_ok=True)
    config.get_decompiled_dir(root).mkdir(parents=True, exist_ok=True)
    config.get_db_dir(root).mkdir(parents=True, exist_ok=True)
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)


def cmd_init(root: Path | None = None) -> int:
    """
    Detecta HytaleServer.jar, valida y guarda la config en .prism.json.
    Crea directorios workspace si no existen.
    """
    root = root or config.get_project_root()
    _ensure_dirs(root)

    # Si HYTALE_JAR_PATH está definida, validar primero y dar mensaje específico si falla
    env_jar = os.environ.get(config.ENV_JAR_PATH)
    if env_jar:
        env_path = Path(env_jar).resolve()
        if not detection.is_valid_jar(env_path):
            print(i18n.t("cli.init.env_jar_invalid"), file=sys.stderr)
            return 1

    jar_path = detection.find_and_validate_jar(root)
    if jar_path is None:
        print(i18n.t("cli.init.jar_not_found"), file=sys.stderr)
        print(i18n.t("cli.init.hint_env"), file=sys.stderr)
        print(i18n.t("cli.init.hint_windows"), file=sys.stderr)
        return 1

    cfg = config.load_config(root)
    cfg[config.CONFIG_KEY_JAR_PATH] = str(jar_path.resolve())
    cfg[config.CONFIG_KEY_OUTPUT_DIR] = str(config.get_workspace_dir(root).resolve())
    jadx_path = detection.resolve_jadx_path(root)
    if jadx_path:
        cfg[config.CONFIG_KEY_JADX_PATH] = jadx_path
    # Detección automática de la otra versión (release / pre-release)
    sibling = detection.get_sibling_version_jar_path(jar_path)
    if sibling:
        if "pre-release" in str(jar_path).replace("\\", "/"):
            cfg[config.CONFIG_KEY_JAR_PATH_RELEASE] = str(sibling.resolve())
        else:
            cfg[config.CONFIG_KEY_JAR_PATH_PRERELEASE] = str(sibling.resolve())
    config.save_config(cfg, root)

    print(i18n.t("cli.init.success_jar", path=jar_path))
    if sibling:
        print(i18n.t("cli.init.sibling_saved", path=sibling))
    print(i18n.t("cli.init.success_config", path=config.get_config_path(root)))
    return 0


def cmd_decompile(root: Path | None = None, version: str | None = None) -> int:
    """Ejecuta JADX y poda. version=None → todas; 'release'|'prerelease' → solo esa. Por defecto (sin arg) → release."""
    root = root or config.get_project_root()
    versions = None if version is None else [version]
    print(i18n.t("cli.decompile.may_take"))
    success, err = decompile.run_decompile_and_prune(root, versions=versions)
    if success:
        print(i18n.t("cli.decompile.success"))
        return 0
    key = f"cli.decompile.{err}"
    print(i18n.t(key), file=sys.stderr)
    return 1


def cmd_query(
    root: Path | None = None,
    query_term: str = "",
    version: str = "release",
    limit: int = 30,
    output_json: bool = False,
) -> int:
    """Ejecuta una búsqueda FTS5 en la DB de la versión indicada. output_json: solo imprime JSON (version, term, count, results con file_path)."""
    root = root or config.get_project_root()
    if not query_term or not query_term.strip():
        print(i18n.t("cli.query.usage"), file=sys.stderr)
        return 1
    if version not in config.VALID_SERVER_VERSIONS:
        print(i18n.t("cli.context.use.invalid"), file=sys.stderr)
        return 1
    db_path = config.get_db_path(root, version)
    if not db_path.is_file():
        print(i18n.t("cli.query.no_db", version=version), file=sys.stderr)
        return 1
    try:
        conn = db.get_connection(db_path)
        rows = db.search_fts(conn, query_term.strip(), limit=limit)
        conn.close()
    except sqlite3.OperationalError as e:
        err_msg = str(e).lower()
        if "fts5" in err_msg or "syntax" in err_msg:
            print(i18n.t("cli.query.error", msg=str(e)), file=sys.stderr)
            print(i18n.t("cli.query.fts5_help"), file=sys.stderr)
        else:
            print(i18n.t("cli.query.error", msg=str(e)), file=sys.stderr)
        return 1
    except Exception as e:
        print(i18n.t("cli.query.error", msg=str(e)), file=sys.stderr)
        return 1
    if output_json:
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
        out = {"version": version, "term": query_term.strip(), "count": len(results), "results": results}
        print(json.dumps(out, ensure_ascii=False))
        return 0
    print(i18n.t("cli.query.result_count", count=len(rows), term=query_term, version=version))
    for r in rows:
        print(f"  {r['package']}.{r['class_name']} ({r['kind']}) :: {r['method_name']}({r['params']}) -> {r['returns']}")
    return 0


def cmd_prune(root: Path | None = None, version: str | None = None) -> int:
    """Ejecuta solo la poda (raw → decompiled). version=None → todas las que tengan raw; 'release'|'prerelease' → esa. Por defecto: release."""
    root = root or config.get_project_root()
    versions = None if version is None else [version]
    success, err = prune.run_prune_only(root, versions=versions)
    if success:
        if version:
            print(i18n.t("cli.prune.success", version=version))
        else:
            print(i18n.t("cli.prune.completed_all"))
        return 0
    key = f"cli.prune.{err}"
    print(i18n.t(key), file=sys.stderr)
    return 1


def cmd_build(root: Path | None = None, version: str | None = None) -> int:
    """Ejecuta decompile e index. version=None → todas; 'release'|'prerelease' → solo esa. Por defecto (sin arg) → release."""
    root = root or config.get_project_root()
    versions = None if version is None else [version]

    print(i18n.t("cli.build.phase_decompile"))
    print(i18n.t("cli.decompile.may_take"))
    success, err = decompile.run_decompile_and_prune(root, versions=versions)
    if not success:
        print(i18n.t("cli.build.decompile_failed"), file=sys.stderr)
        print(i18n.t(f"cli.decompile.{err}"), file=sys.stderr)
        return 1
    print(i18n.t("cli.build.phase_decompile_done"))

    to_index = list(config.VALID_SERVER_VERSIONS) if version is None else [version]
    print(i18n.t("cli.build.phase_index"))
    for v in to_index:
        print(i18n.t("cli.build.indexing_version", version=v))
        ok, payload = extractor.run_index(root, v)
        if ok:
            classes, methods = payload
            print(i18n.t("cli.build.indexed", version=v, classes=classes, methods=methods))
        elif payload == "no_decompiled":
            print(i18n.t("cli.build.skipped_no_code", version=v))
        else:
            print(i18n.t("cli.index.db_error"), file=sys.stderr)
            return 1
    print(i18n.t("cli.build.success"))
    return 0


def cmd_index(root: Path | None = None, version: str | None = None) -> int:
    """Indexa en la DB. version=None → indexa release y prerelease; 'release'|'prerelease' → solo esa. Por defecto (sin arg) → release."""
    root = root or config.get_project_root()
    if version is not None and version not in config.VALID_SERVER_VERSIONS:
        print(i18n.t("cli.context.use.invalid"), file=sys.stderr)
        return 1
    if version is None:
        # --all: indexar ambas versiones
        for v in config.VALID_SERVER_VERSIONS:
            ok, payload = extractor.run_index(root, v)
            if ok:
                classes, methods = payload
                print(i18n.t("cli.index.success", classes=classes, methods=methods, version=v))
            elif payload != "no_decompiled":
                print(i18n.t("cli.index.db_error"), file=sys.stderr)
                return 1
        return 0
    success, payload = extractor.run_index(root, version)
    if success:
        classes, methods = payload
        print(i18n.t("cli.index.success", classes=classes, methods=methods, version=version))
        return 0
    key = f"cli.index.{payload}"
    print(i18n.t(key), file=sys.stderr)
    return 1


def cmd_context_list(root: Path | None = None) -> int:
    """Lista las versiones indexadas (DB existente) y cuál está activa."""
    root = root or config.get_project_root()
    db_dir = config.get_db_dir(root)
    cfg = config.load_config(root)
    active = cfg.get(config.CONFIG_KEY_ACTIVE_SERVER) or "release"
    installed = []
    for v in config.VALID_SERVER_VERSIONS:
        if (db_dir / f"prism_api_{v}.db").is_file():
            installed.append(v)
    print(i18n.t("cli.context.list.title"))
    if not installed:
        print(i18n.t("cli.context.list.none"))
        return 0
    for v in config.VALID_SERVER_VERSIONS:
        if v in installed:
            prefix = "  * " if v == active else "    "
            print(prefix + v)
    return 0


def cmd_context_use(version_str: str, root: Path | None = None) -> int:
    """Establece la versión activa (release o prerelease)."""
    root = root or config.get_project_root()
    version = version_str.strip().lower()
    if version not in config.VALID_SERVER_VERSIONS:
        print(i18n.t("cli.context.use.invalid"), file=sys.stderr)
        return 1
    cfg = config.load_config(root)
    cfg[config.CONFIG_KEY_ACTIVE_SERVER] = version
    config.save_config(cfg, root)
    if not (config.get_db_dir(root) / f"prism_api_{version}.db").is_file():
        print(i18n.t("cli.context.use.not_indexed", version=version), file=sys.stderr)
    print(i18n.t("cli.context.use.success", version=version))
    return 0


def cmd_mcp(_root: Path | None = None) -> int:
    """Inicia el servidor MCP para IA (Fase 3). Bloquea hasta que el cliente desconecte."""
    root = _root or config.get_project_root()
    # Solo mostrar instrucciones si stderr es una terminal (ej. usuario ejecutó a mano).
    # Cuando Cursor lanza el proceso por stdio, stderr no es TTY y no imprimimos, para no interferir.
    if sys.stderr.isatty():
        cwd = str(root.resolve())
        command = sys.executable
        args_str = "main.py mcp"
        print(i18n.t("cli.mcp.instructions_title"), file=sys.stderr)
        print(i18n.t("cli.mcp.instructions_intro"), file=sys.stderr)
        print(i18n.t("cli.mcp.instructions_command", command=command), file=sys.stderr)
        print(i18n.t("cli.mcp.instructions_args", args=args_str), file=sys.stderr)
        print(i18n.t("cli.mcp.instructions_cwd", cwd=cwd), file=sys.stderr)
        print(i18n.t("cli.mcp.instructions_ready"), file=sys.stderr)
    from . import mcp_server
    try:
        mcp_server.run()
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(i18n.t("cli.query.error", msg=str(e)), file=sys.stderr)
        return 1


def cmd_lang_list(root: Path | None = None) -> int:
    """Lista los idiomas disponibles y marca el actual."""
    root = root or config.get_project_root()
    current = i18n.get_current_locale(root)
    locales = i18n.get_available_locales()
    print(i18n.t("lang.list.header"))
    for code, name in locales:
        if code == current:
            print(i18n.t("lang.list.current", code=code, name=name))
        else:
            print(i18n.t("lang.list.entry", code=code, name=name))
    return 0


def cmd_config_set_jar_path(path_str: str, root: Path | None = None) -> int:
    """Establece la ruta a HytaleServer.jar o a la carpeta raíz de Hytale (ej. %%APPDATA%%\\Hytale)."""
    root = root or config.get_project_root()
    path = Path(path_str).resolve()
    cfg = config.load_config(root)

    if path.is_dir() and detection.is_hytale_root(path):
        release_jar, prerelease_jar = detection.find_jar_paths_from_hytale_root(path)
        if not release_jar and not prerelease_jar:
            print(i18n.t("cli.config.jar_set_invalid", path=path_str), file=sys.stderr)
            return 1
        if release_jar:
            cfg[config.CONFIG_KEY_JAR_PATH] = str(release_jar.resolve())
            if prerelease_jar:
                cfg[config.CONFIG_KEY_JAR_PATH_PRERELEASE] = str(prerelease_jar.resolve())
        else:
            cfg[config.CONFIG_KEY_JAR_PATH] = str(prerelease_jar.resolve())
        config.save_config(cfg, root)
        print(i18n.t("cli.config.hytale_root_detected"))
        if release_jar:
            print(i18n.t("cli.init.success_jar", path=release_jar))
        if prerelease_jar:
            print(i18n.t("cli.init.sibling_saved", path=prerelease_jar))
        return 0
    if not detection.is_valid_jar(path):
        print(i18n.t("cli.config.jar_set_invalid", path=path_str), file=sys.stderr)
        return 1
    cfg[config.CONFIG_KEY_JAR_PATH] = str(path)
    sibling = detection.get_sibling_version_jar_path(path)
    if sibling:
        if "pre-release" in str(path).replace("\\", "/"):
            cfg[config.CONFIG_KEY_JAR_PATH_RELEASE] = str(sibling.resolve())
        else:
            cfg[config.CONFIG_KEY_JAR_PATH_PRERELEASE] = str(sibling.resolve())
    config.save_config(cfg, root)
    print(i18n.t("cli.config.jar_set_success", path=path))
    if sibling:
        print(i18n.t("cli.init.sibling_saved", path=sibling))
    return 0


def cmd_lang_set(lang_code: str, root: Path | None = None) -> int:
    """Cambia el idioma guardado en .prism.json."""
    root = root or config.get_project_root()
    code = lang_code.strip().lower()
    if not code:
        print(i18n.t("lang.set.invalid", lang=lang_code), file=sys.stderr)
        return 1
    if not i18n.is_locale_available(code):
        print(i18n.t("lang.set.invalid", lang=code), file=sys.stderr)
        return 1
    cfg = config.load_config(root)
    cfg[config.CONFIG_KEY_LANG] = code
    config.save_config(cfg, root)
    print(i18n.t("lang.set.success", lang=code))
    return 0


def print_help() -> None:
    # Ancho fijo para alinear descripciones (comando + espacios)
    w = 38
    fmt = "  {:<" + str(w) + "}"
    print(i18n.t("cli.help.title"))
    print()
    print(i18n.t("cli.help.usage"))
    print()
    print(i18n.t("cli.help.commands"))
    print(fmt.format("init") + i18n.t("cli.help.init_desc"))
    print(fmt.format("build [release|prerelease|--all|-a]") + i18n.t("cli.help.build_desc"))
    print(fmt.format("decompile [release|prerelease|--all|-a]") + i18n.t("cli.help.decompile_desc"))
    print(fmt.format("prune [release|prerelease|--all|-a]") + i18n.t("cli.help.prune_desc"))
    print(fmt.format("index [release|prerelease|--all|-a]") + i18n.t("cli.help.index_desc"))
    print(fmt.format("query [--json|-j] [--limit N] <término> [release|prerelease]") + i18n.t("cli.help.query_desc"))
    print(fmt.format("mcp") + i18n.t("cli.help.mcp_desc"))
    print()
    print(fmt.format("context list") + i18n.t("cli.help.context_list_desc"))
    print(fmt.format("context use <release|prerelease>") + i18n.t("cli.help.context_use_desc"))
    print()
    print(fmt.format("lang list") + i18n.t("cli.help.lang_list_desc"))
    print(fmt.format("lang set <código>") + i18n.t("cli.help.lang_set_desc"))
    print()
    print(fmt.format("config set game_path <ruta>") + i18n.t("cli.help.config_set_jar_desc"))
    print(fmt.format("") + i18n.t("cli.help.config_set_jar_hint"))
    print()
    print(i18n.t("cli.help.example"))


def main() -> int:
    """Punto de entrada del CLI."""
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print_help()
        return 0

    subcommand = args[0].lower()
    root = config.get_project_root()

    if subcommand == "init":
        return cmd_init(root)
    if subcommand == "config":
        if len(args) >= 4 and args[1].lower() == "set" and args[2].lower() == "game_path":
            return cmd_config_set_jar_path(" ".join(args[3:]), root)
        if len(args) >= 2 and args[1].lower() == "set":
            print("Uso: prism config set game_path <ruta>", file=sys.stderr)
            return 1
        print_help()
        return 0
    if subcommand == "build":
        version_arg, invalid = _parse_version_arg(args, 2)
        if invalid:
            print(i18n.t("cli.context.use.invalid"), file=sys.stderr)
            return 1
        return cmd_build(root, version=version_arg)
    if subcommand == "decompile":
        version_arg, invalid = _parse_version_arg(args, 2)
        if invalid:
            print(i18n.t("cli.context.use.invalid"), file=sys.stderr)
            return 1
        return cmd_decompile(root, version=version_arg)
    if subcommand == "index":
        version_arg, invalid = _parse_version_arg(args, 2)
        if invalid:
            print(i18n.t("cli.context.use.invalid"), file=sys.stderr)
            return 1
        return cmd_index(root, version=version_arg)
    if subcommand == "query":
        query_term, version, limit, output_json = _parse_query_args(args)
        if not query_term:
            print(i18n.t("cli.query.usage"), file=sys.stderr)
            return 1
        return cmd_query(root, query_term=query_term, version=version, limit=limit, output_json=output_json)
    if subcommand == "prune":
        version_arg, invalid = _parse_version_arg(args, 1)
        if invalid:
            print(i18n.t("cli.context.use.invalid"), file=sys.stderr)
            return 1
        return cmd_prune(root, version=version_arg)
    if subcommand == "mcp":
        return cmd_mcp(root)

    if subcommand == "context":
        if len(args) < 2:
            print_help()
            return 0
        sub = args[1].lower()
        if sub == "list":
            return cmd_context_list(root)
        if sub == "use":
            if len(args) < 3:
                print("Uso: prism context use <release|prerelease>", file=sys.stderr)
                return 1
            return cmd_context_use(args[2], root)
        print(i18n.t("cli.unknown_command", cmd=f"context {sub}"), file=sys.stderr)
        return 1

    if subcommand == "lang":
        if len(args) < 2:
            print_help()
            return 0
        sub = args[1].lower()
        if sub == "list":
            return cmd_lang_list(root)
        if sub == "set":
            if len(args) < 3:
                print(i18n.t("cli.lang.set_usage"), file=sys.stderr)
                return 1
            return cmd_lang_set(args[2], root)
        print(i18n.t("cli.unknown_command", cmd=f"lang {sub}"), file=sys.stderr)
        return 1

    print(i18n.t("cli.unknown_command", cmd=subcommand), file=sys.stderr)
    print_help()
    return 1
