# Internationalisation: load JSON locales and translate with fallback to Spanish.

import os
import json
from pathlib import Path

from .infrastructure import config_impl

# Default code when there is no config or env
DEFAULT_LOCALE = "es"
# Language file directory (next to this module)
_LOCALES_DIR = Path(__file__).resolve().parent / "locales"

# Cache: locale -> key dict
_catalogs: dict[str, dict] = {}
# Fallback when active locale has empty value
_fallback_catalog: dict | None = None


def _load_catalog(locale: str) -> dict:
    """Load the locale JSON. Returns empty dict if the file does not exist."""
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
    Get current locale: config .prism.json -> PRISM_LANG -> LANG -> es.
    Normalises to short code (es, en).
    """
    cfg = config_impl.load_config(root)
    lang = cfg.get(config_impl.CONFIG_KEY_LANG)
    if lang:
        return _normalize_locale(lang)
    env = os.environ.get("PRISM_LANG") or os.environ.get("LANG", "")
    if env:
        return _normalize_locale(env)
    return DEFAULT_LOCALE


def _normalize_locale(locale: str) -> str:
    """Convert en_US, en-US, etc. to en; es_ES to es."""
    part = locale.split("_")[0].split("-")[0].strip().lower()
    return part if part else DEFAULT_LOCALE


def t(key: str, **kwargs: str) -> str:
    """
    Translate the key to the current locale. If the value is empty, use the one from es.
    kwargs replaces {name} placeholders in the string.
    """
    root = config_impl.get_project_root()
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
    List of (code, name) for available locales.
    The name is taken from "_name" in each JSON.
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
    """Check whether the locale file exists."""
    return (_LOCALES_DIR / f"{_normalize_locale(locale)}.json").exists()
