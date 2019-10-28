.PHONY: venv
venv:
	python3 -m venv .venv
	@echo 'run `source .venv/bin/activate` to use virtualenv'

# intended to be run within venv
.PHONY: setup
	python3 -m pip install -Ur requirements.txt
	python3 -m pip install -Ur requirements-dev.txt

.PHONY: test
test:
	python3 -m coverage run -m tests
	python3 -m coverage report --omit='.venv/*'

.PHONY: format
format:
	@/bin/bash -c 'die() { echo "$$1"; exit 1; }; \
	  while read filename; do \
	  grep -q "Copyright (c) Facebook" "$$filename" || \
	    die "Missing copyright in $$filename"; \
	  grep -q "#!/usr/bin/env python3" "$$filename" || \
	    die "Missing #! in $$filename"; \
	  done < <( git ls-tree -r --name-only HEAD | grep ".py$$" )'
	isort --recursive -y memory_analyzer tests
	black memory_analyzer tests
