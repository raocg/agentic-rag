# Agentic RAG com n8n

Sistema de RAG (Retrieval-Augmented Generation) configurado com n8n para criar workflows automatizados de ingestão, busca e resposta de documentos usando IA.

## Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Workflows Disponíveis](#workflows-disponíveis)
- [Uso](#uso)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)

## Visão Geral

Este projeto fornece uma infraestrutura completa para criar sistemas RAG usando n8n como plataforma de automação. Inclui:

- **n8n**: Plataforma de automação de workflows
- **Qdrant**: Banco de dados vetorial para armazenar embeddings
- **PostgreSQL**: Banco de dados para persistência do n8n
- **Redis**: Fila de execução para processamento assíncrono
- **Ollama**: LLM local (opcional, pode usar OpenAI API)

## Arquitetura

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Cliente   │────▶│   n8n API    │────▶│   Qdrant    │
└─────────────┘     └──────────────┘     │  (Vectors)  │
                           │              └─────────────┘
                           │
                    ┌──────▼──────┐       ┌─────────────┐
                    │  PostgreSQL │       │    Redis    │
                    │  (Storage)  │       │   (Queue)   │
                    └─────────────┘       └─────────────┘
                           │
                    ┌──────▼──────┐
                    │   Ollama/   │
                    │   OpenAI    │
                    │    (LLM)    │
                    └─────────────┘
```

## Pré-requisitos

- Docker e Docker Compose instalados
- Pelo menos 4GB de RAM disponível
- Porta 5678 (n8n), 6333 (Qdrant) e 11434 (Ollama) disponíveis
- API Key da OpenAI (ou usar Ollama para LLM local)

## Instalação

1. Clone o repositório:
```bash
git clone <repository-url>
cd agentic-rag
```

2. Copie o arquivo de exemplo de variáveis de ambiente:
```bash
cp .env.example .env
```

3. Edite o arquivo `.env` e configure suas credenciais:
```bash
nano .env
```

Principais configurações:
- `N8N_BASIC_AUTH_USER`: Usuário para acesso ao n8n
- `N8N_BASIC_AUTH_PASSWORD`: Senha para acesso ao n8n
- `OPENAI_API_KEY`: Sua API key da OpenAI (se usar GPT)
- `POSTGRES_PASSWORD`: Senha do banco de dados

4. Inicie os containers:
```bash
docker-compose up -d
```

5. Aguarde todos os serviços iniciarem (pode levar alguns minutos):
```bash
docker-compose logs -f
```

6. Acesse o n8n:
```
http://localhost:5678
```

## Configuração

### 1. Configurar Credenciais no n8n

Após acessar o n8n pela primeira vez:

1. Vá em **Settings** → **Credentials**
2. Clique em **Add Credential**
3. Adicione suas credenciais da OpenAI:
   - Nome: `OpenAI API`
   - API Key: Sua chave da OpenAI

### 2. Importar Workflows

Os workflows estão localizados em `n8n/workflows/`:

1. No n8n, vá em **Workflows** → **Import from File**
2. Importe cada arquivo JSON:
   - `01-document-ingestion.json` - Ingestão de documentos
   - `02-rag-query.json` - Consulta e resposta RAG
   - `03-batch-document-processing.json` - Processamento em lote

### 3. Ativar Workflows

Após importar, ative cada workflow clicando no botão **Active** em cada um.

## Workflows Disponíveis

### 1. Document Ingestion (Ingestão de Documentos)

**Propósito**: Recebe documentos via webhook, divide em chunks, cria embeddings e armazena no Qdrant.

**Endpoint**: `POST http://localhost:5678/webhook/ingest-document`

**Payload**:
```json
{
  "text": "Seu texto aqui...",
  "source": "nome_do_arquivo.pdf",
  "document_id": "doc_123"
}
```

**Fluxo**:
1. Recebe documento via webhook
2. Processa o texto
3. Divide em chunks de 1000 caracteres com overlap de 200
4. Cria embeddings usando OpenAI
5. Armazena no Qdrant
6. Retorna confirmação

### 2. RAG Query (Consulta e Resposta)

**Propósito**: Recebe uma pergunta, busca contexto relevante no Qdrant e gera resposta usando LLM.

**Endpoint**: `POST http://localhost:5678/webhook/query`

**Payload**:
```json
{
  "query": "Qual é a capital do Brasil?",
  "top_k": 5
}
```

**Fluxo**:
1. Recebe query via webhook
2. Cria embedding da query
3. Busca documentos similares no Qdrant (top K)
4. Agrega contexto dos documentos encontrados
5. Constrói prompt com contexto
6. Gera resposta usando GPT
7. Retorna resposta com metadados

### 3. Batch Document Processing (Processamento em Lote)

**Propósito**: Processa múltiplos documentos automaticamente em horário programado.

**Agendamento**: Diariamente às 2h da manhã (configurável)

**Fluxo**:
1. Dispara via schedule (cron)
2. Lê arquivos de um diretório
3. Processa em lotes de 10 documentos
4. Cria embeddings e armazena no Qdrant
5. Gera relatório de processamento

## Uso

### Exemplo: Ingestão de Documento

```bash
curl -X POST http://localhost:5678/webhook/ingest-document \
  -H "Content-Type: application/json" \
  -d '{
    "text": "O Brasil é um país localizado na América do Sul. Sua capital é Brasília.",
    "source": "geografia.txt",
    "document_id": "geo_001"
  }'
```

Resposta:
```json
{
  "success": true,
  "message": "Document ingested successfully",
  "chunks": 1,
  "document_id": "geo_001"
}
```

### Exemplo: Consulta RAG

```bash
curl -X POST http://localhost:5678/webhook/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Qual é a capital do Brasil?",
    "top_k": 3
  }'
```

Resposta:
```json
{
  "query": "Qual é a capital do Brasil?",
  "answer": "A capital do Brasil é Brasília.",
  "sources_count": 3
}
```

## API Endpoints

### n8n UI
- URL: `http://localhost:5678`
- Auth: Basic (usuário e senha do .env)

### Qdrant Dashboard
- URL: `http://localhost:6333/dashboard`
- Sem autenticação (em desenvolvimento)

### Ollama API
- URL: `http://localhost:11434`
- Modelos disponíveis: `http://localhost:11434/api/tags`

## Estrutura do Projeto

```
agentic-rag/
├── docker-compose.yml          # Configuração dos containers
├── .env.example               # Exemplo de variáveis de ambiente
├── .gitignore                 # Arquivos ignorados pelo Git
├── README.md                  # Esta documentação
├── n8n/
│   ├── workflows/            # Workflows do n8n (JSON)
│   │   ├── 01-document-ingestion.json
│   │   ├── 02-rag-query.json
│   │   └── 03-batch-document-processing.json
│   └── backups/              # Backups dos workflows
└── docs/
    ├── ARCHITECTURE.md       # Arquitetura detalhada
    └── WORKFLOWS.md          # Guia de workflows
```

## Troubleshooting

### n8n não inicia

```bash
# Verificar logs
docker-compose logs n8n

# Reiniciar serviço
docker-compose restart n8n
```

### Qdrant não conecta

```bash
# Verificar se o Qdrant está rodando
docker-compose ps qdrant

# Verificar logs
docker-compose logs qdrant

# Testar conexão
curl http://localhost:6333/collections
```

### Embeddings falhando

Verifique se:
1. A API Key da OpenAI está correta no `.env`
2. As credenciais foram configuradas no n8n
3. Você tem créditos disponíveis na OpenAI

### Performance lenta

Se o processamento estiver lento:
1. Reduza o `chunk_size` nos workflows
2. Diminua o `top_k` nas consultas
3. Use modelos menores (ex: `gpt-4o-mini` ao invés de `gpt-4`)
4. Configure mais recursos para os containers Docker

## Próximos Passos

Sugestões de melhorias:

1. **Segurança**:
   - Adicionar autenticação JWT nos webhooks
   - Configurar HTTPS com certificados SSL
   - Implementar rate limiting

2. **Funcionalidades**:
   - Suporte para PDF, DOCX, HTML
   - Reranking de resultados
   - Cache de embeddings
   - Interface web para consultas

3. **Monitoramento**:
   - Adicionar Prometheus + Grafana
   - Logs estruturados
   - Alertas de falhas

4. **Escalabilidade**:
   - Kubernetes deployment
   - Load balancing
   - Replicação do Qdrant

## Recursos

- [n8n Documentation](https://docs.n8n.io/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Ollama Documentation](https://ollama.ai/docs)

## Licença

MIT License - veja LICENSE para detalhes.

## Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Suporte

Para questões e suporte:
- Abra uma issue no GitHub
- Entre em contato via e-mail

---

Desenvolvido com n8n, Qdrant e OpenAI
