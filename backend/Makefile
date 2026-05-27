.PHONY: lint format run

lint:
	ruff check app
	ruff format --check app

format:
	ruff check app --fix
	ruff format app

run:
	python run.py
