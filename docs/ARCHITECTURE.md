# Arquitetura do Sistema Agentic RAG

Este documento descreve a arquitetura completa do sistema, decisões de design e como os componentes interagem.

## Visão Geral

O sistema implementa um pipeline RAG (Retrieval-Augmented Generation) completo usando n8n como orquestrador de workflows, permitindo criar aplicações de IA sem código.

## Componentes

### 1. n8n (Workflow Orchestrator)

**Responsabilidades**:
- Orquestração de workflows
- Gestão de execuções
- Interface visual para criação de workflows
- API para integração externa

**Configuração**:
- Porta: 5678
- Auth: Basic Authentication
- Database: PostgreSQL
- Queue: Redis (para execuções assíncronas)

**Escalabilidade**:
- Modo queue permite processamento paralelo
- Múltiplas workers podem ser adicionadas
- PostgreSQL permite persistência e auditoria

### 2. PostgreSQL (Persistence Layer)

**Responsabilidades**:
- Armazenar workflows e execuções
- Histórico de execuções
- Credenciais (criptografadas)
- Configurações

**Schema**:
```sql
-- Workflows
workflows
  - id
  - name
  - nodes (JSON)
  - connections (JSON)
  - settings (JSON)

-- Executions
executions
  - id
  - workflow_id
  - started_at
  - finished_at
  - status
  - data (JSON)

-- Credentials
credentials
  - id
  - name
  - type
  - data (encrypted)
```

**Backup**:
```bash
# Backup manual
docker exec n8n-postgres pg_dump -U n8n n8n > backup.sql

# Restore
docker exec -i n8n-postgres psql -U n8n n8n < backup.sql
```

### 3. Redis (Queue & Cache)

**Responsabilidades**:
- Fila de execução de workflows
- Cache de resultados (opcional)
- Pub/Sub para comunicação entre workers

**Uso**:
```javascript
// Exemplo de caching em workflow
{
  "parameters": {
    "operation": "set",
    "key": "query:{{ $json.query_hash }}",
    "value": "{{ $json.response }}",
    "ttl": 3600
  },
  "type": "n8n-nodes-base.redis"
}
```

### 4. Qdrant (Vector Database)

**Responsabilidades**:
- Armazenar embeddings de documentos
- Busca por similaridade vetorial
- Filtros por metadados

**Collections Schema**:
```json
{
  "name": "documents",
  "vectors": {
    "size": 1536,  // text-embedding-3-small
    "distance": "Cosine"
  },
  "payload_schema": {
    "text": "text",
    "source": "keyword",
    "timestamp": "datetime",
    "document_id": "keyword",
    "category": "keyword"
  }
}
```

**Operações**:
```python
# Criar collection
PUT /collections/documents
{
  "vectors": {
    "size": 1536,
    "distance": "Cosine"
  }
}

# Inserir ponto
PUT /collections/documents/points
{
  "points": [
    {
      "id": 1,
      "vector": [...],
      "payload": {
        "text": "...",
        "source": "..."
      }
    }
  ]
}

# Buscar
POST /collections/documents/points/search
{
  "vector": [...],
  "limit": 5,
  "with_payload": true
}
```

**Otimizações**:
- Index: HNSW para busca rápida
- Quantization: Scalar para reduzir memória
- Sharding: Para grandes volumes

### 5. Ollama (Local LLM)

**Responsabilidades**:
- Executar modelos de linguagem localmente
- Alternativa à OpenAI API
- Privacidade de dados

**Modelos Recomendados**:
```bash
# Instalar modelos
docker exec n8n-ollama ollama pull llama3.2
docker exec n8n-ollama ollama pull mistral
docker exec n8n-ollama ollama pull phi3

# Listar modelos
docker exec n8n-ollama ollama list
```

**Uso no n8n**:
```json
{
  "parameters": {
    "model": "llama3.2",
    "baseUrl": "http://ollama:11434",
    "prompt": "={{ $json.prompt }}"
  },
  "type": "@n8n/n8n-nodes-langchain.lmOllama"
}
```

**Comparação com OpenAI**:
| Aspecto | Ollama | OpenAI |
|---------|--------|--------|
| Custo | Gratuito | Pago por token |
| Velocidade | Depende do hardware | Rápido |
| Qualidade | Boa (modelos menores) | Excelente |
| Privacidade | Total | Enviado para OpenAI |
| Escalabilidade | Limitada | Ilimitada |

## Fluxos de Dados

### Fluxo 1: Ingestão de Documento

