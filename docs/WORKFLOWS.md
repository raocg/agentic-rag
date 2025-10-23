# Guia Completo de Workflows n8n para RAG

Este documento fornece um guia detalhado sobre como criar, modificar e entender os workflows do n8n para sistemas RAG.

## Índice

1. [Introdução aos Workflows](#introdução-aos-workflows)
2. [Estrutura de um Workflow](#estrutura-de-um-workflow)
3. [Nodes Principais](#nodes-principais)
4. [Criando Novos Workflows](#criando-novos-workflows)
5. [Exemplos Práticos](#exemplos-práticos)
6. [Best Practices](#best-practices)

## Introdução aos Workflows

Um workflow no n8n é uma sequência de nodes (nós) conectados que processam dados. Para RAG, usamos workflows para:

- **Ingerir** documentos e criar embeddings
- **Buscar** informação relevante em bases vetoriais
- **Gerar** respostas usando LLMs
- **Processar** dados em lote

## Estrutura de um Workflow

Cada workflow consiste em:

### 1. Trigger Node (Gatilho)

Inicia o workflow. Pode ser:
- **Webhook**: Recebe requisições HTTP
- **Schedule**: Executa em horários programados
- **Manual**: Execução manual
- **Filesystem**: Monitora arquivos

### 2. Processing Nodes (Processamento)

Transformam e manipulam dados:
- **Set**: Define variáveis
- **Code**: Executa JavaScript/Python
- **Function**: Lógica customizada
- **HTTP Request**: Chama APIs externas

### 3. AI Nodes (Inteligência Artificial)

Específicos para IA:
- **OpenAI**: Chat, embeddings, completions
- **Document Loader**: Carrega e processa documentos
- **Text Splitter**: Divide texto em chunks
- **Vector Store**: Armazena e busca embeddings

### 4. Output Nodes (Saída)

Retornam resultados:
- **Respond to Webhook**: Retorna resposta HTTP
- **Send Email**: Envia e-mail
- **Database**: Salva em banco de dados

## Nodes Principais

### Webhook Node

```json
{
  "parameters": {
    "httpMethod": "POST",
    "path": "endpoint-name",
    "options": {}
  },
  "type": "n8n-nodes-base.webhook"
}
```

**Uso**: Receber dados externos via HTTP.

**Configurações importantes**:
- `httpMethod`: GET, POST, PUT, DELETE
- `path`: Caminho do endpoint
- `responseMode`: 'onReceived', 'lastNode'

### Document Loader

```json
{
  "parameters": {
    "operation": "text",
    "text": "={{ $json.body.text }}",
    "options": {
      "metadata": {
        "metadataValues": [
          {
            "name": "source",
            "value": "={{ $json.body.source }}"
          }
        ]
      }
    }
  },
  "type": "@n8n/n8n-nodes-langchain.documentDefaultDataLoader"
}
```

**Uso**: Carregar documentos com metadados.

**Metadados úteis**:
- `source`: Origem do documento
- `timestamp`: Data/hora de processamento
- `author`: Autor do documento
- `category`: Categoria/tag

### Text Splitter

```json
{
  "parameters": {
    "chunkSize": 1000,
    "chunkOverlap": 200
  },
  "type": "@n8n/n8n-nodes-langchain.textSplitterRecursiveCharacterTextSplitter"
}
```

**Uso**: Dividir texto em chunks.

**Parâmetros**:
- `chunkSize`: Tamanho máximo do chunk (recomendado: 500-2000)
- `chunkOverlap`: Overlap entre chunks (recomendado: 10-20% do chunkSize)

**Estratégias de chunking**:
1. **Pequenos (500)**: Melhor precisão, mais chunks
2. **Médios (1000)**: Balanceado
3. **Grandes (2000)**: Mais contexto, menos precisão

### OpenAI Embeddings

```json
{
  "parameters": {
    "model": "text-embedding-3-small",
    "options": {}
  },
  "type": "@n8n/n8n-nodes-langchain.embeddingsOpenAi"
}
```

**Modelos disponíveis**:
- `text-embedding-3-small`: Rápido, menor custo (1536 dimensões)
- `text-embedding-3-large`: Melhor qualidade (3072 dimensões)
- `text-embedding-ada-002`: Versão anterior (1536 dimensões)

### Qdrant Vector Store

```json
{
  "parameters": {
    "qdrantCollection": "documents",
    "options": {
      "qdrantUrl": "http://qdrant:6333"
    }
  },
  "type": "@n8n/n8n-nodes-langchain.vectorStoreQdrant"
}
```

**Operações**:
- **Insert**: Adicionar novos vetores
- **Search**: Buscar vetores similares
- **Update**: Atualizar vetores existentes
- **Delete**: Remover vetores

**Parâmetros de busca**:
- `topK`: Número de resultados (padrão: 5)
- `scoreThreshold`: Threshold de similaridade (0-1)

### OpenAI Chat

```json
{
  "parameters": {
    "model": "gpt-4o-mini",
    "options": {
      "temperature": 0.7,
      "maxTokens": 500
    },
    "prompt": "={{ $json.prompt }}"
  },
  "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi"
}
```

**Modelos**:
- `gpt-4o-mini`: Rápido, econômico
- `gpt-4o`: Mais capaz, mais caro
- `gpt-4-turbo`: Contexto maior

**Parâmetros**:
- `temperature`: 0 (determinístico) a 1 (criativo)
- `maxTokens`: Limite de tokens na resposta
- `topP`: Nucleus sampling (alternativa à temperature)

## Criando Novos Workflows

### Workflow 1: Ingestão de URLs

```javascript
// Estrutura
Webhook (POST /ingest-url)
  → HTTP Request (Fetch URL)
  → HTML Extract (Parse content)
  → Document Loader (Load text)
  → Text Splitter (Chunk)
  → Embeddings (Create vectors)
  → Vector Store (Save)
  → Respond
```

### Workflow 2: Conversational RAG

```javascript
// Estrutura
Webhook (POST /chat)
  → Extract conversation history
  → Build context with history
  → Create query embedding
  → Search vector store
  → Aggregate context
  → Build prompt with history + context
  → LLM (Generate response)
  → Save conversation
  → Respond
```

### Workflow 3: Multi-Modal RAG (Imagens + Texto)

```javascript
// Estrutura
Webhook (POST /ingest-multimodal)
  → Check content type
    → If image: Vision API → Extract description
    → If text: Direct processing
  → Document Loader
  → Text Splitter
  → Embeddings
  → Vector Store (with image metadata)
  → Respond
```

## Exemplos Práticos

### Exemplo 1: Adicionar Reranking

Melhorar a qualidade dos resultados com reranking:

```json
{
  "nodes": [
    // ... nodes anteriores ...
    {
      "parameters": {
        "model": "cohere-rerank",
        "query": "={{ $('Extract Query Parameters').item.json.query }}",
        "documents": "={{ $json.documents }}",
        "topN": 3
      },
      "name": "Rerank Results",
      "type": "n8n-nodes-cohere.rerank"
    }
    // ... nodes seguintes ...
  ]
}
```

### Exemplo 2: Adicionar Cache

Evitar consultas repetidas com cache:

```json
{
  "nodes": [
    {
      "parameters": {
        "operation": "get",
        "key": "={{ $json.query_hash }}"
      },
      "name": "Check Cache",
      "type": "n8n-nodes-base.redis"
    },
    {
      "parameters": {
        "conditions": {
          "boolean": [
            {
              "value1": "={{ $json.cached }}",
              "value2": true
            }
          ]
        }
      },
      "name": "Is Cached?",
      "type": "n8n-nodes-base.if"
    }
  ]
}
```

### Exemplo 3: Processar PDF

Workflow para extrair texto de PDFs:

```json
{
  "nodes": [
    {
      "parameters": {
        "binaryPropertyName": "data",
        "options": {}
      },
      "name": "PDF Extract",
      "type": "n8n-nodes-base.extractFromFile"
    },
    {
      "parameters": {
        "operation": "text",
        "text": "={{ $json.text }}",
        "options": {
          "metadata": {
            "metadataValues": [
              {
                "name": "filename",
                "value": "={{ $json.filename }}"
              },
              {
                "name": "pages",
                "value": "={{ $json.pages }}"
              }
            ]
          }
        }
      },
      "name": "Process PDF Text",
      "type": "@n8n/n8n-nodes-langchain.documentDefaultDataLoader"
    }
  ]
}
```

## Best Practices

### 1. Gestão de Erros

Sempre adicione error handling:

```json
{
  "parameters": {
    "options": {
      "continueOnFail": true
    }
  }
}
```

Use IF nodes para validação:

```json
{
  "parameters": {
    "conditions": {
      "boolean": [
        {
          "value1": "={{ $json.body.text !== undefined }}",
          "value2": true
        }
      ]
    }
  },
  "name": "Validate Input"
}
```

### 2. Logging

Adicione logs para debugging:

```json
{
  "parameters": {
    "assignments": {
      "assignments": [
        {
          "name": "log",
          "value": "=Processing document: {{ $json.document_id }}",
          "type": "string"
        }
      ]
    },
    "options": {
      "logOutput": true
    }
  },
  "name": "Log Activity"
}
```

### 3. Otimização de Performance

**Batch Processing**:
```json
{
  "parameters": {
    "batchSize": 10,
    "options": {}
  },
  "type": "n8n-nodes-base.splitInBatches"
}
```

**Parallel Execution**:
Configure `Mode` para `Parallel` em nodes que suportam.

**Caching**:
Use Redis para cachear resultados frequentes.

### 4. Versionamento

Mantenha versões dos workflows:
- Use tags descritivas (v1.0, v2.0)
- Documente mudanças
- Faça backup antes de alterações grandes

### 5. Segurança

**Validação de Input**:
```javascript
// Em Code node
if (!items[0].json.text || items[0].json.text.length > 10000) {
  throw new Error('Invalid input: text required and must be < 10000 chars');
}
return items;
```

**Sanitização**:
```javascript
// Remover caracteres perigosos
const sanitized = items[0].json.text
  .replace(/[<>]/g, '')
  .trim();
items[0].json.text = sanitized;
return items;
```

### 6. Monitoramento

Configure notificações de erro:
```json
{
  "parameters": {
    "toEmail": "admin@example.com",
    "subject": "Workflow Error: {{ $workflow.name }}",
    "text": "Error: {{ $json.error }}"
  },
  "name": "Send Error Alert",
  "type": "n8n-nodes-base.emailSend"
}
```

## Expressões Úteis

### Acessar dados anteriores
```javascript
// Node anterior
$json.field_name

// Node específico
$('Node Name').item.json.field_name

// Todos os items
$input.all()

// Primeiro item
$input.first()
```

### Manipulação de datas
```javascript
// Data atual ISO
$now.toISO()

// Data formatada
$now.format('yyyy-MM-dd')

// Adicionar dias
$now.plus({ days: 7 })
```

### String manipulation
```javascript
// Concatenar
={{ $json.first_name + ' ' + $json.last_name }}

// Uppercase
={{ $json.text.toUpperCase() }}

// Substring
={{ $json.text.substring(0, 100) }}

// Replace
={{ $json.text.replace('old', 'new') }}
```

### Arrays
```javascript
// Length
={{ $json.items.length }}

// Map
={{ $json.items.map(item => item.name) }}

// Filter
={{ $json.items.filter(item => item.active) }}

// Join
={{ $json.items.join(', ') }}
```

## Debugging

### 1. Ativar Debug Mode
No workflow, clique em Settings → Debug Mode

### 2. Ver dados entre nodes
Clique em cada node para ver input/output

### 3. Usar Execute Node
Teste nodes individualmente

### 4. Console logs
Em Code nodes:
```javascript
console.log('Debug:', items[0].json);
return items;
```

## Recursos Adicionais

- [n8n Expression Reference](https://docs.n8n.io/code/expressions/)
- [n8n Community Workflows](https://n8n.io/workflows)
- [LangChain n8n Integration](https://docs.n8n.io/integrations/langchain/)

---

Este guia será atualizado conforme novos workflows e patterns forem desenvolvidos.
