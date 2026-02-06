# Detección de HytaleServer.jar: env, rutas estándar Windows y validación.

import os
import zipfile
from pathlib import Path

from . import config


def _is_valid_jar(path: Path) -> bool:
    """Comprueba que el archivo existe y es un JAR (ZIP con estructura válida)."""
    if not path.is_file() or path.suffix.lower() != ".jar":
        return False
    try:
        with zipfile.ZipFile(path, "r") as z:
            # Un JAR tiene al menos META-INF/MANIFEST.MF o clases
            names = z.namelist()
            return any(
                n.startswith("META-INF/") or n.endswith(".class")
                for n in names[:50]
            )
    except (zipfile.BadZipFile, OSError):
        return False


def _search_standard_paths() -> list[Path]:
    """Rutas estándar donde puede estar Hytale (Windows)."""
    candidates: list[Path] = []
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        base = Path(local_app)
        # Nombres típicos de carpeta de Hytale
        for name in ("Hytale", "Hypixel", "HytaleServer"):
            folder = base / name
            if folder.is_dir():
                candidates.append(folder)
        # Subcarpetas comunes
        for parent in (base, base / "Programs"):
            if parent.is_dir():
                for child in parent.iterdir():
                    if child.is_dir() and "hytale" in child.name.lower():
                        candidates.append(child)
    return candidates


def find_jar_in_dir(directory: Path, jar_name: str = config.HYTALE_JAR_NAME) -> Path | None:
    """Busca el JAR en un directorio (y un nivel de subcarpetas)."""
    if not directory.is_dir():
        return None
    # Directo en la carpeta
    direct = directory / jar_name
    if direct.is_file():
        return direct
    for child in directory.iterdir():
        if child.is_dir():
            candidate = child / jar_name
            if candidate.is_file():
                return candidate
    return None


def find_and_validate_jar(root: Path | None = None) -> Path | None:
    """
    Inferencia de ruta de HytaleServer.jar:
    1. Variable HYTALE_JAR_PATH
    2. Config guardada (jar_path)
    3. workspace/server/
    4. Rutas estándar Windows (LOCALAPPDATA)
    Devuelve Path del JAR válido o None.
    """
    root = root or config.get_project_root()
    workspace = config.get_workspace_dir(root)
    jar_name = config.HYTALE_JAR_NAME

    # 1. Variable de entorno
    env_path = os.environ.get(config.ENV_JAR_PATH)
    if env_path:
        p = Path(env_path).resolve()
        if _is_valid_jar(p):
            return p

    # 2. Config guardada
    from .config import get_jar_path_from_config
    saved = get_jar_path_from_config(root)
    if saved and _is_valid_jar(saved):
        return saved

    # 3. workspace/server/
    server_jar = find_jar_in_dir(workspace / "server", jar_name)
    if server_jar and _is_valid_jar(server_jar):
        return server_jar

    # 4. Rutas estándar
    for candidate_dir in _search_standard_paths():
        found = find_jar_in_dir(candidate_dir, jar_name)
        if found and _is_valid_jar(found):
            return found

    return None