```
┌─────────┐
│ Cliente │
└────┬────┘
     │ POST /ingest-document
     │ { text, source, document_id }
     ▼
┌─────────────────┐
│ n8n Webhook     │
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ Document Loader │  Adiciona metadados
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ Text Splitter   │  Divide em chunks
└────┬────────────┘  (1000 chars, overlap 200)
     │
     ▼
┌─────────────────┐
│ OpenAI          │  Cria embeddings
│ Embeddings      │  (1536 dimensões)
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ Qdrant          │  Armazena vetores
│ Vector Store    │  + metadados
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ Response        │  { success, chunks_count }
└─────────────────┘
```

**Tempos estimados**:
- Documento 1000 palavras: ~2-5 segundos
- Criação de embeddings: ~1 segundo
- Armazenamento no Qdrant: ~0.5 segundos

### Fluxo 2: Query RAG

```
┌─────────┐
│ Cliente │
└────┬────┘
     │ POST /query
     │ { query, top_k }
     ▼
┌─────────────────┐
│ n8n Webhook     │
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ Extract Params  │  query, top_k
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ OpenAI          │  Embedding da query
│ Embeddings      │  (1536 dimensões)
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ Qdrant Search   │  Busca top_k similares
└────┬────────────┘  (cosine similarity)
     │
     ▼
┌─────────────────┐
│ Aggregate       │  Concatena contextos
│ Context         │
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ Build Prompt    │  Template + contexto
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ OpenAI Chat     │  Gera resposta
└────┬────────────┘  (GPT-4o-mini)
     │
     ▼
┌─────────────────┐
│ Response        │  { query, answer, sources }
└─────────────────┘
```

**Tempos estimados**:
- Embedding da query: ~0.5 segundos
- Busca vetorial: ~0.1-0.5 segundos
- Geração da resposta: ~2-5 segundos
- **Total**: ~3-6 segundos

### Fluxo 3: Batch Processing

```
┌─────────────────┐
│ Cron Schedule   │  Diariamente 2h AM
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ Read Files      │  Lê diretório /data
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ Convert Binary  │  Texto dos arquivos
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ Split Batches   │  Lotes de 10
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ Process Each    │  Loop sobre lotes
│ Document        │
└────┬────────────┘
     │
     ├─► Document Loader
     ├─► Text Splitter
     ├─► Embeddings
     └─► Vector Store
     │
     ▼
┌─────────────────┐
│ Summary Report  │  Total processado
└─────────────────┘
```

**Escalabilidade**:
- Processa 10 documentos por vez
- Pode ser ajustado via `batchSize`
- Evita sobrecarga de memória

## Decisões de Design

### 1. Por que n8n?

**Vantagens**:
- Interface visual (low-code)
- Self-hosted (controle total)
- Extensível (custom nodes)
- Comunidade ativa
- Integração nativa com LangChain

**Alternativas consideradas**:
- Airflow: Mais complexo, focado em data engineering
- Zapier: SaaS, menos flexível
- Custom Python: Mais trabalho de desenvolvimento

### 2. Por que Qdrant?

**Vantagens**:
- Performance excelente
- Filtros por metadados
- API simples
- Docker-friendly
- Suporte a Python/JavaScript

**Alternativas**:
- Pinecone: SaaS, mais caro
- Weaviate: Mais features, mais complexo
- Chroma: Menos maduro
- FAISS: Sem filtros por metadados

### 3. Por que PostgreSQL?

**Vantagens**:
- Requerimento do n8n
- Confiável e maduro
- Ótimo para auditoria
- Suporte a JSON

**Alternativas**:
- SQLite: Não recomendado para produção
- MySQL: Menos features JSON

### 4. Chunking Strategy

**Configuração atual**:
```json
{
  "chunkSize": 1000,
  "chunkOverlap": 200
}
```

**Rationale**:
- 1000 chars ≈ 250 tokens (balanceado)
- Overlap de 200 mantém contexto entre chunks
- Funciona bem com GPT-4o-mini (128k context)

**Ajustes por tipo de documento**:
```javascript
// Código
{ chunkSize: 500, chunkOverlap: 50 }

// Artigos
{ chunkSize: 1000, chunkOverlap: 200 }

// Livros
{ chunkSize: 1500, chunkOverlap: 300 }

// Chat messages
{ chunkSize: 300, chunkOverlap: 0 }
```

### 5. Embedding Model

**Escolhido**: `text-embedding-3-small`

**Rationale**:
- Custo: $0.02 / 1M tokens (barato)
- Performance: Boa qualidade
- Dimensões: 1536 (balanceado)
- Velocidade: Rápido

**Comparação**:
| Modelo | Dimensões | Custo/1M tokens | Use case |
|--------|-----------|----------------|----------|
| ada-002 | 1536 | $0.10 | Legacy |
| 3-small | 1536 | $0.02 | Geral |
| 3-large | 3072 | $0.13 | Alta precisão |

