# Punto de entrada del CLI: dispatch por subcomando.

import sys
from pathlib import Path

from ... import i18n
from ...infrastructure import config_impl

from . import context
from . import help as cli_help
from . import lang
from . import config_cmd
from . import query
from . import mcp_cmd


def main() -> int:
    """Punto de entrada del CLI."""
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        cli_help.print_help()
        return 0

    subcommand = args[0].lower()
    root = config_impl.get_project_root()

    if subcommand == "config_impl":
        result = config_cmd.run_config(args, root)
        if result != 0:
            return result
        cli_help.print_help()
        return 0
    if subcommand == "query":
        return query.run_query(args, root)
    if subcommand == "mcp":
        return mcp_cmd.run_mcp(args, root)

    if subcommand in ("context", "ctx"):
        if len(args) < 2:
            cli_help.print_help()
            return 0
        return context.run_context(args, root)

    if subcommand == "lang":
        if len(args) < 2:
            cli_help.print_help()
            return 0
        return lang.run_lang(args, root)

    print(i18n.t("cli.unknown_command", cmd=subcommand), file=sys.stderr)
    cli_help.print_help()
    return 1
