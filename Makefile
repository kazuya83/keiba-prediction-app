PYTHON_PROJECT_DIR := backend
FRONTEND_PROJECT_DIR := frontend

.PHONY: setup fmt lint test up down clean

setup:
	@echo "==> Installing backend dependencies with Poetry"
	cd $(PYTHON_PROJECT_DIR) && poetry install --no-root
	@echo "==> Installing frontend dependencies with pnpm"
	cd $(FRONTEND_PROJECT_DIR) && pnpm install

fmt:
	@echo "==> Formatting backend (black, isort)"
	cd $(PYTHON_PROJECT_DIR) && poetry run black .
	cd $(PYTHON_PROJECT_DIR) && poetry run isort .
	@echo "==> Formatting frontend (prettier)"
	cd $(FRONTEND_PROJECT_DIR) && pnpm exec prettier --write .

format: fmt

lint:
	@echo "==> Linting backend (flake8, mypy)"
	cd $(PYTHON_PROJECT_DIR) && poetry run flake8 .
	cd $(PYTHON_PROJECT_DIR) && poetry run mypy .
	@echo "==> Linting frontend (eslint)"
	cd $(FRONTEND_PROJECT_DIR) && pnpm exec eslint "src/**/*.{ts,tsx}"

test:
	@echo "==> Running backend tests (pytest)"
	cd $(PYTHON_PROJECT_DIR) && poetry run pytest
	@echo "==> Running frontend tests (vitest)"
	cd $(FRONTEND_PROJECT_DIR) && pnpm test

up:
	docker compose up -d

down:
	docker compose down

clean:
	@echo "==> Cleaning caches and virtual environments"
	cd $(PYTHON_PROJECT_DIR) && poetry env remove --all || true
	cd $(FRONTEND_PROJECT_DIR) && pnpm store prune

