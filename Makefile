.PHONY: help start stop restart logs status clean backup restore test

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Agentic RAG - Makefile Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

setup: ## Initial setup - copy .env.example to .env
	@echo "$(BLUE)Setting up environment...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✓ Created .env file. Please edit it with your credentials.$(NC)"; \
	else \
		echo "$(YELLOW)⚠ .env file already exists. Skipping.$(NC)"; \
	fi

start: ## Start all services
	@echo "$(BLUE)Starting all services...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✓ Services started successfully!$(NC)"
	@echo "$(YELLOW)Access n8n at: http://localhost:5678$(NC)"
	@echo "$(YELLOW)Access Qdrant at: http://localhost:6333/dashboard$(NC)"

stop: ## Stop all services
	@echo "$(BLUE)Stopping all services...$(NC)"
	@docker-compose stop
	@echo "$(GREEN)✓ Services stopped$(NC)"

restart: ## Restart all services
	@echo "$(BLUE)Restarting all services...$(NC)"
	@docker-compose restart
	@echo "$(GREEN)✓ Services restarted$(NC)"

down: ## Stop and remove all containers
	@echo "$(BLUE)Stopping and removing containers...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✓ Containers removed$(NC)"

logs: ## Show logs from all services
	@docker-compose logs -f

logs-n8n: ## Show n8n logs
	@docker-compose logs -f n8n

logs-qdrant: ## Show Qdrant logs
	@docker-compose logs -f qdrant

logs-postgres: ## Show PostgreSQL logs
	@docker-compose logs -f postgres

status: ## Show status of all services
	@echo "$(BLUE)Services Status:$(NC)"
	@docker-compose ps

clean: ## Remove all containers, volumes and clean up
	@echo "$(RED)⚠ This will remove all data! Press Ctrl+C to cancel...$(NC)"
	@sleep 5
	@docker-compose down -v
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

backup: ## Backup n8n database and Qdrant data
	@echo "$(BLUE)Creating backup...$(NC)"
	@mkdir -p backups
	@docker exec n8n-postgres pg_dump -U n8n n8n | gzip > backups/n8n-db-$$(date +%Y%m%d-%H%M%S).sql.gz
	@echo "$(GREEN)✓ PostgreSQL backup created$(NC)"
	@curl -X POST http://localhost:6333/collections/documents/snapshots > /dev/null 2>&1
	@echo "$(GREEN)✓ Qdrant snapshot created$(NC)"

restore-db: ## Restore PostgreSQL database (usage: make restore-db FILE=backup.sql.gz)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)Error: Please specify FILE=backup.sql.gz$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Restoring database from $(FILE)...$(NC)"
	@gunzip -c $(FILE) | docker exec -i n8n-postgres psql -U n8n n8n
	@echo "$(GREEN)✓ Database restored$(NC)"

shell-n8n: ## Open shell in n8n container
	@docker exec -it n8n sh

shell-postgres: ## Open PostgreSQL shell
	@docker exec -it n8n-postgres psql -U n8n n8n

shell-qdrant: ## Open shell in Qdrant container
	@docker exec -it n8n-qdrant sh

test-ingest: ## Test document ingestion endpoint
	@echo "$(BLUE)Testing document ingestion...$(NC)"
	@curl -X POST http://localhost:5678/webhook/ingest-document \
		-H "Content-Type: application/json" \
		-d '{"text":"O Brasil é um país localizado na América do Sul. Sua capital é Brasília.","source":"test.txt","document_id":"test_001"}' \
		| jq .
	@echo "$(GREEN)✓ Test completed$(NC)"

test-query: ## Test RAG query endpoint
	@echo "$(BLUE)Testing RAG query...$(NC)"
	@curl -X POST http://localhost:5678/webhook/query \
		-H "Content-Type: application/json" \
		-d '{"query":"Qual é a capital do Brasil?","top_k":3}' \
		| jq .
	@echo "$(GREEN)✓ Test completed$(NC)"

qdrant-collections: ## List Qdrant collections
	@echo "$(BLUE)Qdrant Collections:$(NC)"
	@curl -s http://localhost:6333/collections | jq .

qdrant-status: ## Show Qdrant status
	@echo "$(BLUE)Qdrant Status:$(NC)"
	@curl -s http://localhost:6333/ | jq .

qdrant-count: ## Count documents in Qdrant
	@echo "$(BLUE)Document count:$(NC)"
	@curl -s http://localhost:6333/collections/documents/points/count | jq .

ollama-list: ## List installed Ollama models
	@echo "$(BLUE)Installed Ollama models:$(NC)"
	@docker exec n8n-ollama ollama list

ollama-pull: ## Pull an Ollama model (usage: make ollama-pull MODEL=llama3.2)
	@if [ -z "$(MODEL)" ]; then \
		echo "$(RED)Error: Please specify MODEL=model_name$(NC)"; \
		echo "Available models: llama3.2, mistral, phi3"; \
		exit 1; \
	fi
	@echo "$(BLUE)Pulling $(MODEL)...$(NC)"
	@docker exec n8n-ollama ollama pull $(MODEL)
	@echo "$(GREEN)✓ Model pulled successfully$(NC)"

update: ## Update all Docker images
	@echo "$(BLUE)Updating Docker images...$(NC)"
	@docker-compose pull
	@echo "$(GREEN)✓ Images updated. Run 'make restart' to apply changes.$(NC)"

health: ## Check health of all services
	@echo "$(BLUE)Checking service health...$(NC)"
	@echo "$(YELLOW)n8n:$(NC)"
	@curl -s http://localhost:5678/healthz > /dev/null && echo "  $(GREEN)✓ Healthy$(NC)" || echo "  $(RED)✗ Unhealthy$(NC)"
	@echo "$(YELLOW)Qdrant:$(NC)"
	@curl -s http://localhost:6333/healthz > /dev/null && echo "  $(GREEN)✓ Healthy$(NC)" || echo "  $(RED)✗ Unhealthy$(NC)"
	@echo "$(YELLOW)PostgreSQL:$(NC)"
	@docker exec n8n-postgres pg_isready -U n8n > /dev/null 2>&1 && echo "  $(GREEN)✓ Healthy$(NC)" || echo "  $(RED)✗ Unhealthy$(NC)"
	@echo "$(YELLOW)Redis:$(NC)"
	@docker exec n8n-redis redis-cli ping > /dev/null 2>&1 && echo "  $(GREEN)✓ Healthy$(NC)" || echo "  $(RED)✗ Unhealthy$(NC)"

dev: ## Start services in development mode (with logs)
	@echo "$(BLUE)Starting in development mode...$(NC)"
	@docker-compose up

install: setup start ## Complete installation (setup + start)
	@echo "$(GREEN)✓ Installation complete!$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "1. Edit .env file with your credentials"
	@echo "2. Run 'make restart' to apply changes"
	@echo "3. Access n8n at http://localhost:5678"
	@echo "4. Import workflows from n8n/workflows/"
