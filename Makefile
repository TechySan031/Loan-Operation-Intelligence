.PHONY: help dev up down db-migrate db-seed ingest-kb test lint eval

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev: ## Start all services for local development
	docker-compose up --build

up: ## Start services in background
	docker-compose up -d --build

down: ## Stop all services
	docker-compose down

db-migrate: ## Run Alembic migrations
	cd backend && alembic upgrade head

db-seed: ## Seed business rules and sample data
	cd backend && python -m scripts.seed_rules
	cd backend && python -m scripts.seed_sample_data

ingest-kb: ## Ingest knowledge base content
	cd backend && python -m scripts.ingest_kb

test: ## Run backend tests
	cd backend && pytest tests/ -v --tb=short

lint: ## Run linting
	cd backend && ruff check app/ --fix
	cd backend && ruff format app/

eval: ## Run evaluation suite
	cd backend && python -m scripts.run_eval

simulate: ## Simulate real-time call for nudge testing
	cd backend && python -m scripts.simulate_realtime

setup-vapi: ## Configure Vapi assistants
	cd backend && python -m scripts.setup_vapi
