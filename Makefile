.PHONY: install test test-integration migrate run docker-build docker-up docker-down docker-logs

install:
	python -m pip install -r requirements.txt

test:
	python -m pytest

test-integration:
	python -m pytest tests/integration -q

migrate:
	python -m alembic upgrade head

run:
	./startup.sh

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f enterprise-api
