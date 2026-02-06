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


# Subruta bajo la raíz de Hytale para llegar al JAR del servidor (release o pre-release)
_RELATIVE_SERVER_JAR = ("install", "release", "package", "game", "latest", "Server", config.HYTALE_JAR_NAME)
_RELATIVE_SERVER_JAR_PRERELEASE = ("install", "pre-release", "package", "game", "latest", "Server", config.HYTALE_JAR_NAME)


def find_jar_paths_from_hytale_root(hytale_root: Path) -> tuple[Path | None, Path | None]:
    """
    Dada la ruta raíz de Hytale (ej. %APPDATA%\\Hytale), infiere y valida las rutas
    de HytaleServer.jar para release y pre-release.
    Devuelve (release_jar, prerelease_jar); cada uno es None si no existe o no es válido.
    """
    root = hytale_root.resolve()
    if not root.is_dir():
        return (None, None)
    release_jar = root.joinpath(*_RELATIVE_SERVER_JAR)
    prerelease_jar = root.joinpath(*_RELATIVE_SERVER_JAR_PRERELEASE)
    r = release_jar if release_jar.is_file() and _is_valid_jar(release_jar) else None
    p = prerelease_jar if prerelease_jar.is_file() and _is_valid_jar(prerelease_jar) else None
    return (r, p)


def is_hytale_root(path: Path) -> bool:
    """Comprueba si la ruta es la carpeta raíz de Hytale (contiene install/release o install/pre-release)."""
    root = path.resolve()
    if not root.is_dir():
        return False
    release_jar = root.joinpath(*_RELATIVE_SERVER_JAR)
    prerelease_jar = root.joinpath(*_RELATIVE_SERVER_JAR_PRERELEASE)
    return release_jar.is_file() or prerelease_jar.is_file()


def _search_standard_paths() -> list[Path]:
    """Rutas estándar: raíz Hytale (%APPDATA%\\Hytale) y Server release."""
    candidates: list[Path] = []
    appdata = os.environ.get("APPDATA")
    if appdata:
        hytale_root = Path(appdata) / "Hytale"
        if hytale_root.is_dir():
            candidates.append(hytale_root)
        server_install = hytale_root / "install" / "release" / "package" / "game" / "latest" / "Server"
        if server_install.is_dir() and server_install not in candidates:
            candidates.append(server_install)
    return candidates


def get_sibling_version_jar_path(jar_path: Path) -> Path | None:
    """
    Si la ruta del JAR contiene el segmento 'install/release/...' o 'install/pre-release/...',
    construye la ruta del "hermano" (release <-> pre-release) y la devuelve si existe
    y es un JAR válido. En caso contrario devuelve None.
    """
    resolved = jar_path.resolve()
    parts = list(resolved.parts)
    try:
        i_install = parts.index("install")
    except ValueError:
        return None
    if i_install + 1 >= len(parts):
        return None
    version_segment = parts[i_install + 1]
    if version_segment == "release":
        sibling_parts = parts[: i_install + 1] + ["pre-release"] + parts[i_install + 2 :]
    elif version_segment == "pre-release":
        sibling_parts = parts[: i_install + 1] + ["release"] + parts[i_install + 2 :]
    else:
        return None
    sibling = Path(*sibling_parts)
    if sibling.is_file() and _is_valid_jar(sibling):
        return sibling
    return None


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
    2. Config guardada (jar_path; ver prism config set game_path)
    3. Ruta estándar Windows: %APPDATA%\\Hytale\\install\\...\\Server
    Devuelve Path del JAR válido o None.
    """
    root = root or config.get_project_root()
    jar_name = config.HYTALE_JAR_NAME

    # 1. Variable de entorno (puede ser JAR o la carpeta raíz de Hytale)
    env_path = os.environ.get(config.ENV_JAR_PATH)
    if env_path:
        p = Path(env_path).resolve()
        if p.is_dir() and is_hytale_root(p):
            release_jar, prerelease_jar = find_jar_paths_from_hytale_root(p)
            if release_jar:
                return release_jar
            if prerelease_jar:
                return prerelease_jar
        elif _is_valid_jar(p):
            return p

    # 2. Config guardada
    from .config import get_jar_path_from_config
    saved = get_jar_path_from_config(root)
    if saved and _is_valid_jar(saved):
        return saved

    # 3. Rutas estándar (raíz Hytale o carpeta Server)
    for candidate_dir in _search_standard_paths():
        if is_hytale_root(candidate_dir):
            release_jar, prerelease_jar = find_jar_paths_from_hytale_root(candidate_dir)
            if release_jar:
                return release_jar
            if prerelease_jar:
                return prerelease_jar
        else:
            found = find_jar_in_dir(candidate_dir, jar_name)
            if found and _is_valid_jar(found):
                return found

    return None
