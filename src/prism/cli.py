# CLI Orbis Prism: subcomandos init, decompile, index, serve.

import sys
from pathlib import Path

from . import config
from . import detection


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

    jar_path = detection.find_and_validate_jar(root)
    if jar_path is None:
        print("Error: HytaleServer.jar no encontrado.", file=sys.stderr)
        print(
            "  - Define HYTALE_JAR_PATH o coloca el JAR en workspace/server/",
            file=sys.stderr,
        )
        print(
            "  - En Windows se buscan también rutas en %LOCALAPPDATA%.",
            file=sys.stderr,
        )
        return 1

    cfg = config.load_config(root)
    cfg[config.CONFIG_KEY_JAR_PATH] = str(jar_path.resolve())
    cfg[config.CONFIG_KEY_OUTPUT_DIR] = str(config.get_workspace_dir(root).resolve())
    config.save_config(cfg, root)

    print(f"Listo. JAR detectado: {jar_path}")
    print(f"Config guardada en: {config.get_config_path(root)}")
    return 0


def cmd_decompile(_root: Path | None = None) -> int:
    """Placeholder: requiere pipeline JADX (Fase 1)."""
    print("Comando 'decompile' no implementado aún. Ver Fase 1 del plan.", file=sys.stderr)
    return 1


def cmd_index(_root: Path | None = None) -> int:
    """Placeholder: requiere extractor y SQLite (Fase 2)."""
    print("Comando 'index' no implementado aún. Ver Fase 2 del plan.", file=sys.stderr)
    return 1


def cmd_serve(_root: Path | None = None) -> int:
    """Placeholder: requiere servidor MCP (Fase 3)."""
    print("Comando 'serve' no implementado aún. Ver Fase 3 del plan.", file=sys.stderr)
    return 1


def print_help() -> None:
    print("Orbis Prism - Herramientas para modding de Hytale")
    print()
    print("Uso: python main.py <comando>")
    print()
    print("Comandos:")
    print("  init       Detecta HytaleServer.jar y guarda la configuración.")
    print("  decompile  Descompila el JAR con JADX y deja solo com.hypixel.hytale.")
    print("  index      Indexa el código en la base SQLite (FTS5).")
    print("  serve      Inicia el servidor MCP para IA.")
    print()
    print("Ejemplo: python main.py init")


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
    if subcommand == "decompile":
        return cmd_decompile(root)
    if subcommand == "index":
        return cmd_index(root)
    if subcommand == "serve":
        return cmd_serve(root)

    print(f"Comando desconocido: {subcommand}", file=sys.stderr)
    print_help()
    return 1
