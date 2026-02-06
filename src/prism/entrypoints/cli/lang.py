# Comandos lang: list y set.

import sys
from pathlib import Path

from ... import i18n
from ...infrastructure import config_impl


def cmd_lang_list(root: Path | None = None) -> int:
    """Lista idiomas disponibles y marca el actual."""
    root = root or config_impl.get_project_root()
    current = i18n.get_current_locale(root)
    locales = i18n.get_available_locales()
    print(i18n.t("lang.list.header"))
    for code, name in locales:
        if code == current:
            print(i18n.t("lang.list.current", code=code, name=name))
        else:
            print(i18n.t("lang.list.entry", code=code, name=name))
    return 0


def cmd_lang_set(lang_code: str, root: Path | None = None) -> int:
    """Cambia el idioma guardado en .prism.json."""
    root = root or config_impl.get_project_root()
    code = lang_code.strip().lower()
    if not code:
        print(i18n.t("lang.set.invalid", lang=lang_code), file=sys.stderr)
        return 1
    if not i18n.is_locale_available(code):
        print(i18n.t("lang.set.invalid", lang=code), file=sys.stderr)
        return 1
    cfg = config_impl.load_config(root)
    cfg[config_impl.CONFIG_KEY_LANG] = code
    config_impl.save_config(cfg, root)
    print(i18n.t("lang.set.success", lang=code))
    return 0


def run_lang(args: list[str], root: Path) -> int:
    """Dispatch del comando lang (list | set)."""
    if len(args) < 2:
        return 0  # main mostrará ayuda
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
