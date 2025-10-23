# Setup Guide - Agentic RAG with n8n Integration

Este guia completo vai te ajudar a configurar todo o ambiente para trabalhar com n8n e Claude Code.

## Pré-requisitos

- Docker e Docker Compose instalados
- Node.js 18+ (para desenvolvimento do nó customizado)
- Python 3.11+ (para desenvolvimento da API)
- API Key da Anthropic (Claude)
- Git

## Estrutura do Projeto

```
agentic-rag/
├── n8n-nodes/              # Nós customizados do n8n
│   ├── nodes/              # Código dos nós
│   ├── credentials/        # Credenciais para APIs
│   └── package.json        # Dependências
├── workflows/              # Templates de workflows JSON
├── api/                    # Backend API FastAPI
│   ├── src/
│   │   ├── routes/        # Endpoints da API
│   │   ├── services/      # Lógica de negócio
│   │   ├── models/        # Schemas Pydantic
│   │   └── main.py        # Aplicação principal
│   └── requirements.txt
├── docs/                   # Documentação
├── config/                 # Configurações
└── docker-compose.yml      # Orquestração dos serviços
```

## Instalação Rápida

### 1. Clone o repositório

```bash
git clone <seu-repositorio>
cd agentic-rag
```

### 2. Configure as variáveis de ambiente

```bash
# Copie o arquivo de exemplo
cp api/.env.example api/.env

# Edite e adicione sua API key da Anthropic
nano api/.env
```

Adicione sua chave:
```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

### 3. Inicie os serviços com Docker

```bash
docker-compose up -d
```

Isso vai iniciar:
- **n8n**: http://localhost:5678 (user: admin, pass: admin123)
- **API RAG**: http://localhost:8000
- **PostgreSQL**: porta 5432
- **Redis**: porta 6379

### 4. Instale o nó customizado do n8n

```bash
# Entre no container do n8n
docker exec -it agentic-rag-n8n /bin/sh

# Navegue até o diretório de nós customizados
cd /home/node/.n8n/custom

# Instale as dependências
npm install

# Build do nó
npm run build

# Reinicie o n8n
exit
docker-compose restart n8n
```

## Desenvolvimento Local (Sem Docker)

### API Backend

```bash
cd api

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure o .env
cp .env.example .env
# Edite .env com suas configurações

# Rode a API
uvicorn src.main:app --reload --port 8000
```

A API estará disponível em: http://localhost:8000
Documentação interativa: http://localhost:8000/docs

### Nó Customizado n8n

```bash
cd n8n-nodes

# Instale as dependências
npm install

# Desenvolva com watch mode
npm run dev
```

### n8n Local

```bash
# Instale n8n globalmente
npm install n8n -g

# Rode n8n
n8n start
```

## Verificação da Instalação

### 1. Teste a API

```bash
# Health check
curl http://localhost:8000/health

# Teste de upload de documento
curl -X POST "http://localhost:8000/api/documents/add-text" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Claude é um assistente de IA desenvolvido pela Anthropic.",
    "knowledge_base_id": "default",
    "metadata": {"source": "test"}
  }'

# Teste de query RAG
curl -X POST "http://localhost:8000/api/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quem desenvolveu o Claude?",
    "knowledge_base_id": "default",
    "top_k": 3
  }'
```

### 2. Configure n8n

1. Acesse http://localhost:5678
2. Login: admin / admin123
3. Vá em **Settings** → **Credentials**
4. Adicione nova credencial "Claude API"
5. Cole sua API Key da Anthropic

### 3. Importe um workflow

1. No n8n, clique em "Import workflow"
2. Navegue até `workflows/claude-rag-workflow.json`
3. Importe o workflow
4. Configure as credenciais
5. Ative o workflow

## Uso

### 1. Via n8n Interface

Use a interface visual do n8n para criar workflows que:
- Respondem a webhooks
- Processam documentos
- Executam tarefas agênticas
- Integram com outras ferramentas

### 2. Via API Direta

```python
import requests

# Query RAG
response = requests.post(
    "http://localhost:8000/api/rag/query",
    json={
        "query": "Sua pergunta aqui",
        "knowledge_base_id": "default",
        "top_k": 5
    }
)
print(response.json()["answer"])

# Execute tarefa agêntica
response = requests.post(
    "http://localhost:8000/api/agent/execute",
    json={
        "task": "Analise os logs e resuma os erros",
        "model": "claude-3-5-sonnet-20241022"
    }
)
print(response.json()["result"])
```

### 3. Via Claude Code

Você pode usar o Claude Code para:
- Editar os nós customizados
- Modificar workflows JSON
- Desenvolver novos endpoints na API
- Criar novos agentes e ferramentas

## Workflows de Exemplo

### 1. RAG Query via Webhook

Importar: `workflows/claude-rag-workflow.json`

Webhook → Claude RAG Query → Respond

### 2. Tarefa Agêntica Agendada

Importar: `workflows/agent-task-workflow.json`

Schedule → Execute Command → Claude Agent → Slack

## Próximos Passos

1. **Adicione seus documentos**: Use a API para fazer upload de seus documentos
2. **Crie workflows**: Use a interface do n8n para criar automações
3. **Desenvolva ferramentas**: Adicione novas ferramentas para o agente
4. **Personalize**: Ajuste os prompts e parâmetros conforme necessário

## Troubleshooting

### n8n não reconhece o nó customizado

```bash
# Verifique se o build foi feito
cd n8n-nodes
npm run build

# Reinicie o n8n
docker-compose restart n8n
```

### API retorna erro de API key

```bash
# Verifique se a variável de ambiente está configurada
docker exec agentic-rag-api env | grep ANTHROPIC
```

### Vector store vazio

```bash
# Adicione documentos primeiro
curl -X POST "http://localhost:8000/api/documents/add-text" \
  -H "Content-Type: application/json" \
  -d '{"content": "Seu conteúdo aqui"}'
```

## Suporte

Para problemas ou dúvidas, abra uma issue no repositório.
