.PHONY: build up down restart logs clean test help

DCGM_DIR ?= $(HOME)/Workspace/DCGM/_out/Linux-amd64-debug
IMAGE_NAME ?= dcgm-fake-gpu-exporter
IMAGE_TAG ?= latest

help: ## Show this help message
	@echo "DCGM Fake GPU Exporter - Make Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

build: ## Build Docker image
	@echo "Building Docker image..."
	@if [ ! -d "$(DCGM_DIR)" ]; then \
		echo "Error: DCGM_DIR not found: $(DCGM_DIR)"; \
		echo "Please set DCGM_DIR or build DCGM first"; \
		exit 1; \
	fi
	./build.sh

up: ## Start containers
	docker-compose up -d

down: ## Stop containers
	docker-compose down

restart: down up ## Restart containers

logs: ## View container logs
	docker-compose logs -f dcgm-exporter

logs-all: ## View all container logs
	docker-compose logs -f

ps: ## Show running containers
	docker-compose ps

test: ## Test the exporter
	@echo "Testing DCGM exporter..."
	@sleep 5
	@curl -f http://localhost:9400/health > /dev/null 2>&1 && echo "✓ Health check passed" || echo "✗ Health check failed"
	@curl -s http://localhost:9400/metrics | grep -q "dcgm_gpu_temp" && echo "✓ Metrics available" || echo "✗ No metrics found"
	@echo ""
	@echo "Sample metrics:"
	@curl -s http://localhost:9400/metrics | grep "dcgm_gpu_temp{" | head -4

test-full: up ## Start and test
	@echo "Starting containers..."
	@sleep 15
	@$(MAKE) test

clean: down ## Clean up containers and volumes
	docker-compose down -v
	docker rmi $(IMAGE_NAME):$(IMAGE_TAG) 2>/dev/null || true

clean-all: clean ## Clean everything including DCGM build artifacts
	rm -rf dcgm/

shell: ## Open shell in container
	docker exec -it dcgm-exporter bash

metrics: ## Show current metrics
	@curl -s http://localhost:9400/metrics

health: ## Check health endpoint
	@curl -s http://localhost:9400/health

with-prometheus: ## Start with Prometheus
	docker-compose --profile with-prometheus up -d
	@echo ""
	@echo "Services started:"
	@echo "  Exporter:   http://localhost:9400/metrics"
	@echo "  Prometheus: http://localhost:9090"

lint: ## Lint Python code
	@echo "Linting Python files..."
	@command -v flake8 >/dev/null 2>&1 || { echo "flake8 not installed. Install: pip install flake8"; exit 1; }
	flake8 dcgm_exporter.py dcgm_fake_manager.py --max-line-length=100 || true

format: ## Format Python code with black
	@echo "Formatting Python files..."
	@command -v black >/dev/null 2>&1 || { echo "black not installed. Install: pip install black"; exit 1; }
	black dcgm_exporter.py dcgm_fake_manager.py

shellcheck: ## Check shell scripts
	@echo "Checking shell scripts..."
	@command -v shellcheck >/dev/null 2>&1 || { echo "shellcheck not installed"; exit 1; }
	shellcheck build.sh docker-entrypoint.sh || true

validate: lint shellcheck ## Run all validation

install-dev-deps: ## Install development dependencies
	pip install flake8 black pylint

dcgmi: ## Run dcgmi in container
	docker exec -it dcgm-exporter \
		/root/Workspace/DCGM/_out/Linux-amd64-debug/share/dcgm_tests/apps/amd64/dcgmi $(ARGS)

dmon: ## Run dcgmi dmon in container
	docker exec -it dcgm-exporter \
		/root/Workspace/DCGM/_out/Linux-amd64-debug/share/dcgm_tests/apps/amd64/dcgmi dmon -e 150,155,203,204

discovery: ## Run GPU discovery in container
	docker exec -it dcgm-exporter \
		/root/Workspace/DCGM/_out/Linux-amd64-debug/share/dcgm_tests/apps/amd64/dcgmi discovery -l

status: ## Show DCGM status in container
	docker exec -it dcgm-exporter python3 /usr/local/bin/dcgm_fake_manager.py status
