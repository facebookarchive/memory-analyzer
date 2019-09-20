PYTHON?=python3

.PHONY: venv
venv:
	$(PYTHON) -m venv .venv
	@echo 'run `source .venv/bin/activate` to use virtualenv'

# intended to be run within venv
.PHONY: setup
setup:
	$(PYTHON) -m pip install -Ur requirements.txt
	$(PYTHON) -m pip install -Ur requirements-dev.txt

.PHONY: test
test:
	$(PYTHON) -m coverage run -m memory_analyzer.tests
	$(PYTHON) -m coverage report --omit='.venv/*'

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
