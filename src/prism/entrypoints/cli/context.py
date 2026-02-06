# Comandos context / ctx: detect, init, clean, reset, decompile, prune, db, list, use.

import os
import sys
from pathlib import Path

from ...application import get_context_list
from ... import i18n
from ...domain.constants import VALID_SERVER_VERSIONS
from ...infrastructure import config_impl
from ...infrastructure import decompile
from ...infrastructure import detection
from ...infrastructure import extractor
from ...infrastructure import file_config
from ...infrastructure import prune
from ...infrastructure import workspace_cleanup

from . import args as cli_args


def _ensure_dirs(root: Path) -> None:
    """Asegura que existan workspace/server, decompiled, db y logs."""
    config_impl.get_workspace_dir(root).mkdir(parents=True, exist_ok=True)
    (config_impl.get_workspace_dir(root) / "server").mkdir(parents=True, exist_ok=True)
    config_impl.get_decompiled_dir(root).mkdir(parents=True, exist_ok=True)
    config_impl.get_db_dir(root).mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(parents=True, exist_ok=True)


def cmd_init(root: Path | None = None) -> int:
    """
    Detecta HytaleServer.jar, valida y guarda config en .prism.json.
    Crea los directorios del workspace si no existen.
    """
    root = root or config_impl.get_project_root()
    _ensure_dirs(root)

    env_jar = os.environ.get(config_impl.ENV_JAR_PATH)
    if env_jar:
        env_path = Path(env_jar).resolve()
        if not detection.is_valid_jar(env_path):
            print(i18n.t("cli.init.env_jar_invalid"), file=sys.stderr)
            return 1

    jar_path = detection.find_and_validate_jar(root)
    if jar_path is None:
        print(i18n.t("cli.init.jar_not_found"), file=sys.stderr)
        print(i18n.t("cli.init.hint_env"), file=sys.stderr)
        print(i18n.t("cli.init.hint_windows"), file=sys.stderr)
        return 1

    cfg = config_impl.load_config(root)
    cfg[config_impl.CONFIG_KEY_JAR_PATH] = str(jar_path.resolve())
    cfg[config_impl.CONFIG_KEY_OUTPUT_DIR] = str(config_impl.get_workspace_dir(root).resolve())
    jadx_path = detection.resolve_jadx_path(root)
    if jadx_path:
        cfg[config_impl.CONFIG_KEY_JADX_PATH] = jadx_path
    sibling = detection.get_sibling_version_jar_path(jar_path)
    if sibling:
        if "pre-release" in str(jar_path).replace("\\", "/"):
            cfg[config_impl.CONFIG_KEY_JAR_PATH_RELEASE] = str(sibling.resolve())
        else:
            cfg[config_impl.CONFIG_KEY_JAR_PATH_PRERELEASE] = str(sibling.resolve())
    config_impl.save_config(cfg, root)

    print(i18n.t("cli.init.success_jar", path=jar_path))
    if sibling:
        print(i18n.t("cli.init.sibling_saved", path=sibling))
    print(i18n.t("cli.init.success_config", path=config_impl.get_config_path(root)))
    return 0


def cmd_context_detect(root: Path | None = None) -> int:
    """Detecta JAR y guarda config (misma lógica que init top-level)."""
    return cmd_init(root)


def _resolve_context_versions(root: Path, version: str | None) -> list[str] | None:
    """Determina la lista de versiones a usar; None si no hay JAR configurado."""
    if version is not None:
        return [version]
    versions = []
    if config_impl.get_jar_path_release_from_config(root):
        versions.append("release")
    if config_impl.get_jar_path_prerelease_from_config(root):
        versions.append("prerelease")
    if not versions and config_impl.get_jar_path_from_config(root):
        versions = ["release"]
    return versions if versions else None


