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
# Raíz del proyecto cuando se lanza desde MCP/Docker (evita depender solo de cwd)
ENV_WORKSPACE = "PRISM_WORKSPACE"

# Nombres de archivo de configuración (raíz del proyecto)
CONFIG_FILENAME = ".prism.json"
CONFIG_KEY_JAR_PATH = "jar_path"
CONFIG_KEY_JAR_PATH_PRERELEASE = "jar_path_prerelease"
CONFIG_KEY_JAR_PATH_RELEASE = "jar_path_release"
CONFIG_KEY_OUTPUT_DIR = "output_dir"
CONFIG_KEY_JADX_PATH = "jadx_path"
CONFIG_KEY_LANG = "lang"
CONFIG_KEY_ACTIVE_SERVER = "active_server"

# Versiones de servidor soportadas (cada una tiene su DB y su carpeta descompilada)
VALID_SERVER_VERSIONS = ("release", "prerelease")


def get_project_root() -> Path:
    """Raíz del proyecto: carpeta que contiene main.py / .prism.json (o src)."""
    env_root = os.environ.get(ENV_WORKSPACE)
    if env_root:
        p = Path(env_root).resolve()
        if p.is_dir():
            return p
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


def get_jar_path_release_from_config(root: Path | None = None) -> Path | None:
    """JAR de la versión release. Lee jar_path_release o infiere desde jar_path / sibling."""
    root = root or get_project_root()
    cfg = load_config(root)
    raw = cfg.get(CONFIG_KEY_JAR_PATH_RELEASE)
    if raw:
        p = Path(raw)
        if p.is_file():
            return p
    jar = get_jar_path_from_config(root)
    if jar is None:
        return None
    s = str(jar).replace("\\", "/")
    if "release" in s:
        return jar
    if "pre-release" in s:
        from . import detection
        return detection.get_sibling_version_jar_path(jar)
    # Un solo JAR sin ruta release/prerelease: se considera release
    return jar


def get_jar_path_prerelease_from_config(root: Path | None = None) -> Path | None:
    """JAR de la versión prerelease. Lee jar_path_prerelease o infiere desde jar_path / sibling."""
    root = root or get_project_root()
    cfg = load_config(root)
    raw = cfg.get(CONFIG_KEY_JAR_PATH_PRERELEASE)
    if raw:
        p = Path(raw)
        if p.is_file():
            return p
    jar = get_jar_path_from_config(root)
    if jar is None:
        return None
    s = str(jar).replace("\\", "/")
    if "pre-release" in s:
        return jar
    if "release" in s:
        from . import detection
        return detection.get_sibling_version_jar_path(jar)
    return None


def get_jadx_path_from_config(root: Path | None = None) -> Path | None:
    """Obtiene la ruta de JADX desde la config. None si no está o no es ejecutable."""
    cfg = load_config(root)
    raw = cfg.get(CONFIG_KEY_JADX_PATH)
    if not raw:
        return None
    p = Path(raw).resolve()
    return p if p.is_file() else None


def get_decompiled_dir(root: Path | None = None, version: str = "release") -> Path:
    """Directorio de salida descompilada para una versión (release/prerelease)."""
    return get_workspace_dir(root) / "decompiled" / version


def get_decompiled_raw_dir(root: Path | None = None, version: str = "release") -> Path:
    """Directorio de salida cruda de JADX para una versión (antes de la poda)."""
    return get_workspace_dir(root) / "decompiled_raw" / version


def get_db_dir(root: Path | None = None) -> Path:
    """Directorio de la base de datos SQLite."""
    return get_workspace_dir(root) / "db"


def get_db_path(root: Path | None = None, version: str | None = None) -> Path:
    """
    Ruta de la DB. Si version es None, usa active_server de config (default 'release').
    Compatibilidad: si no hay active_server y existe prism_api.db, se devuelve esa.
    """
    root = root or get_project_root()
    db_dir = get_db_dir(root)
    if version is not None:
        return db_dir / f"prism_api_{version}.db"
    cfg = load_config(root)
    active = cfg.get(CONFIG_KEY_ACTIVE_SERVER)
    if active in VALID_SERVER_VERSIONS:
        return db_dir / f"prism_api_{active}.db"
    legacy = db_dir / "prism_api.db"
    if legacy.exists():
        return legacy
    return db_dir / "prism_api_release.db"


def get_logs_dir(root: Path | None = None) -> Path:
    """Directorio de logs."""
    base = root if root is not None else get_project_root()
    return base / "logs"
