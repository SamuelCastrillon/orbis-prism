# Configuración central: rutas por defecto, constantes y lectura de variables de entorno.

import os
import json
from pathlib import Path

# Nombre del archivo JAR del servidor de Hytale
HYTALE_JAR_NAME = "HytaleServer.jar"

# Paquete núcleo que se conserva tras la poda
CORE_PACKAGE = "com.hypixel.hytale"
CORE_PACKAGE_PATH = "com/hypixel/hytale"

# Variables de entorno (BluePrint / convención)
ENV_JAR_PATH = "HYTALE_JAR_PATH"
ENV_OUTPUT_DIR = "PRISM_OUTPUT_DIR"
ENV_JADX_PATH = "JADX_PATH"
ENV_LANG = "PRISM_LANG"

# Nombres de archivo de configuración (raíz del proyecto)
CONFIG_FILENAME = ".prism.json"
CONFIG_KEY_JAR_PATH = "jar_path"
CONFIG_KEY_OUTPUT_DIR = "output_dir"
CONFIG_KEY_JADX_PATH = "jadx_path"
CONFIG_KEY_LANG = "lang"


def get_project_root() -> Path:
    """Raíz del proyecto: carpeta que contiene main.py / .prism.json (o src)."""
    # Si estamos en src/prism/, subir dos niveles
    current = Path(__file__).resolve().parent
    if (current / ".." / ".." / "main.py").resolve().exists():
        return (current / ".." / "..").resolve()
    # Fallback: directorio de trabajo actual
    return Path.cwd()


def get_workspace_dir(root: Path | None = None) -> Path:
    """Directorio workspace (decompiled, db, server)."""
    root = root or get_project_root()
    env_dir = os.environ.get(ENV_OUTPUT_DIR)
    if env_dir and Path(env_dir).is_dir():
        return Path(env_dir)
    return root / "workspace"


def get_config_path(root: Path | None = None) -> Path:
    """Ruta del archivo de configuración persistente."""
    root = root or get_project_root()
    return root / CONFIG_FILENAME


def load_config(root: Path | None = None) -> dict:
    """Carga la configuración desde .prism.json. Devuelve dict vacío si no existe."""
    path = get_config_path(root)
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(config: dict, root: Path | None = None) -> None:
    """Guarda la configuración en .prism.json."""
    path = get_config_path(root)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_jar_path_from_config(root: Path | None = None) -> Path | None:
    """Obtiene la ruta del JAR desde la config (string guardado). None si no está."""
    cfg = load_config(root)
    raw = cfg.get(CONFIG_KEY_JAR_PATH)
    if not raw:
        return None
    p = Path(raw)
    return p if p.is_file() else None


def get_decompiled_dir(root: Path | None = None) -> Path:
    """Directorio de salida descompilada (solo núcleo Hytale)."""
    return get_workspace_dir(root) / "decompiled"


def get_db_dir(root: Path | None = None) -> Path:
    """Directorio de la base de datos SQLite."""
    return get_workspace_dir(root) / "db"


def get_db_path(root: Path | None = None) -> Path:
    """Ruta del archivo prism_api.db."""
    return get_db_dir(root) / "prism_api.db"


def get_logs_dir(root: Path | None = None) -> Path:
    """Directorio de logs."""
    base = root if root is not None else get_project_root()
    return base / "logs"
