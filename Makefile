
clean:
	isort .
	black .
	flake8 .

test:
	pytest
