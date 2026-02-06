# Comando mcp: inicia el servidor MCP.

import sys
from pathlib import Path

from ... import i18n
from ...infrastructure import config_impl

from . import args as cli_args


def cmd_mcp(
    _root: Path | None = None,
    transport: str = "stdio",
    host: str = "0.0.0.0",
    port: int = 8000,
) -> int:
    """Inicia el servidor MCP para IA. Por defecto stdio; con transport streamable-http escucha en host:port."""
    root = _root or config_impl.get_project_root()
    if sys.stderr.isatty():
        if transport == "streamable-http":
            print(i18n.t("cli.mcp.instructions_http_title"), file=sys.stderr)
            print(i18n.t("cli.mcp.instructions_http_ready", host=host, port=port), file=sys.stderr)
            print(i18n.t("cli.mcp.instructions_http_url", url=f"http://{host}:{port}/mcp"), file=sys.stderr)
        else:
            cwd = str(root.resolve())
            command = sys.executable
            args_str = "main.py mcp"
            print(i18n.t("cli.mcp.instructions_title"), file=sys.stderr)
            print(i18n.t("cli.mcp.instructions_intro"), file=sys.stderr)
            print(i18n.t("cli.mcp.instructions_command", command=command), file=sys.stderr)
            print(i18n.t("cli.mcp.instructions_args", args=args_str), file=sys.stderr)
            print(i18n.t("cli.mcp.instructions_cwd", cwd=cwd), file=sys.stderr)
            print(i18n.t("cli.mcp.instructions_ready"), file=sys.stderr)
    from .. import mcp_server
    try:
        mcp_server.run(transport=transport, host=host, port=port)
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(i18n.t("cli.query.error", msg=str(e)), file=sys.stderr)
        return 1


def run_mcp(args: list[str], root: Path) -> int:
    """Dispatch del comando mcp."""
    transport, host, port = cli_args.parse_mcp_args(args, 1)
    return cmd_mcp(root, transport=transport, host=host, port=port)
