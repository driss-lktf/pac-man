#!/usr/bin/env bash
# Build a standalone Pac-Man executable and the archive to publish on Itch.io.
#
# Usage:
#   ./build.sh
#
# Outputs:
#   dist/pac-man            a single self-contained executable
#   dist/pac-man-release/   the folder a player unzips (binary, config,
#                           launcher and the in-package instructions)
#   dist/pac-man-linux.zip  that folder, ready to upload
set -euo pipefail

# Build inside the project virtualenv (created by `make install`) so the build
# dependencies never conflict with the packages installed on the machine.
if [ -z "${PYTHON:-}" ]; then
	[ -x .venv/bin/python ] || python3 -m venv .venv
	PYTHON=.venv/bin/python
fi

echo ">> Installing build dependencies..."
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install -r requirements.txt
"$PYTHON" -m pip install pyinstaller

echo ">> Cleaning previous build..."
rm -rf build dist

echo ">> Building with PyInstaller..."
"$PYTHON" -m PyInstaller pacman.spec

# The game takes exactly one argument, so a downloaded build needs a launcher
# that supplies it; double-clicking the bare executable would only print the
# usage line. The release folder also carries the minimal in-package
# instructions the subject asks for.
echo ">> Preparing the release folder..."
RELEASE=dist/pac-man-release
mkdir -p "$RELEASE"
cp dist/pac-man config.json "$RELEASE/"

cat > "$RELEASE/play.sh" <<'LAUNCHER'
#!/usr/bin/env bash
# Launch Pac-Man with the configuration file shipped next to it.
cd "$(dirname "$0")"
exec ./pac-man config.json
LAUNCHER
chmod +x "$RELEASE/play.sh" "$RELEASE/pac-man"

cat > "$RELEASE/README.txt" <<'INSTRUCTIONS'
Pac-Man - Ghosts! More ghosts!
==============================

RUN
  ./play.sh              (or: ./pac-man config.json)

CONTROLS
  Arrow keys or W A S D  move
  Esc                    pause / back
  Enter                  validate a menu entry

RULES
  Eat every pacgum to clear a level. The super-pacgums in the four corners
  make the ghosts edible for a few seconds. A ghost touch costs a life, and
  each level has a time limit. Your score and lives carry over between
  levels; at the end you can save your score under a name (10 characters
  max, letters, digits and spaces).

CHEAT MODE (for the peer review)
  F1 invincibility   F2 freeze ghosts   F3 skip level
  F4 extra life      F5 cycle player speed

OPTIONS
  Everything is configurable in config.json next to this file: lives, seed,
  time per level, points per pacgum / super-pacgum / ghost, speeds, ghost
  respawn delay, the number of pacgums and the list of levels with their
  maze sizes. The file is JSON and accepts # and // comments. Any missing
  or invalid value falls back to a safe default, so the game always starts.

  Highscores are stored in highscores.json, created next to the game.
INSTRUCTIONS

echo ">> Zipping the release..."
(cd dist && rm -f pac-man-linux.zip \
    && zip -q -r pac-man-linux.zip pac-man-release)

echo ">> Done."
echo ">> Executable:  ./dist/pac-man config.json"
echo ">> Release zip: dist/pac-man-linux.zip  (upload this to Itch.io)"
echo ">> To publish on Itch.io, see project_management/packaging.md"
