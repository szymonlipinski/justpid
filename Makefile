
clean:
	isort .
	black .
	flake8 .

test:
	pytest

test-install:
	pip install -e .[test]

.PHONY: clean test test-install