## Segurança

### 1. Autenticação

**n8n**:
```yaml
N8N_BASIC_AUTH_ACTIVE: true
N8N_BASIC_AUTH_USER: ${USER}
N8N_BASIC_AUTH_PASSWORD: ${PASSWORD}
```

**Recomendações**:
- Usar senhas fortes (min 16 chars)
- Considerar OAuth2 para produção
- Ativar 2FA se disponível

### 2. Network Isolation

```yaml
networks:
  n8n-network:
    driver: bridge
    internal: false  # Mudar para true em prod
```

**Produção**:
- Isolar network internamente
- Usar reverse proxy (nginx)
- Configurar firewall

### 3. Secrets Management

**Nunca comitar**:
- `.env` (use `.env.example`)
- Credenciais do n8n
- API keys

**Usar**:
- Docker secrets
- Vault (HashiCorp)
- AWS Secrets Manager

### 4. Rate Limiting

Implementar no nginx:
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /webhook/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://n8n:5678;
}
```

## Monitoramento

### 1. Logs

```bash
# n8n logs
docker-compose logs -f n8n

# Todos os serviços
docker-compose logs -f

# Logs específicos
docker-compose logs -f qdrant
```

### 2. Métricas

**n8n**:
- Execuções totais
- Execuções com erro
- Tempo médio de execução

**Qdrant**:
```bash
# Status da collection
curl http://localhost:6333/collections/documents

# Contagem de pontos
curl http://localhost:6333/collections/documents/points/count
```

### 3. Health Checks

```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:5678/healthz || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### 4. Alertas

Configurar no n8n:
- Email on workflow error
- Slack notifications
- PagerDuty integration

## Performance

### 1. Benchmarks

**Ingestão**:
- 1 documento (1000 palavras): ~3s
- 10 documentos: ~25s
- 100 documentos: ~4min (batch)

**Query**:
- Query simples: ~3-5s
- Query com reranking: ~6-8s
- Query cached: ~0.5s

### 2. Otimizações

**Qdrant**:
```python
# Configurar HNSW
{
  "hnsw_config": {
    "m": 16,
    "ef_construct": 100
  }
}
```

**Batch size**:
```javascript
// Ajustar baseado em memória
batchSize = Math.floor(availableMemoryMB / documentSizeMB)
```

**Caching**:
```javascript
// Cache de embeddings
const cacheKey = `emb:${hash(text)}`;
const cached = await redis.get(cacheKey);
if (cached) return cached;
```

### 3. Scaling

**Horizontal**:
```yaml
n8n-worker-1:
  image: n8nio/n8n
  environment:
    - EXECUTIONS_MODE=queue
    - ...

n8n-worker-2:
  image: n8nio/n8n
  environment:
    - EXECUTIONS_MODE=queue
    - ...
```

**Vertical**:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

## Backup & Recovery

### 1. n8n Workflows

```bash
# Exportar todos workflows
curl -u admin:password \
  http://localhost:5678/api/v1/workflows \
  > workflows-backup.json

# Importar
curl -u admin:password \
  -X POST \
  -H "Content-Type: application/json" \
  -d @workflows-backup.json \
  http://localhost:5678/api/v1/workflows
```

### 2. PostgreSQL

```bash
# Backup automático diário
0 3 * * * docker exec n8n-postgres pg_dump -U n8n n8n | gzip > /backups/n8n-$(date +\%Y\%m\%d).sql.gz

# Retention (manter 30 dias)
find /backups -name "n8n-*.sql.gz" -mtime +30 -delete
```

### 3. Qdrant

```bash
# Snapshot
curl -X POST http://localhost:6333/collections/documents/snapshots

# Download snapshot
curl -O http://localhost:6333/collections/documents/snapshots/{snapshot-name}

# Restore
curl -X PUT \
  -H "Content-Type: multipart/form-data" \
  -F "snapshot=@snapshot.snapshot" \
  http://localhost:6333/collections/documents/snapshots/upload
```

## Roadmap

### Fase 1: MVP (Atual)
- [x] Setup básico
- [x] Workflows de ingestão
- [x] Workflows de query
- [x] Documentação

### Fase 2: Melhorias
- [ ] Interface web
- [ ] Reranking
- [ ] Cache avançado
- [ ] Multi-modal (imagens)

### Fase 3: Produção
- [ ] Autenticação avançada
- [ ] Monitoramento (Grafana)
- [ ] CI/CD
- [ ] Testes automatizados

### Fase 4: Escala
- [ ] Kubernetes deployment
- [ ] Multi-tenancy
- [ ] Rate limiting avançado
- [ ] Analytics dashboard

---

Documento mantido por: Time de Desenvolvimento
Última atualização: 2025-01-23
