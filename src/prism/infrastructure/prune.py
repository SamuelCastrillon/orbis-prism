# Prune: copy only com.hypixel.hytale from decompiled_raw to decompiled.

import sys
import shutil
from pathlib import Path

from . import config_impl

# Subdirectories where JADX may leave sources (version-dependent)
PRUNE_SOURCE_CANDIDATES = (
    "sources",  # Many JADX versions use -d and write to <out>/sources/
    "",        # Or directly in the -d root
)


def prune_to_core(raw_dir: Path, dest_dir: Path) -> tuple[bool, dict | None]:
    """
    Copy only the com/hypixel/hytale branch from raw_dir to dest_dir.
    Tries raw_dir/sources/com/hypixel/hytale and raw_dir/com/hypixel/hytale.
    Returns (True, {"files": N, "source_subdir": "sources"|"."}) or (False, None) if not found.
    """
    core_rel = config_impl.CORE_PACKAGE_PATH  # "com/hypixel/hytale"
    source_core = None
    source_subdir = None
    for sub in PRUNE_SOURCE_CANDIDATES:
        candidate = (raw_dir / sub / core_rel) if sub else (raw_dir / core_rel)
        if candidate.is_dir():
            source_core = candidate
            source_subdir = sub or "."
            break
    if source_core is None:
        return (False, None)
    target = dest_dir / core_rel
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_core, target)
    # Count only .java files for the log
    file_count = sum(1 for _ in source_core.rglob("*.java"))
    return (True, {"files": file_count, "source_subdir": source_subdir})


def run_prune_only_for_version(root: Path | None, version: str) -> tuple[bool, str]:
    """
    Run only the prune: copy com/hypixel/hytale from decompiled_raw/<version> to decompiled/<version>.
    Returns (True, "") or (False, "no_raw"|"prune_failed").
    """
    from . import i18n

    root = root or config_impl.get_project_root()
    raw_dir = config_impl.get_decompiled_raw_dir(root, version)
    decompiled_dir = config_impl.get_decompiled_dir(root, version)
    if not raw_dir.is_dir():
        return (False, "no_raw")
    print(i18n.t("cli.prune.running", version=version, raw_dir=raw_dir))
    ok, stats = prune_to_core(raw_dir, decompiled_dir)
    if not ok:
        print(i18n.t("cli.prune.no_core", raw_dir=raw_dir), file=sys.stderr)
        return (False, "prune_failed")
    print(i18n.t("cli.prune.done", files=stats["files"], dest=decompiled_dir, subdir=stats["source_subdir"]))
    return (True, "")


def run_prune_only(
    root: Path | None = None,
    versions: list[str] | None = None,
) -> tuple[bool, str]:
    """
    Run only the prune for one or more versions.
    If versions is None, process those that have an existing decompiled_raw folder.
    """
    root = root or config_impl.get_project_root()
    if versions is None:
        versions = [
            v for v in config_impl.VALID_SERVER_VERSIONS
            if config_impl.get_decompiled_raw_dir(root, v).is_dir()
        ]
        if not versions:
            return (False, "no_raw")
    for version in versions:
        ok, err = run_prune_only_for_version(root, version)
        if not ok:
            return (False, err)
    return (True, "")
