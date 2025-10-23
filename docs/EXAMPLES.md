# Exemplos Práticos

Exemplos completos de como usar o sistema Agentic RAG.

## Exemplo 1: Sistema de Suporte Automático

### Objetivo
Responder automaticamente perguntas de clientes usando uma base de conhecimento.

### Passo 1: Adicionar documentos à base

```python
import requests

# Upload manual do produto
with open('manual-produto.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/documents/upload',
        files={'file': f},
        data={'knowledge_base_id': 'suporte'}
    )
print(f"Documento indexado: {response.json()}")

# Adicionar FAQs
faqs = """
Q: Como resetar minha senha?
A: Clique em "Esqueci minha senha" na tela de login.

Q: Qual o prazo de entrega?
A: Entregamos em até 7 dias úteis.

Q: Como cancelar meu pedido?
A: Acesse "Meus Pedidos" e clique em "Cancelar".
"""

response = requests.post(
    'http://localhost:8000/api/documents/add-text',
    json={
        'content': faqs,
        'knowledge_base_id': 'suporte',
        'metadata': {'type': 'faq', 'version': '1.0'}
    }
)
print(f"FAQs indexadas: {response.json()}")
```

### Passo 2: Criar workflow n8n

**Workflow: Email Support Bot**

```json
{
  "name": "Email Support Bot",
  "nodes": [
    {
      "type": "n8n-nodes-base.emailReadImap",
      "name": "Monitor Emails",
      "parameters": {
        "mailbox": "INBOX",
        "options": {
          "allowUnauthorizedCerts": true
        }
      }
    },
    {
      "type": "n8n-nodes-base.function",
      "name": "Extract Question",
      "parameters": {
        "functionCode": "return items.map(item => ({json: {query: item.json.subject + '\\n' + item.json.textPlain, from: item.json.from}}));"
      }
    },
    {
      "type": "n8n-nodes-claude-rag.claudeRag",
      "name": "Query Support KB",
      "parameters": {
        "resource": "ragQuery",
        "operation": "query",
        "prompt": "={{$json.query}}",
        "ragEndpoint": "http://rag-api:8000",
        "knowledgeBaseId": "suporte",
        "model": "claude-3-5-sonnet-20241022",
        "systemPrompt": "Você é um assistente de suporte. Seja educado e profissional."
      }
    },
    {
      "type": "n8n-nodes-base.emailSend",
      "name": "Send Reply",
      "parameters": {
        "toEmail": "={{$json.from}}",
        "subject": "Re: ={{$json.query}}",
        "text": "={{$json.response}}"
      }
    }
  ]
}
```

### Passo 3: Testar o sistema

```python
# Simular uma consulta
response = requests.post(
    'http://localhost:8000/api/rag/query',
    json={
        'query': 'Como faço para resetar minha senha?',
        'knowledge_base_id': 'suporte',
        'temperature': 0.3  # Mais determinístico para suporte
    }
)

print("Resposta:", response.json()['answer'])
print("\nFontes usadas:")
for source in response.json()['sources']:
    print(f"- {source['metadata']['source']}")
```

---

## Exemplo 2: Análise de Documentos Financeiros

### Objetivo
Processar relatórios financeiros e responder perguntas sobre eles.

### Passo 1: Upload de relatórios

```python
import os
import requests

# Upload de múltiplos relatórios
reports_dir = './relatorios-financeiros/'
files = []

for filename in os.listdir(reports_dir):
    if filename.endswith('.pdf'):
        with open(os.path.join(reports_dir, filename), 'rb') as f:
            files.append(('files', f))

response = requests.post(
    'http://localhost:8000/api/documents/batch-upload',
    files=files,
    data={'knowledge_base_id': 'financeiro'}
)

print(f"Uploaded {response.json()['total_uploaded']} relatórios")
```

### Passo 2: Criar agent para análise

