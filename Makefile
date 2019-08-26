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
	isort --recursive -y memory_analyzer tests
	black memory_analyzer tests
