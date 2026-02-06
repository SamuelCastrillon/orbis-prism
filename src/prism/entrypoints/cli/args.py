# Parsers de argumentos del CLI y constantes de flags.

import os
from pathlib import Path

from ...domain.constants import VALID_SERVER_VERSIONS, normalize_version

VERSION_FLAG_ALL = ("--all", "-a")
QUERY_JSON_FLAGS = ("--json", "-j")
QUERY_LIMIT_FLAGS = ("--limit", "-n")
MCP_HTTP_FLAGS = ("--http", "-H")
MCP_PORT_FLAGS = ("--port", "-p")
MCP_HOST_FLAGS = ("--host",)
ENV_MCP_TRANSPORT = "MCP_TRANSPORT"
ENV_MCP_PORT = "MCP_PORT"
ENV_MCP_HOST = "MCP_HOST"


def parse_version_arg(args: list[str], start_index: int) -> tuple[str | None, bool]:
    """
    Parsea el argumento de versión. Devuelve (version, invalid).
    version: 'release' | 'prerelease' | None (all). Sin argumento -> por defecto 'release'.
    invalid: True si el argumento no es válido.
    """
    if len(args) <= start_index:
        return ("release", False)
    a = args[start_index].strip().lower()
    if a in VERSION_FLAG_ALL:
        return (None, False)
    if a in VALID_SERVER_VERSIONS:
        return (a, False)
    return (None, True)


def parse_query_args(args: list[str]) -> tuple[str | None, str, int, bool]:
    """
    Parsea args del comando query (desde args[1]).
    Devuelve (query_term, version, limit, output_json). query_term es None si no se dio término.
    """
    output_json = False
    limit = 30
    positionals = []
    i = 1
    while i < len(args):
        a = args[i]
        if a in QUERY_JSON_FLAGS:
            output_json = True
            i += 1
        elif a in QUERY_LIMIT_FLAGS:
            if i + 1 < len(args):
                try:
                    limit = int(args[i + 1])
                    limit = max(1, min(limit, 500))
                except ValueError:
                    pass
                i += 2
            else:
                i += 1
        elif a.startswith("-"):
            i += 1
        else:
            positionals.append(a)
            i += 1
    term = positionals[0] if positionals else None
    version = positionals[1] if len(positionals) > 1 else "release"
    version = normalize_version(version)
    return (term, version, limit, output_json)


def parse_mcp_args(args: list[str], start_index: int) -> tuple[str, str, int]:
    """
    Parsea argumentos del comando mcp (desde args[start_index]).
    También lee MCP_TRANSPORT, MCP_HOST, MCP_PORT (el CLI sobreescribe env).
    Devuelve (transport, host, port). transport: "stdio" | "streamable-http".
    """
    transport = "stdio"
    host = "0.0.0.0"
    port = 8000
    env_transport = os.environ.get(ENV_MCP_TRANSPORT, "").strip().lower()
    if env_transport in ("http", "streamable-http"):
        transport = "streamable-http"
    try:
        port = int(os.environ.get(ENV_MCP_PORT, "8000"))
        port = max(1, min(port, 65535))
    except ValueError:
        pass
    host = os.environ.get(ENV_MCP_HOST, "0.0.0.0").strip() or "0.0.0.0"
    i = start_index
    while i < len(args):
        a = args[i]
        if a in MCP_HTTP_FLAGS:
            transport = "streamable-http"
            i += 1
        elif a in MCP_PORT_FLAGS:
            if i + 1 < len(args):
                try:
                    port = int(args[i + 1])
                    port = max(1, min(port, 65535))
                except ValueError:
                    pass
                i += 2
            else:
                i += 1
        elif a in MCP_HOST_FLAGS:
            if i + 1 < len(args):
                host = args[i + 1].strip() or host
                i += 2
            else:
                i += 1
        elif a.startswith("-"):
            i += 1
        else:
            i += 1
    return (transport, host, port)
