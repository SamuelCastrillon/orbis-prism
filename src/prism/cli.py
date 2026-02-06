# CLI Orbis Prism: subcomandos init, decompile, index, serve, lang.

import os
import sys
from pathlib import Path

from . import config
from . import detection
from . import i18n


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


def cmd_decompile(_root: Path | None = None) -> int:
    """Placeholder: requiere pipeline JADX (Fase 1)."""
    print(i18n.t("cli.decompile.not_implemented"), file=sys.stderr)
    return 1


def cmd_index(_root: Path | None = None) -> int:
    """Placeholder: requiere extractor y SQLite (Fase 2)."""
    print(i18n.t("cli.index.not_implemented"), file=sys.stderr)
    return 1


def cmd_serve(_root: Path | None = None) -> int:
    """Placeholder: requiere servidor MCP (Fase 3)."""
    print(i18n.t("cli.serve.not_implemented"), file=sys.stderr)
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
    print(i18n.t("cli.help.title"))
    print()
    print(i18n.t("cli.help.usage"))
    print()
    print(i18n.t("cli.help.commands"))
    print("  init       ", i18n.t("cli.help.init_desc"))
    print("  decompile  ", i18n.t("cli.help.decompile_desc"))
    print("  index      ", i18n.t("cli.help.index_desc"))
    print("  serve      ", i18n.t("cli.help.serve_desc"))
    print("  lang list   ", i18n.t("cli.help.lang_list_desc"))
    print("  lang set <código>  ", i18n.t("cli.help.lang_set_desc"))
    print("  config set game_path <ruta>  ", i18n.t("cli.help.config_set_jar_desc"))
    print("      ", i18n.t("cli.help.config_set_jar_hint"))
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
    if subcommand == "decompile":
        return cmd_decompile(root)
    if subcommand == "index":
        return cmd_index(root)
    if subcommand == "serve":
        return cmd_serve(root)

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
