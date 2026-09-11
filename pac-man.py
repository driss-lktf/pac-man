#!/usr/bin/env python3
"""Pac-Man entry point.

Usage::

    python3 pac-man.py config.json

The program takes exactly one argument: a configuration file.  Its name does
not matter but its content must be JSON, so the file is accepted or rejected
on what it contains rather than on its extension.  Every error (missing file,
bad argument, invalid value, generator failure) is reported with a clear
message and never as a Python traceback.
"""

from __future__ import annotations

import os
import sys
from typing import List

from pacman.app import App
from pacman.config import load_config


def usage(program: str) -> str:
    """Return the usage line matching how the program was started.

    Args:
        program: The value of ``argv[0]``.

    Returns:
        The command line the user should type.
    """
    if getattr(sys, "frozen", False):
        return f"Usage: ./{os.path.basename(program)} <config.json>"
    return "Usage: python3 pac-man.py <config.json>"


def main(argv: List[str]) -> int:
    """Validate arguments, load the config and run the game.

    Args:
        argv: The full process argument vector (``sys.argv``).

    Returns:
        An exit code: 0 on success, 1 on any handled error.
    """
    if len(argv) != 2:
        print(usage(argv[0] if argv else "pac-man.py"))
        return 1
    path = argv[1]

    try:
        config = load_config(path)
    except ValueError as error:
        print(f"Error: {error}")
        return 1

    try:
        App(config).run()
    except Exception as error:  # last-resort guard: no traceback for review
        print(f"Error: unexpected failure: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
