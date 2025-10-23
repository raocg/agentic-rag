# Agentic RAG - Integração Completa n8n + Claude Code

Sistema completo de RAG (Retrieval-Augmented Generation) com capacidades agênticas, integrado com n8n para automação de workflows e otimizado para desenvolvimento com Claude Code.

## Visão Geral

Este projeto oferece **todas as formas** de trabalhar com n8n e Claude:

1. **Nós Customizados do n8n** - Componentes reutilizáveis para workflows
2. **Templates de Workflows** - Workflows prontos em JSON editáveis
3. **API Backend Completa** - FastAPI com RAG e sistema agêntico
4. **Sistema RAG Completo** - Vector store, embeddings, e busca semântica
5. **Agente Inteligente** - Agent com tool use para tarefas complexas

## Recursos Principais

- Nó customizado Claude RAG para n8n
- API REST completa para RAG e tarefas agênticas
- Vector store com ChromaDB
- Embeddings com Sentence Transformers
- Suporte a múltiplas bases de conhecimento
- Sistema de ferramentas extensível para agents
- Upload e processamento de documentos (PDF, TXT, MD, JSON, CSV)
- Docker Compose para deploy fácil
- Documentação completa

## Início Rápido

### Pré-requisitos

- Docker e Docker Compose
- API Key da Anthropic (Claude)

### Instalação (5 minutos)

```bash
# 1. Clone o repositório
git clone <seu-repo>
cd agentic-rag

# 2. Configure a API key
cp api/.env.example api/.env
# Edite api/.env e adicione: ANTHROPIC_API_KEY=sua-chave-aqui

# 3. Inicie todos os serviços
docker-compose up -d

# 4. Acesse as interfaces
# n8n: http://localhost:5678 (admin/admin123)
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

Pronto! Agora você tem:
- n8n rodando na porta 5678
- API RAG rodando na porta 8000
- PostgreSQL e Redis configurados
- Vector store inicializado

## Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                         n8n                             │
│  (Workflows, Automações, Nó Customizado Claude RAG)    │
└─────────────┬───────────────────────────┬───────────────┘
              │                           │
              ├── Webhooks               │
              ├── Schedules              ├── PostgreSQL
              └── Triggers               │
                          │               │
                          ↓               │
              ┌───────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────┐
│                    API Backend (FastAPI)                │
│  ┌──────────────┬──────────────┬─────────────────────┐  │
│  │  RAG Service │ Agent Service│ Document Service    │  │
│  └──────┬───────┴──────┬───────┴─────────┬───────────┘  │
│         │              │                 │              │
│         ↓              ↓                 ↓              │
│  ┌─────────────┐ ┌──────────┐    ┌──────────────┐     │
│  │ VectorStore │ │  Claude  │    │   Tools      │     │
│  │  (Chroma)   │ │ Service  │    │   System     │     │
│  └─────────────┘ └──────────┘    └──────────────┘     │
└─────────────────────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────────────┐
│  Storage: Redis (Cache) + Vector DB (ChromaDB)          │
└─────────────────────────────────────────────────────────┘
```

## Estrutura do Projeto

```
agentic-rag/
├── n8n-nodes/                    # Nós customizados do n8n
│   ├── nodes/
│   │   └── ClaudeRAG/
│   │       └── ClaudeRAG.node.ts # Nó principal
│   ├── credentials/
│   │   └── ClaudeApi.credentials.ts
│   ├── package.json
│   └── tsconfig.json
│
├── workflows/                     # Templates de workflows
│   ├── claude-rag-workflow.json
│   └── agent-task-workflow.json
│
├── api/                          # Backend API
│   ├── src/
│   │   ├── routes/              # Endpoints REST
│   │   ├── services/            # Lógica de negócio
│   │   ├── models/              # Schemas
│   │   └── main.py              # App principal
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── docs/                         # Documentação
│   ├── SETUP.md                 # Guia de instalação
│   ├── USAGE.md                 # Guia de uso
│   ├── API.md                   # Referência da API
│   └── EXAMPLES.md              # Exemplos práticos
│
├── docker-compose.yml            # Orquestração
├── Makefile                      # Comandos úteis
└── README.md                     # Este arquivo
```

## Uso Rápido

### Via API

```bash
# Upload documento
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@documento.pdf"

# Query RAG
curl -X POST "http://localhost:8000/api/rag/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Como funciona o sistema?"}'

# Execute agent
curl -X POST "http://localhost:8000/api/agent/execute" \
  -H "Content-Type: application/json" \
  -d '{"task": "Analise os logs e resuma os erros"}'
```

### Via Python

```python
import requests

# Query RAG
response = requests.post(
    "http://localhost:8000/api/rag/query",
    json={"query": "Sua pergunta", "top_k": 5}
)
print(response.json()["answer"])

# Execute agent
response = requests.post(
    "http://localhost:8000/api/agent/execute",
    json={"task": "Calcule a média de vendas"}
)
print(response.json()["result"])
```

### Com Claude Code

Claude Code pode ajudar você a:

```
"Adicione um parâmetro 'timeout' ao nó ClaudeRAG"
"Crie um workflow que processa PDFs automaticamente"
"Adicione uma ferramenta de web search ao agent"
"Crie um endpoint para sumarizar documentos"
```

## Comandos Make

```bash
make start      # Inicia todos os serviços
make stop       # Para todos os serviços
make logs       # Mostra logs
make build      # Build das imagens
make clean      # Remove containers e volumes
make test       # Roda testes
make n8n-build  # Build do nó customizado
```

## Documentação

- **[Guia de Instalação](docs/SETUP.md)** - Setup detalhado e troubleshooting
- **[Guia de Uso](docs/USAGE.md)** - Como usar todas as features
- **[API Reference](docs/API.md)** - Documentação completa da API
- **[Exemplos](docs/EXAMPLES.md)** - Exemplos práticos de uso

## Casos de Uso

1. **Sistema de Q&A Automático** - Responder perguntas via email/chat
2. **Processamento de Documentos** - Indexar e analisar documentos automaticamente
3. **Monitoramento Inteligente** - Analisar logs e tomar ações
4. **Documentação Interativa** - Busca inteligente em documentação
5. **Pesquisa e Sumários** - Gerar newsletters e relatórios automáticos

## Recursos

### Modelos Claude Suportados

- `claude-3-5-sonnet-20241022` (Recomendado)
- `claude-3-5-haiku-20241022` (Rápido)
- `claude-3-opus-20240229` (Mais capaz)

### Formatos de Documento

- Texto: `.txt`, `.md`
- PDF: `.pdf`
- Dados: `.json`, `.csv`

### Ferramentas do Agent

- `search_knowledge_base` - Busca na base de conhecimento
- `python_repl` - Executa código Python
- `web_search` - Busca na web (placeholder)

## Desenvolvimento

### Setup Local

```bash
# API Backend
cd api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload

# Nó n8n
cd n8n-nodes
npm install
npm run dev
```

### Testes

```bash
make test
```

## Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Licença

MIT License

---

Desenvolvido com Claude Code