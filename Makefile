# AnchorPrune developer tasks (v0.9). Local-first; nothing here touches a network
# unless you explicitly run a real provider.

.PHONY: help dev test lint bench real-eval-smoke build migrate doctor compose-config demo

help:
	@echo "AnchorPrune make targets:"
	@echo "  make dev              Install the package with dev + api extras"
	@echo "  make test             Run the test suite"
	@echo "  make lint             Run ruff"
	@echo "  make bench            Regenerate the deterministic benchmark pack"
	@echo "  make real-eval-smoke  Run the offline mock real-eval"
	@echo "  make build            Build sdist+wheel and twine-check"
	@echo "  make migrate          Apply SQLite migrations"
	@echo "  make doctor           Diagnose the install"
	@echo "  make compose-config   Validate docker-compose.yml"
	@echo "  make demo             Run the v1.0 one-button offline demo"

demo:
	bash scripts/demo_v1.sh

dev:
	python -m pip install -e ".[dev,api]"

test:
	pytest

lint:
	ruff check .

bench:
	anchorprune pack --out benchmarks --window 2

real-eval-smoke:
	anchorprune real-eval --provider mock --model mock-deterministic \
		--scenarios coding_agent --trials 1 --out /tmp/real_eval_smoke

build:
	python -m build
	twine check dist/*

migrate:
	anchorprune db migrate --db .anchorprune/anchorprune.db

doctor:
	anchorprune doctor

compose-config:
	docker compose config >/dev/null && echo "docker-compose.yml is valid"