```python
# Agent que pode fazer cálculos e análises
task = """
Analise os relatórios financeiros e:
1. Calcule a receita total do último trimestre
2. Identifique as 3 maiores despesas
3. Calcule a margem de lucro
4. Gere um resumo executivo
"""

response = requests.post(
    'http://localhost:8000/api/agent/execute',
    json={
        'task': task,
        'knowledge_base_id': 'financeiro',
        'tools': ['search_knowledge_base', 'python_repl'],
        'max_iterations': 10
    }
)

result = response.json()
print("Resultado da análise:")
print(result['result'])

print("\nPassos executados:")
for step in result['steps']:
    print(f"\nIteração {step['iteration']}:")
    print(f"Pensamento: {step['thought']}")
    for tool_use in step['tool_uses']:
        print(f"  - Usou {tool_use['tool']}")
```

### Passo 3: Workflow agendado para relatórios

**Workflow: Daily Financial Report**

```json
{
  "name": "Daily Financial Report",
  "nodes": [
    {
      "type": "n8n-nodes-base.scheduleTrigger",
      "name": "Every Day 8AM",
      "parameters": {
        "rule": {
          "interval": [{"field": "hours", "hoursInterval": 24}]
        }
      }
    },
    {
      "type": "n8n-nodes-claude-rag.claudeRag",
      "name": "Generate Report",
      "parameters": {
        "resource": "agentTask",
        "operation": "execute",
        "prompt": "Analise os dados financeiros de ontem e gere um relatório resumido",
        "ragEndpoint": "http://rag-api:8000"
      }
    },
    {
      "type": "n8n-nodes-base.emailSend",
      "name": "Email to Management",
      "parameters": {
        "toEmail": "management@company.com",
        "subject": "Relatório Financeiro Diário",
        "text": "={{$json.result}}"
      }
    }
  ]
}
```

---

## Exemplo 3: Documentação Técnica Interativa

### Objetivo
Criar um sistema de busca inteligente para documentação técnica.

### Passo 1: Indexar documentação

```bash
# Script para crawlear e indexar docs
cat > index_docs.py << 'EOF'
import requests
import os
from pathlib import Path

def index_directory(directory, kb_id='technical-docs'):
    """Indexa todos os arquivos de um diretório"""
    for filepath in Path(directory).rglob('*.md'):
        with open(filepath, 'r') as f:
            content = f.read()

        # Adiciona metadados úteis
        metadata = {
            'filename': filepath.name,
            'path': str(filepath),
            'category': filepath.parent.name,
            'last_modified': os.path.getmtime(filepath)
        }

        response = requests.post(
            'http://localhost:8000/api/documents/add-text',
            json={
                'content': content,
                'knowledge_base_id': kb_id,
                'metadata': metadata
            }
        )

        print(f"✓ Indexed: {filepath.name}")

# Uso
index_directory('./docs/', 'technical-docs')
EOF

python index_docs.py
```

### Passo 2: API de busca com exemplos de código

```python
def search_docs(query, include_code_examples=True):
    """Busca na documentação e inclui exemplos de código"""

    response = requests.post(
        'http://localhost:8000/api/rag/query',
        json={
            'query': query,
            'knowledge_base_id': 'technical-docs',
            'system_prompt': '''Você é um assistente de documentação técnica.
            Sempre inclua exemplos de código quando relevante.
            Cite as seções da documentação usadas.'''
        }
    )

    result = response.json()

    return {
        'answer': result['answer'],
        'references': [
            {
                'file': s['metadata']['filename'],
                'relevance': s['score']
            }
            for s in result['sources']
        ]
    }

# Teste
result = search_docs("Como configurar autenticação JWT?")
print(result['answer'])
print("\nReferências:")
for ref in result['references']:
    print(f"- {ref['file']} (relevância: {ref['relevance']:.2f})")
```

### Passo 3: Webhook para Slack

**Workflow: Slack Doc Bot**

