"""Pac-Man game package.

A modular, object-oriented re-creation of the classic arcade game,
built for the 42 'Pac-Man' project.
"""

import os as _os

# Hide pygame's import banner so the program output stays clean.
_os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

__all__ = ["__version__"]

__version__ = "1.0.0"
