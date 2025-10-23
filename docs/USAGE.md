# Guia de Uso - Como Trabalhar com n8n e Claude Code

Este guia mostra **todas as formas** de trabalhar com n8n usando Claude Code.

## 1. Desenvolvendo Nós Customizados do n8n

### Estrutura de um Nó

Um nó do n8n tem três partes principais:

```typescript
// n8n-nodes/nodes/MeuNo/MeuNo.node.ts
import { INodeType, INodeTypeDescription, IExecuteFunctions } from 'n8n-workflow';

export class MeuNo implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Meu Nó',
    name: 'meuNo',
    group: ['transform'],
    version: 1,
    description: 'Descrição do que o nó faz',
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      // Parâmetros que aparecem na UI
    ]
  };

  async execute(this: IExecuteFunctions) {
    // Lógica de execução
  }
}
```

### Editando Nós com Claude Code

**Exemplo: Adicionar novo parâmetro**

```bash
# Abra o arquivo no Claude Code
"Edite o nó ClaudeRAG em n8n-nodes/nodes/ClaudeRAG/ClaudeRAG.node.ts
e adicione um parâmetro para controlar o número máximo de tokens"
```

Claude Code vai:
1. Ler o arquivo
2. Adicionar o parâmetro na seção `properties`
3. Usar o parâmetro na função `execute`
4. Fazer commit das mudanças

**Exemplo: Adicionar nova operação**

```bash
"Adicione uma operação 'summarize' ao nó ClaudeRAG que resume documentos"
```

### Build e Deploy

```bash
cd n8n-nodes
npm run build
docker-compose restart n8n
```

## 2. Editando Workflows em JSON

Os workflows do n8n são arquivos JSON que você pode editar diretamente.

### Estrutura de um Workflow

```json
{
  "name": "Meu Workflow",
  "nodes": [
    {
      "parameters": {},
      "id": "node-id",
      "name": "Nome do Nó",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300]
    }
  ],
  "connections": {
    "Node1": {
      "main": [[{ "node": "Node2", "type": "main", "index": 0 }]]
    }
  }
}
```

### Editando com Claude Code

**Exemplo: Adicionar novo nó ao workflow**

```bash
"Edite o workflow em workflows/claude-rag-workflow.json e adicione
um nó HTTP Request que chama uma API externa antes do Claude RAG"
```

**Exemplo: Criar novo workflow**

```bash
"Crie um novo workflow que:
1. Monitora uma pasta
2. Quando detecta novo arquivo PDF
3. Envia para a API RAG para processar
4. Notifica via email quando completo"
```

### Importar Workflow Editado

1. Salve o arquivo JSON
2. No n8n, clique em "Import workflow"
3. Selecione o arquivo
4. Workflow estará disponível

## 3. Desenvolvendo API Backend

### Criar Novo Endpoint

**Exemplo: Endpoint de sumário**

```bash
"Crie um novo endpoint POST /api/summarize que:
- Recebe um documento
- Resume usando Claude
- Retorna o sumário e estatísticas"
```

Claude Code vai:
1. Criar o schema em `models/schemas.py`
2. Criar a rota em `routes/`
3. Implementar o serviço em `services/`
4. Atualizar a documentação

### Adicionar Nova Ferramenta para o Agente

```bash
"Adicione uma ferramenta 'send_email' ao AgentService que pode
enviar emails usando SMTP"
```

### Testar API

```bash
# Com curl
curl -X POST "http://localhost:8000/api/seu-endpoint" \
  -H "Content-Type: application/json" \
  -d '{"param": "value"}'

# Com Python
import requests
response = requests.post(
    "http://localhost:8000/api/seu-endpoint",
    json={"param": "value"}
)
```

## 4. Criando Workflows Completos

### Workflow 1: Sistema de Q&A Automático

**Objetivo**: Responder perguntas via email usando RAG

```bash
"Crie um workflow n8n que:
1. Monitora emails recebidos (IMAP)
2. Extrai a pergunta do corpo do email
3. Consulta a base de conhecimento via Claude RAG
4. Envia resposta por email
5. Registra a interação em planilha Google"
```

### Workflow 2: Processamento de Documentos

**Objetivo**: Processar documentos automaticamente

```bash
"Crie um workflow que:
1. Webhook recebe notificação de novo documento no Dropbox
2. Baixa o documento
3. Envia para API RAG para indexação
4. Extrai metadados com Claude
5. Atualiza database PostgreSQL
6. Notifica no Slack quando completo"
```

### Workflow 3: Agente Monitoring

**Objetivo**: Monitorar sistemas e agir automaticamente

```bash
"Crie um workflow que:
1. A cada 5 minutos verifica logs do sistema
2. Se encontrar erros, usa Agent para analisar
3. Agent decide se precisa tomar ação
4. Executa ação se necessário (restart, alerta, etc)
5. Gera relatório diário de incidentes"
```

## 5. Integrações Complexas

### Integração com Banco de Dados

**Workflow: RAG + PostgreSQL**

```bash
"Modifique a API para:
1. Antes de fazer query RAG, buscar dados relevantes no PostgreSQL
2. Combinar dados estruturados com documentos
3. Gerar resposta contextualizada
4. Salvar histórico de queries no banco"
```

### Integração com Cloud Storage

**Workflow: Auto-indexação de documentos**

```bash
"Crie sistema que:
1. Monitora bucket S3 para novos arquivos
2. Baixa e processa automaticamente
3. Indexa no vector store
4. Atualiza catálogo de documentos
5. Notifica usuários sobre novos conteúdos"
```