```json
{
  "name": "Slack Documentation Bot",
  "nodes": [
    {
      "type": "n8n-nodes-base.slackTrigger",
      "name": "When Message Starts with /docs",
      "parameters": {
        "slashCommand": "/docs"
      }
    },
    {
      "type": "n8n-nodes-claude-rag.claudeRag",
      "name": "Search Docs",
      "parameters": {
        "resource": "ragQuery",
        "operation": "query",
        "prompt": "={{$json.text}}",
        "knowledgeBaseId": "technical-docs"
      }
    },
    {
      "type": "n8n-nodes-base.slack",
      "name": "Reply in Thread",
      "parameters": {
        "channel": "={{$json.channel}}",
        "text": "={{$json.response}}",
        "threadTs": "={{$json.ts}}"
      }
    }
  ]
}
```

---

## Exemplo 4: Sistema de Monitoramento Inteligente

### Objetivo
Monitorar logs e tomar ações automáticas quando necessário.

### Passo 1: Indexar logs históricos

```python
import requests
from datetime import datetime, timedelta

def index_logs(log_file):
    """Indexa arquivo de logs com contexto temporal"""
    with open(log_file, 'r') as f:
        logs = f.readlines()

    # Agrupa logs em blocos de 100 linhas
    chunk_size = 100
    for i in range(0, len(logs), chunk_size):
        chunk = ''.join(logs[i:i+chunk_size])

        metadata = {
            'type': 'log',
            'chunk_index': i // chunk_size,
            'timestamp': datetime.now().isoformat()
        }

        requests.post(
            'http://localhost:8000/api/documents/add-text',
            json={
                'content': chunk,
                'knowledge_base_id': 'system-logs',
                'metadata': metadata
            }
        )

    print(f"✓ Indexed {len(logs)} log lines")

index_logs('/var/log/application.log')
```

### Passo 2: Agent de análise de logs

```python
def analyze_errors():
    """Agent analisa logs e toma ações"""
    task = """
    Analise os logs do sistema das últimas 24 horas e:
    1. Identifique todos os erros e warnings
    2. Classifique por severidade
    3. Identifique padrões ou erros recorrentes
    4. Se houver erros críticos, calcule estatísticas
    5. Sugira ações para resolver os problemas
    """

    response = requests.post(
        'http://localhost:8000/api/agent/execute',
        json={
            'task': task,
            'knowledge_base_id': 'system-logs',
            'tools': ['search_knowledge_base', 'python_repl'],
            'max_iterations': 8
        }
    )

    return response.json()

result = analyze_errors()
print(result['result'])

# Se encontrou problemas críticos, notificar
if 'CRITICAL' in result['result']:
    # Enviar alerta...
    pass
```

### Passo 3: Workflow de monitoramento contínuo

**Workflow: Continuous Log Monitoring**

```json
{
  "name": "Continuous Log Monitoring",
  "nodes": [
    {
      "type": "n8n-nodes-base.scheduleTrigger",
      "name": "Every 15 Minutes",
      "parameters": {
        "rule": {
          "interval": [{"field": "minutes", "minutesInterval": 15}]
        }
      }
    },
    {
      "type": "n8n-nodes-base.executeCommand",
      "name": "Get Recent Logs",
      "parameters": {
        "command": "tail -n 1000 /var/log/app.log"
      }
    },
    {
      "type": "n8n-nodes-claude-rag.claudeRag",
      "name": "Analyze Logs",
      "parameters": {
        "resource": "agentTask",
        "operation": "execute",
        "prompt": "Analise estes logs: {{$json.stdout}}. Há algum problema crítico?"
      }
    },
    {
      "type": "n8n-nodes-base.if",
      "name": "Critical Issue?",
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{$json.result}}",
              "operation": "contains",
              "value2": "CRITICAL"
            }
          ]
        }
      }
    },
    {
      "type": "n8n-nodes-base.slack",
      "name": "Alert Team",
      "parameters": {
        "channel": "#alerts",
        "text": "🚨 Critical Issue Detected:\\n\\n={{$json.result}}"
      }
    }
  ]
}
```

---

## Exemplo 5: Pesquisa e Sumários Automáticos

### Objetivo
Monitorar fontes de informação e gerar sumários periódicos.

### Passo 1: Coletar conteúdo