def cmd_context_init(root: Path | None = None, version: str | None = None) -> int:
    """Pipeline completo: detecta JAR si falta → decompile (solo JADX) → prune → db. version=None -> all."""
    root = root or config_impl.get_project_root()
    versions_list = _resolve_context_versions(root, version)
    if not versions_list:
        # Intentar detectar el JAR antes de fallar (equivalente a ctx detect)
        print(i18n.t("cli.decompile.no_jar"), file=sys.stderr)
        print(i18n.t("cli.init.attempting_detect"))
        if cmd_init(root) != 0:
            return 1
        versions_list = _resolve_context_versions(root, version)
        if not versions_list:
            print(i18n.t("cli.decompile.no_jar"), file=sys.stderr)
            return 1

    print(i18n.t("cli.build.phase_decompile"))
    print(i18n.t("cli.decompile.may_take"))
    success, err = decompile.run_decompile_only(root, versions=versions_list)
    if not success:
        print(i18n.t("cli.build.decompile_failed"), file=sys.stderr)
        print(i18n.t(f"cli.decompile.{err}"), file=sys.stderr)
        return 1
    print(i18n.t("cli.build.phase_decompile_done"))

    success, err = prune.run_prune_only(root, versions=versions_list)
    if not success:
        print(i18n.t("cli.prune." + err), file=sys.stderr)
        return 1

    print(i18n.t("cli.build.phase_index"))
    for v in versions_list:
        print(i18n.t("cli.build.indexing_version", version=v))
        ok, payload = extractor.run_index(root, v)
        if ok:
            classes, methods = payload
            print(i18n.t("cli.build.indexed", version=v, classes=classes, methods=methods))
        elif payload == "no_decompiled":
            print(i18n.t("cli.build.skipped_no_code", version=v))
        else:
            print(i18n.t("cli.index.db_error"), file=sys.stderr)
            return 1
    print(i18n.t("cli.build.success"))
    return 0


def cmd_context_clean(root: Path | None = None, target: str = "") -> int:
    """Limpia según target: db | build | b | all."""
    root = root or config_impl.get_project_root()
    t = (target or "").strip().lower()
    if t == "db":
        workspace_cleanup.clean_db(root)
        print(i18n.t("cli.context.clean.db_done"))
        return 0
    if t in ("build", "b"):
        workspace_cleanup.clean_build(root)
        print(i18n.t("cli.context.clean.build_done"))
        return 0
    if t == "all":
        workspace_cleanup.clean_db(root)
        workspace_cleanup.clean_build(root)
        print(i18n.t("cli.context.clean.all_done"))
        return 0
    print(i18n.t("cli.context.clean.usage"), file=sys.stderr)
    return 1


def cmd_context_reset(root: Path | None = None) -> int:
    """Deja el proyecto a cero: clean db + build y elimina .prism.json."""
    root = root or config_impl.get_project_root()
    workspace_cleanup.reset_workspace(root)
    print(i18n.t("cli.context.reset.done"))
    return 0


def cmd_context_decompile(root: Path | None = None, version: str | None = None) -> int:
    """Solo JADX → decompiled_raw (sin prune). version=None -> all."""
    root = root or config_impl.get_project_root()
    versions = None if version is None else [version]
    print(i18n.t("cli.decompile.may_take"))
    success, err = decompile.run_decompile_only(root, versions=versions)
    if success:
        print(i18n.t("cli.decompile.success"))
        return 0
    print(i18n.t(f"cli.decompile.{err}"), file=sys.stderr)
    return 1


def cmd_prune(root: Path | None = None, version: str | None = None) -> int:
    """Solo prune (raw → decompiled). version=None -> todas las que tengan raw."""
    root = root or config_impl.get_project_root()
    versions = None if version is None else [version]
    success, err = prune.run_prune_only(root, versions=versions)
    if success:
        if version:
            print(i18n.t("cli.prune.success", version=version))
        else:
            print(i18n.t("cli.prune.completed_all"))
        return 0
    print(i18n.t(f"cli.prune.{err}"), file=sys.stderr)
    return 1


