# Coloured CLI output (phase, success, error). Respects TTY and NO_COLOR.

import os
import sys

from colorama import Fore, Style


def _use_color(stream) -> bool:
    """Return True if we should emit colour for the given stream (TTY and NO_COLOR not set)."""
    return stream.isatty() and not os.environ.get("NO_COLOR")


def phase(msg: str) -> None:
    """Print a phase header to stdout (cyan when colour is enabled)."""
    if _use_color(sys.stdout):
        print(Fore.CYAN + msg + Style.RESET_ALL)
    else:
        print(msg)


def success(msg: str) -> None:
    """Print a success message to stdout (green when colour is enabled)."""
    if _use_color(sys.stdout):
        print(Fore.GREEN + msg + Style.RESET_ALL)
    else:
        print(msg)


def error(msg: str) -> None:
    """Print an error message to stderr (red when colour is enabled)."""
    if _use_color(sys.stderr):
        print(Fore.RED + msg + Style.RESET_ALL, file=sys.stderr)
    else:
        print(msg, file=sys.stderr)
