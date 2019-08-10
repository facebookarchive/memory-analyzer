.PHONY: venv
venv:
	python3 -m venv .venv
	@echo 'run `source .venv/bin/activate` to use virtualenv'

# intended to be run within venv
.PHONY: setup
	python3 -m pip install -Ur requirements.txt

.PHONY: test
test:
	python3 -m coverage run -m tests
	python3 -m coverage report --omit='.venv/*'