```python
def fetch_and_index_articles(urls, kb_id='research'):
    """Fetches articles and indexes them"""
    import requests
    from bs4 import BeautifulSoup

    for url in urls:
        # Fetch content
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract main content
        content = soup.get_text()

        # Index
        requests.post(
            'http://localhost:8000/api/documents/add-text',
            json={
                'content': content,
                'knowledge_base_id': kb_id,
                'metadata': {
                    'url': url,
                    'fetched_at': datetime.now().isoformat()
                }
            }
        )

        print(f"✓ Indexed: {url}")

# Monitorar blog posts
urls = [
    'https://blog.example.com/post1',
    'https://blog.example.com/post2',
]
fetch_and_index_articles(urls)
```

### Passo 2: Gerar sumários temáticos

```python
def generate_weekly_summary(topic):
    """Gera sumário semanal sobre um tópico"""
    task = f"""
    Analise todo o conteúdo indexado sobre '{topic}' da última semana.

    Gere um sumário que inclua:
    1. Principais desenvolvimentos e notícias
    2. Tendências identificadas
    3. Insights e análises
    4. Links para os artigos mais relevantes

    Formate como um newsletter profissional.
    """

    response = requests.post(
        'http://localhost:8000/api/agent/execute',
        json={
            'task': task,
            'knowledge_base_id': 'research',
            'model': 'claude-3-5-sonnet-20241022',
            'max_iterations': 5
        }
    )

    return response.json()['result']

summary = generate_weekly_summary('inteligência artificial')
print(summary)
```

### Passo 3: Workflow de newsletter automático

**Workflow: Weekly Newsletter Generator**

```json
{
  "name": "Weekly AI Newsletter",
  "nodes": [
    {
      "type": "n8n-nodes-base.scheduleTrigger",
      "name": "Every Monday 9AM"
    },
    {
      "type": "n8n-nodes-base.httpRequest",
      "name": "Fetch RSS Feeds",
      "parameters": {
        "url": "https://feeds.example.com/ai",
        "responseFormat": "json"
      }
    },
    {
      "type": "n8n-nodes-base.function",
      "name": "Index New Articles",
      "parameters": {
        "functionCode": "// Code to index articles"
      }
    },
    {
      "type": "n8n-nodes-claude-rag.claudeRag",
      "name": "Generate Newsletter",
      "parameters": {
        "resource": "agentTask",
        "operation": "execute",
        "prompt": "Gere newsletter semanal sobre IA"
      }
    },
    {
      "type": "n8n-nodes-base.sendgrid",
      "name": "Send Newsletter",
      "parameters": {
        "to": "subscribers@example.com",
        "subject": "Newsletter Semanal de IA",
        "html": "={{$json.result}}"
      }
    }
  ]
}
```

---

## Dicas e Boas Práticas

### 1. Chunking de Documentos

```python
# Use chunks menores para precisão, maiores para contexto
# Default: 1000 caracteres com overlap de 200

# Para documentos técnicos (mais precisão):
chunk_size = 500
chunk_overlap = 100

# Para narrativas (mais contexto):
chunk_size = 2000
chunk_overlap = 400
```

### 2. Otimizando Queries

```python
# Use temperature baixa para respostas precisas
temperature = 0.3  # Suporte, FAQ

# Use temperature alta para criatividade
temperature = 0.9  # Geração de conteúdo, brainstorming
```

### 3. Metadados Úteis

```python
metadata = {
    'source': 'manual-v2.pdf',
    'section': 'troubleshooting',
    'version': '2.0',
    'language': 'pt-BR',
    'author': 'team',
    'last_updated': '2024-01-15',
    'tags': ['setup', 'installation']
}
```

### 4. Filtros em Queries

```python
# Buscar apenas em documentos específicos
response = requests.post(
    'http://localhost:8000/api/rag/search',
    json={
        'query': 'instalação',
        'filter': {
            'version': '2.0',
            'section': 'setup'
        }
    }
)
```

---

## Mais Exemplos

Veja os workflows de exemplo em `/workflows/` para mais casos de uso.
