# Internacionalización: carga de locales JSON y traducción con fallback a español.

import os
import json
from pathlib import Path

from . import config

# Código por defecto cuando no hay config ni env
DEFAULT_LOCALE = "es"
# Directorio de archivos de idioma (junto a este módulo)
_LOCALES_DIR = Path(__file__).resolve().parent / "locales"

# Cache: locale -> dict de claves
_catalogs: dict[str, dict] = {}
# Fallback cuando el idioma activo tiene valor vacío
_fallback_catalog: dict | None = None


def _load_catalog(locale: str) -> dict:
    """Carga el JSON del idioma. Devuelve dict vacío si el archivo no existe."""
    if locale in _catalogs:
        return _catalogs[locale]
    path = _LOCALES_DIR / f"{locale}.json"
    if not path.exists():
        _catalogs[locale] = {}
        return _catalogs[locale]
    try:
        with open(path, encoding="utf-8") as f:
            _catalogs[locale] = json.load(f)
        return _catalogs[locale]
    except (json.JSONDecodeError, OSError):
        _catalogs[locale] = {}
        return _catalogs[locale]


def get_current_locale(root: Path | None = None) -> str:
    """
    Obtiene el idioma actual: config .prism.json -> PRISM_LANG -> LANG -> es.
    Normaliza a código corto (es, en).
    """
    cfg = config.load_config(root)
    lang = cfg.get(config.CONFIG_KEY_LANG)
    if lang:
        return _normalize_locale(lang)
    env = os.environ.get("PRISM_LANG") or os.environ.get("LANG", "")
    if env:
        return _normalize_locale(env)
    return DEFAULT_LOCALE


def _normalize_locale(locale: str) -> str:
    """Convierte en_US, en-US, etc. a en; es_ES a es."""
    part = locale.split("_")[0].split("-")[0].strip().lower()
    return part if part else DEFAULT_LOCALE


def t(key: str, **kwargs: str) -> str:
    """
    Traduce la clave al idioma actual. Si el valor está vacío, usa el de es.
    kwargs reemplaza placeholders {name} en la cadena.
    """
    root = config.get_project_root()
    locale = get_current_locale(root)
    catalog = _load_catalog(locale)
    fallback = _load_catalog(DEFAULT_LOCALE) if locale != DEFAULT_LOCALE else None

    value = catalog.get(key)
    if not value and fallback:
        value = fallback.get(key)
    if value is None:
        value = key

    for k, v in kwargs.items():
        value = value.replace("{" + k + "}", str(v))
    return value


def get_available_locales() -> list[tuple[str, str]]:
    """
    Lista de (código, nombre) de idiomas disponibles.
    El nombre se toma de "_name" en cada JSON.
    """
    result: list[tuple[str, str]] = []
    if not _LOCALES_DIR.is_dir():
        return result
    for path in sorted(_LOCALES_DIR.glob("*.json")):
        code = path.stem.lower()
        catalog = _load_catalog(code)
        name = catalog.get("_name", code)
        result.append((code, name))
    return result


def is_locale_available(locale: str) -> bool:
    """Comprueba si existe el archivo de idioma."""
    return (_LOCALES_DIR / f"{_normalize_locale(locale)}.json").exists()