### Integração Multi-Agent

**Workflow: Sistema de agents especializados**

```bash
"Crie API com múltiplos agents:
1. Agent de triagem - decide qual agent usar
2. Agent de busca - especializado em RAG
3. Agent de análise - especializado em dados
4. Agent de execução - pode executar ações
5. Workflow n8n orquestra entre agents"
```

## 6. Padrões de Desenvolvimento

### Padrão 1: Webhook → Process → Store

```json
{
  "name": "Process and Store",
  "nodes": [
    {"type": "webhook", "name": "Receive Data"},
    {"type": "claudeRag", "name": "Process with Claude"},
    {"type": "postgres", "name": "Store Result"}
  ]
}
```

### Padrão 2: Schedule → Fetch → Agent → Action

```json
{
  "name": "Scheduled Agent Task",
  "nodes": [
    {"type": "schedule", "name": "Every Hour"},
    {"type": "http", "name": "Fetch Data"},
    {"type": "claudeRag", "name": "Agent Analysis", "operation": "agentTask"},
    {"type": "if", "name": "Action Needed?"},
    {"type": "slack", "name": "Notify"}
  ]
}
```

### Padrão 3: Event → RAG → Multi-channel Response

```json
{
  "name": "Multi-channel RAG Response",
  "nodes": [
    {"type": "webhook", "name": "Event Trigger"},
    {"type": "claudeRag", "name": "RAG Query"},
    {"type": "split", "name": "Split Response"},
    {"type": "slack", "name": "To Slack"},
    {"type": "email", "name": "To Email"},
    {"type": "http", "name": "To API"}
  ]
}
```

## 7. Debugging e Testes

### Debug de Nó Customizado

```typescript
// Adicione logs no código do nó
console.log('DEBUG: Parameter value:', this.getNodeParameter('param', 0));

// Verifique logs
docker logs agentic-rag-n8n -f
```

### Debug de Workflow

1. Ative workflow em modo de execução manual
2. Clique em "Execute Node" em cada nó
3. Veja os dados de entrada/saída
4. Ajuste parâmetros conforme necessário

### Debug de API

```python
# Adicione logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"Processing request: {request}")

# Verifique logs
docker logs agentic-rag-api -f
```

### Testes Automatizados

```bash
# Teste de API
cd api
pytest tests/

# Teste de nó n8n
cd n8n-nodes
npm test
```

## 8. Casos de Uso Reais

### Case 1: Suporte ao Cliente Automatizado

**Componentes**:
- Nó customizado: ClaudeRAG com histórico de conversas
- Workflow: Email → RAG → Resposta
- API: Endpoint de chat com memória

**Implementação**:
```bash
"Crie sistema de suporte que:
- Recebe tickets por email
- Consulta base de conhecimento + tickets anteriores
- Gera resposta personalizada
- Se não conseguir resolver, escala para humano
- Aprende com respostas aprovadas"
```

### Case 2: Análise de Documentos Legais

**Componentes**:
- Processamento de PDFs
- Extração de cláusulas
- Análise comparativa
- Geração de relatórios

**Implementação**:
```bash
"Crie pipeline de análise legal:
- Upload de contratos via webhook
- Extração de texto e metadados
- Análise de riscos com Claude
- Comparação com templates padrão
- Geração de relatório executivo"
```

### Case 3: Pesquisa e Sumários Automáticos

**Componentes**:
- Web scraping
- Indexação em tempo real
- Sumários periódicos
- Alertas inteligentes

**Implementação**:
```bash
"Crie sistema de research:
- Monitora fontes configuradas (RSS, APIs, websites)
- Indexa conteúdo novo automaticamente
- Gera sumários diários por tópico
- Envia alertas de conteúdos importantes
- Permite queries ad-hoc sobre todo conteúdo"
```

## 9. Performance e Otimização

### Cache de Embeddings

```python
# Use Redis para cache
from services.cache_service import CacheService

cache = CacheService()
embedding = await cache.get_or_compute_embedding(text)
```

### Batch Processing

```python
# Processe documentos em lote
documents = [doc1, doc2, doc3, ...]
await vectorstore.add_documents(documents)  # Batch insert
```

### Rate Limiting

```python
# Adicione rate limiting na API
from fastapi_limiter import FastAPILimiter

@app.post("/api/rag/query")
@limiter.limit("10/minute")
async def query_rag(request: Request):
    ...
```

## 10. Monitoramento

### Logs Estruturados

```python
import structlog

logger = structlog.get_logger()
logger.info("rag_query", query=query, kb=kb_id, latency=elapsed)
```

### Métricas

```python
from prometheus_client import Counter, Histogram

rag_queries = Counter('rag_queries_total', 'Total RAG queries')
query_latency = Histogram('rag_query_duration_seconds', 'RAG query latency')
```

### Alertas

Configure alertas no n8n para:
- Erros na API
- Queries lentas
- Vector store cheio
- Custos de API altos

## Próximos Passos

1. **Explore os exemplos**: Teste os workflows incluídos
2. **Customize**: Adapte para seu caso de uso
3. **Expanda**: Adicione novas integrações
4. **Compartilhe**: Documente seus workflows

## Recursos Adicionais

- [Documentação do n8n](https://docs.n8n.io)
- [Claude API Docs](https://docs.anthropic.com)
- [FastAPI Docs](https://fastapi.tiangolo.com)
