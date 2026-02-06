# Detección de HytaleServer.jar: env, rutas estándar Windows y validación.

import os
import shutil
import zipfile
from pathlib import Path

from . import config


def is_valid_jar(path: Path) -> bool:
    """Comprueba que el archivo existe y es un JAR válido (público, para uso en CLI)."""
    return _is_valid_jar(path)


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
    """Ruta de instalación oficial en Windows (Roaming): %APPDATA%\\Hytale\\install\\...\\Server."""
    candidates: list[Path] = []
    appdata = os.environ.get("APPDATA")
    if appdata:
        server_install = Path(appdata) / "Hytale" / "install" / "release" / "package" / "game" / "latest" / "Server"
        if server_install.is_dir():
            candidates.append(server_install)
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


def resolve_jadx_path(root: Path | None = None) -> str | None:
    """
    Resuelve la ruta del ejecutable JADX para guardar en config.
    Orden: JADX_PATH -> bin/jadx o bin/jadx.bat en raíz -> which('jadx').
    Devuelve la ruta como string o None si no se encuentra.
    """
    root = root or config.get_project_root()

    def _check_path(p: Path) -> str | None:
        if p.is_file():
            return str(p.resolve())
        if p.is_dir():
            for name in ("jadx", "jadx.bat", "jadx.cmd"):
                candidate = p / name
                if candidate.is_file():
                    return str(candidate.resolve())
        return None

    # 1. Variable de entorno
    env_path = os.environ.get(config.ENV_JADX_PATH)
    if env_path:
        result = _check_path(Path(env_path).resolve())
        if result:
            return result
    # 2. bin/ en la raíz del proyecto
    bin_dir = root / "bin"
    if bin_dir.is_dir():
        for name in ("jadx", "jadx.bat", "jadx.cmd"):
            candidate = bin_dir / name
            if candidate.is_file():
                return str(candidate.resolve())
    # 3. which('jadx')
    jadx = shutil.which("jadx")
    if jadx:
        return jadx
    return None


def find_and_validate_jar(root: Path | None = None) -> Path | None:
    """
    Inferencia de ruta de HytaleServer.jar:
    1. Variable HYTALE_JAR_PATH
    2. Config guardada (jar_path; ver prism config set jar_path)
    3. Ruta estándar Windows: %APPDATA%\\Hytale\\install\\...\\Server
    Devuelve Path del JAR válido o None.
    """
    root = root or config.get_project_root()
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

    # 3. Ruta estándar (APPDATA)
    for candidate_dir in _search_standard_paths():
        found = find_jar_in_dir(candidate_dir, jar_name)
        if found and _is_valid_jar(found):
            return found

    return None
