.PHONY: run test eval ingest docker-up lint setup

setup:
	pip install -r requirements.txt
	cp -n .env.example .env || true

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

eval:
	python eval/run_eval.py

ingest:
	python scripts/ingest.py

seed:
	python scripts/seed_vectorstore.py

docker-up:
	docker-compose -f docker/docker-compose.yaml up --build

lint:
	ruff check . --fix

demo:
	python -m src.chains.pipeline --demo
