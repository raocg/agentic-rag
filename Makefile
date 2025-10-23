.PHONY: help start stop restart logs build clean install test

help:
	@echo "Agentic RAG - Comandos disponíveis:"
	@echo ""
	@echo "  make start     - Inicia todos os serviços"
	@echo "  make stop      - Para todos os serviços"
	@echo "  make restart   - Reinicia todos os serviços"
	@echo "  make logs      - Mostra logs dos serviços"
	@echo "  make build     - Build das imagens Docker"
	@echo "  make clean     - Remove containers e volumes"
	@echo "  make install   - Instala dependências"
	@echo "  make test      - Roda testes"
	@echo "  make n8n-build - Build do nó customizado n8n"

start:
	docker-compose up -d
	@echo "✓ Serviços iniciados"
	@echo "  n8n: http://localhost:5678"
	@echo "  API: http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

stop:
	docker-compose down
	@echo "✓ Serviços parados"

restart:
	docker-compose restart
	@echo "✓ Serviços reiniciados"

logs:
	docker-compose logs -f

build:
	docker-compose build
	@echo "✓ Build completo"

clean:
	docker-compose down -v
	@echo "✓ Containers e volumes removidos"

install:
	@echo "Instalando dependências da API..."
	cd api && pip install -r requirements.txt
	@echo "Instalando dependências do nó n8n..."
	cd n8n-nodes && npm install
	@echo "✓ Dependências instaladas"

test:
	@echo "Rodando testes da API..."
	cd api && pytest tests/ -v
	@echo "Rodando testes do nó n8n..."
	cd n8n-nodes && npm test
	@echo "✓ Testes completos"

n8n-build:
	@echo "Building nó customizado n8n..."
	cd n8n-nodes && npm run build
	docker-compose restart n8n
	@echo "✓ Nó n8n atualizado"

dev-api:
	cd api && uvicorn src.main:app --reload --port 8000

dev-n8n:
	cd n8n-nodes && npm run dev

status:
	@echo "Status dos serviços:"
	@docker-compose ps
