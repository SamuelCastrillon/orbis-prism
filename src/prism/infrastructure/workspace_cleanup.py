# Limpieza del workspace: borrar DB, artefactos de build y reset completo.

import shutil
from pathlib import Path

from ..domain.constants import VALID_SERVER_VERSIONS
from . import config_impl


def clean_db(root: Path | None = None) -> None:
    """
    Borra las bases SQLite del workspace (prism_api_release.db y prism_api_prerelease.db).
    No elimina otros archivos del directorio db.
    """
    root = root or config_impl.get_project_root()
    db_dir = config_impl.get_db_dir(root)
    if not db_dir.is_dir():
        return
    for version in VALID_SERVER_VERSIONS:
        db_path = config_impl.get_db_path(root, version)
        if db_path.is_file():
            db_path.unlink()


def clean_build(root: Path | None = None) -> None:
    """
    Borra los directorios de artefactos de build: decompiled_raw/<version> y decompiled/<version>
    para release y prerelease. Solo elimina si existen.
    """
    root = root or config_impl.get_project_root()
    for version in VALID_SERVER_VERSIONS:
        raw_dir = config_impl.get_decompiled_raw_dir(root, version)
        if raw_dir.is_dir():
            shutil.rmtree(raw_dir)
        decompiled_dir = config_impl.get_decompiled_dir(root, version)
        if decompiled_dir.is_dir():
            shutil.rmtree(decompiled_dir)


def reset_workspace(root: Path | None = None) -> None:
    """
    Deja el proyecto a cero: ejecuta clean_db y clean_build, y elimina .prism.json
    para que el usuario pueda volver a ejecutar context detect e init desde el principio.
    """
    root = root or config_impl.get_project_root()
    clean_db(root)
    clean_build(root)
    config_path = config_impl.get_config_path(root)
    if config_path.is_file():
        config_path.unlink()
