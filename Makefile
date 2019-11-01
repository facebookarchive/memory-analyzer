PYTHON?=python3

.PHONY: venv
venv:
	$(PYTHON) -m venv .venv
	@echo 'run `source .venv/bin/activate` to use virtualenv'

# The rest of these are intended to be run within the venv, where python points
# to whatever was used to set up the venv.
#
.PHONY: setup
setup:
	python3 -m pip install -Ur requirements.txt
	python3 -m pip install -Ur requirements-dev.txt

.PHONY: test
test:
	python3 -m coverage run -m memory_analyzer.tests
	python3 -m coverage report --omit='.venv/*,.tox/*' --show-missing

.PHONY: format
format:
	@/bin/bash -c 'die() { echo "$$1"; exit 1; }; \
	  while read filename; do \
	  grep -q "Copyright (c) Facebook" "$$filename" || \
	    die "Missing copyright in $$filename"; \
	  grep -q "#!/usr/bin/env python3" "$$filename" || \
	    die "Missing #! in $$filename"; \
	  done < <( git ls-tree -r --name-only HEAD | grep ".py$$" )'
	isort --recursive -y memory_analyzer setup.py
	black memory_analyzer setup.py

.PHONY: release
release:
	pip install -U wheel
	rm -r dist
	python3 setup.py sdist bdist_wheel
	twine upload dist/*

# Run this via 'tox -e integration' -- this verifies that templates are
# packaged, and that nothing is leaking through from the repo.
.PHONY: integrationtest
integrationtest:
	which memory_analyzer
	python3 -m unittest memory_analyzer.integrationtest