def cmd_index(root: Path | None = None, version: str | None = None) -> int:
    """Indexa en la DB. version=None -> release y prerelease."""
    root = root or config_impl.get_project_root()
    if version is not None and version not in VALID_SERVER_VERSIONS:
        print(i18n.t("cli.context.use.invalid"), file=sys.stderr)
        return 1
    if version is None:
        for v in VALID_SERVER_VERSIONS:
            ok, payload = extractor.run_index(root, v)
            if ok:
                classes, methods = payload
                print(i18n.t("cli.index.success", classes=classes, methods=methods, version=v))
            elif payload != "no_decompiled":
                print(i18n.t("cli.index.db_error"), file=sys.stderr)
                return 1
        return 0
    success, payload = extractor.run_index(root, version)
    if success:
        classes, methods = payload
        print(i18n.t("cli.index.success", classes=classes, methods=methods, version=version))
        return 0
    print(i18n.t(f"cli.index.{payload}"), file=sys.stderr)
    return 1


def cmd_context_list(root: Path | None = None) -> int:
    """Lista versiones indexadas y cuál está activa."""
    root = root or config_impl.get_project_root()
    provider = file_config.FileConfigProvider()
    ctx = get_context_list(provider, root)
    installed = ctx["indexed"]
    active = ctx["active"]
    print(i18n.t("cli.context.list.title"))
    if not installed:
        print(i18n.t("cli.context.list.none"))
        return 0
    for v in VALID_SERVER_VERSIONS:
        if v in installed:
            prefix = "  * " if v == active else "    "
            print(prefix + v)
    return 0


def cmd_context_use(version_str: str, root: Path | None = None) -> int:
    """Establece la versión activa (release o prerelease)."""
    root = root or config_impl.get_project_root()
    version = version_str.strip().lower()
    if version not in VALID_SERVER_VERSIONS:
        print(i18n.t("cli.context.use.invalid"), file=sys.stderr)
        return 1
    cfg = config_impl.load_config(root)
    cfg[config_impl.CONFIG_KEY_ACTIVE_SERVER] = version
    config_impl.save_config(cfg, root)
    if not config_impl.get_db_path(root, version).is_file():
        print(i18n.t("cli.context.use.not_indexed", version=version), file=sys.stderr)
    print(i18n.t("cli.context.use.success", version=version))
    return 0


def run_context(args: list[str], root: Path) -> int:
    """Dispatch del comando context | ctx."""
    if len(args) < 2:
        return 0  # main mostrará ayuda
    sub = args[1].lower()
    if sub in ("detect", "detec"):
        return cmd_context_detect(root)
    if sub == "init":
        version_arg, invalid = cli_args.parse_version_arg(args, 2)
        if invalid:
            print(i18n.t("cli.context.use.invalid"), file=sys.stderr)
            return 1
        return cmd_context_init(root, version=version_arg)
    if sub == "clean":
        target = args[2] if len(args) > 2 else ""
        return cmd_context_clean(root, target=target)
    if sub == "reset":
        return cmd_context_reset(root)
    if sub == "decompile":
        version_arg, invalid = cli_args.parse_version_arg(args, 2)
        if invalid:
            print(i18n.t("cli.context.use.invalid"), file=sys.stderr)
            return 1
        return cmd_context_decompile(root, version=version_arg)
    if sub == "prune":
        version_arg, invalid = cli_args.parse_version_arg(args, 2)
        if invalid:
            print(i18n.t("cli.context.use.invalid"), file=sys.stderr)
            return 1
        return cmd_prune(root, version=version_arg)
    if sub == "db":
        version_arg, invalid = cli_args.parse_version_arg(args, 2)
        if invalid:
            print(i18n.t("cli.context.use.invalid"), file=sys.stderr)
            return 1
        return cmd_index(root, version=version_arg)
    if sub == "list":
        return cmd_context_list(root)
    if sub == "use":
        if len(args) < 3:
            print("Uso: prism context use <release|prerelease>", file=sys.stderr)
            return 1
        return cmd_context_use(args[2], root)
    print(i18n.t("cli.unknown_command", cmd=f"context {sub}"), file=sys.stderr)
    return 1
