# API Reference

Documentação completa da API do sistema Agentic RAG.

## Base URL

```
http://localhost:8000
```

## Autenticação

Atualmente a API não requer autenticação. Em produção, adicione autenticação via API keys ou OAuth.

---

## Endpoints RAG

### POST /api/rag/query

Executa uma query RAG (Retrieval-Augmented Generation).

**Request Body:**
```json
{
  "query": "Sua pergunta aqui",
  "knowledge_base_id": "default",
  "top_k": 5,
  "include_sources": true,
  "model": "claude-3-5-sonnet-20241022",
  "temperature": 0.7
}
```

**Parameters:**
- `query` (string, required): A pergunta ou prompt
- `knowledge_base_id` (string, optional): ID da base de conhecimento. Default: "default"
- `top_k` (integer, optional): Número de documentos a recuperar (1-20). Default: 5
- `include_sources` (boolean, optional): Incluir documentos fonte na resposta. Default: true
- `model` (string, optional): Modelo Claude a usar. Default: "claude-3-5-sonnet-20241022"
- `temperature` (float, optional): Temperatura de geração (0-1). Default: 0.7

**Response:**
```json
{
  "answer": "Resposta gerada pelo Claude...",
  "sources": [
    {
      "content": "Conteúdo do documento...",
      "metadata": {
        "source": "documento.pdf",
        "chunk_index": 0
      },
      "score": 0.85
    }
  ],
  "usage": {
    "input_tokens": 150,
    "output_tokens": 300
  },
  "model": "claude-3-5-sonnet-20241022"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Como funciona o RAG?",
    "knowledge_base_id": "default",
    "top_k": 3
  }'
```

---

### POST /api/rag/search

Busca documentos sem geração de resposta.

**Request Body:**
```json
{
  "query": "termo de busca",
  "knowledge_base_id": "default",
  "top_k": 5,
  "filter": {
    "source": "specific-doc.pdf"
  }
}
```

**Response:**
```json
{
  "results": [
    {
      "content": "Conteúdo do documento...",
      "metadata": {
        "source": "doc.pdf"
      },
      "score": 0.92
    }
  ],
  "total": 5,
  "query": "termo de busca"
}
```

---

### GET /api/rag/knowledge-bases

Lista todas as bases de conhecimento disponíveis.

**Response:**
```json
{
  "knowledge_bases": ["default", "technical-docs", "customer-support"]
}
```

---

## Endpoints de Agent

### POST /api/agent/execute

Executa uma tarefa agêntica usando Claude com ferramentas.

**Request Body:**
```json
{
  "task": "Analise os últimos logs e resuma os erros",
  "model": "claude-3-5-sonnet-20241022",
  "max_iterations": 5,
  "knowledge_base_id": "default",
  "tools": ["search_knowledge_base", "python_repl"]
}
```

**Parameters:**
- `task` (string, required): Descrição da tarefa para o agent executar
- `model` (string, optional): Modelo Claude. Default: "claude-3-5-sonnet-20241022"
- `max_iterations` (integer, optional): Máximo de iterações (1-20). Default: 5
- `knowledge_base_id` (string, optional): Base de conhecimento para usar
- `tools` (array, optional): Lista de ferramentas disponíveis. Default: todas

**Response:**
```json
{
  "result": "Resultado da execução da tarefa...",
  "steps": [
    {
      "iteration": 1,
      "thought": "Vou buscar informações sobre...",
      "tool_uses": [
        {
          "tool": "search_knowledge_base",
          "input": {"query": "logs de erro"},
          "result": {"results": [...]}
        }
      ]
    }
  ],
  "usage": {
    "input_tokens": 500,
    "output_tokens": 800
  },
  "success": true
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/agent/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Calcule a média de vendas do último trimestre",
    "tools": ["python_repl"]
  }'
```

---

### GET /api/agent/tools

Lista todas as ferramentas disponíveis para o agent.

**Response:**
```json
{
  "tools": [
    {
      "name": "search_knowledge_base",
      "description": "Busca informações na base de conhecimento",
      "parameters": {
        "query": "string",
        "knowledge_base_id": "string",
        "top_k": "integer"
      }
    },
    {
      "name": "python_repl",
      "description": "Executa código Python",
      "parameters": {
        "code": "string"
      }
    }
  ]
}
```

---

### POST /api/agent/tools/{tool_name}/invoke

Invoca uma ferramenta diretamente (útil para testes).

**Path Parameters:**
- `tool_name` (string): Nome da ferramenta

**Request Body:**
```json
{
  "query": "machine learning",
  "top_k": 3
}
```

**Response:**
```json
{
  "tool": "search_knowledge_base",
  "result": {
    "results": [...]
  }
}
```

---

## Endpoints de Documentos

### POST /api/documents/upload

Faz upload de um arquivo para a base de conhecimento.

**Form Data:**
- `file` (file, required): Arquivo a fazer upload (txt, pdf, md, json, csv)
- `knowledge_base_id` (string, optional): ID da base. Default: "default"
- `metadata` (json string, optional): Metadados adicionais

**Response:**
```json
{
  "document_id": "uuid-123-456",
  "knowledge_base_id": "default",
  "chunks_created": 15,
  "status": "success"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@documento.pdf" \
  -F "knowledge_base_id=technical-docs" \
  -F 'metadata={"category":"manual","version":"2.0"}'
```

