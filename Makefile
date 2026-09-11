# Pac-Man - Makefile
# Common automation tasks for the 42 Pac-Man project.

# The project installs into a local virtualenv so it never fights with the
# packages already present in the user's site-packages. Every target reuses
# that interpreter once it exists, and falls back to the system one before
# the first `make install` (or when PYTHON is set explicitly).
VENV    := .venv
VPYTHON := $(VENV)/bin/python
PYTHON  ?= $(if $(wildcard $(VPYTHON)),$(VPYTHON),python3)
CONFIG  ?= config.json
# Put the virtualenv first on PATH so `flake8` and `mypy` below are the ones
# installed by `make install`, while the rules stay the exact commands the
# subject asks for. Without a virtualenv this simply falls back to the
# interpreters found on the system PATH.
export PATH := $(CURDIR)/$(VENV)/bin:$(PATH)
MYPY_FLAGS = --warn-return-any --warn-unused-ignores \
	--ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

.PHONY: install run debug lint lint-strict test clean fclean

install: $(VPYTHON)
	$(VPYTHON) -m pip install --upgrade --quiet pip
	$(VPYTHON) -m pip install -r requirements.txt

$(VPYTHON):
	python3 -m venv $(VENV)

run:
	$(PYTHON) pac-man.py $(CONFIG)

debug:
	$(PYTHON) -m pdb pac-man.py $(CONFIG)

lint:
	flake8 .
	mypy . $(MYPY_FLAGS)

lint-strict:
	flake8 .
	mypy . --strict

test:
	$(PYTHON) -m pytest -q

clean:
	rm -rf __pycache__ */__pycache__ .mypy_cache .pytest_cache
	find . -type f -name '*.pyc' -delete

fclean: clean
	rm -rf build dist *.egg-info $(VENV)