---

### POST /api/documents/add-text

Adiciona texto diretamente à base de conhecimento.

**Request Body:**
```json
{
  "content": "Conteúdo do documento em texto...",
  "knowledge_base_id": "default",
  "metadata": {
    "source": "manual-entry",
    "author": "John Doe"
  }
}
```

**Response:**
```json
{
  "document_id": "uuid-789",
  "knowledge_base_id": "default",
  "chunks_created": 3,
  "status": "success"
}
```

---

### POST /api/documents/batch-upload

Faz upload de múltiplos arquivos de uma vez.

**Form Data:**
- `files` (file[], required): Array de arquivos
- `knowledge_base_id` (string, optional): Base de conhecimento

**Response:**
```json
{
  "total_uploaded": 5,
  "results": [
    {
      "document_id": "uuid-1",
      "chunks_created": 10,
      "status": "success"
    },
    ...
  ]
}
```

---

### DELETE /api/documents/delete/{document_id}

Deleta um documento da base de conhecimento.

**Path Parameters:**
- `document_id` (string): ID do documento

**Query Parameters:**
- `knowledge_base_id` (string, optional): Base de conhecimento. Default: "default"

**Response:**
```json
{
  "status": "success",
  "message": "Document uuid-123 deleted"
}
```

---

### GET /api/documents/list

Lista documentos em uma base de conhecimento.

**Query Parameters:**
- `knowledge_base_id` (string, optional): Base a listar. Default: "default"
- `limit` (integer, optional): Máximo de resultados. Default: 100

**Response:**
```json
{
  "documents": [
    {
      "knowledge_base_id": "default",
      "document_count": 42
    }
  ],
  "total": 1
}
```

---

## Health & Status

### GET /health

Verifica a saúde dos serviços.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "vectorstore": true,
    "claude": true
  }
}
```

---

### GET /

Informações básicas da API.

**Response:**
```json
{
  "message": "Agentic RAG API",
  "version": "1.0.0",
  "endpoints": {
    "rag": "/api/rag",
    "agent": "/api/agent",
    "documents": "/api/documents",
    "docs": "/docs"
  }
}
```

---

## Códigos de Status HTTP

- `200 OK`: Requisição bem-sucedida
- `400 Bad Request`: Parâmetros inválidos
- `404 Not Found`: Recurso não encontrado
- `500 Internal Server Error`: Erro no servidor

---

## Rate Limits

Atualmente sem rate limits. Configure conforme necessário para produção.

---

## Modelos Claude Disponíveis

- `claude-3-5-sonnet-20241022` - Recomendado para a maioria dos casos
- `claude-3-5-haiku-20241022` - Rápido e econômico
- `claude-3-opus-20240229` - Maior capacidade

---

## Exemplos de Integração

### Python

```python
import requests

class AgenticRAGClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def query_rag(self, query, kb_id="default", top_k=5):
        response = requests.post(
            f"{self.base_url}/api/rag/query",
            json={
                "query": query,
                "knowledge_base_id": kb_id,
                "top_k": top_k
            }
        )
        return response.json()

    def execute_agent_task(self, task, tools=None):
        response = requests.post(
            f"{self.base_url}/api/agent/execute",
            json={
                "task": task,
                "tools": tools or []
            }
        )
        return response.json()

    def upload_document(self, file_path, kb_id="default"):
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/api/documents/upload",
                files={"file": f},
                data={"knowledge_base_id": kb_id}
            )
        return response.json()

# Uso
client = AgenticRAGClient()

# Upload documento
client.upload_document("manual.pdf", "technical-docs")

# Query RAG
result = client.query_rag("Como instalar o sistema?", "technical-docs")
print(result["answer"])

# Execute agent
task_result = client.execute_agent_task("Analise os logs e gere relatório")
print(task_result["result"])
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

class AgenticRAGClient {
  constructor(baseURL = 'http://localhost:8000') {
    this.client = axios.create({ baseURL });
  }

  async queryRAG(query, kbId = 'default', topK = 5) {
    const response = await this.client.post('/api/rag/query', {
      query,
      knowledge_base_id: kbId,
      top_k: topK
    });
    return response.data;
  }

  async executeAgentTask(task, tools = []) {
    const response = await this.client.post('/api/agent/execute', {
      task,
      tools
    });
    return response.data;
  }

  async uploadDocument(filePath, kbId = 'default') {
    const FormData = require('form-data');
    const fs = require('fs');

    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));
    form.append('knowledge_base_id', kbId);

    const response = await this.client.post('/api/documents/upload', form, {
      headers: form.getHeaders()
    });
    return response.data;
  }
}

// Uso
const client = new AgenticRAGClient();

(async () => {
  // Upload
  await client.uploadDocument('manual.pdf', 'technical-docs');

  // Query
  const result = await client.queryRAG('Como instalar?', 'technical-docs');
  console.log(result.answer);

  // Agent
  const taskResult = await client.executeAgentTask('Gere relatório');
  console.log(taskResult.result);
})();
```

---

## Documentação Interativa

Acesse a documentação interativa (Swagger UI) em:

```
http://localhost:8000/docs
```

Ou a documentação alternativa (ReDoc) em:

```
http://localhost:8000/redoc
```
