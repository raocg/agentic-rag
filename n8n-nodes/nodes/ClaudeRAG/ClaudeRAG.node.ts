import {
  IExecuteFunctions,
  INodeExecutionData,
  INodeType,
  INodeTypeDescription,
  NodeOperationError,
} from 'n8n-workflow';
import Anthropic from '@anthropic-ai/sdk';

export class ClaudeRAG implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Claude RAG',
    name: 'claudeRag',
    icon: 'file:claude.svg',
    group: ['transform'],
    version: 1,
    subtitle: '={{$parameter["operation"] + ": " + $parameter["resource"]}}',
    description: 'Interact with Claude AI with RAG capabilities',
    defaults: {
      name: 'Claude RAG',
    },
    inputs: ['main'],
    outputs: ['main'],
    credentials: [
      {
        name: 'claudeApi',
        required: true,
      },
    ],
    properties: [
      {
        displayName: 'Resource',
        name: 'resource',
        type: 'options',
        noDataExpression: true,
        options: [
          {
            name: 'Message',
            value: 'message',
          },
          {
            name: 'RAG Query',
            value: 'ragQuery',
          },
          {
            name: 'Agent Task',
            value: 'agentTask',
          },
        ],
        default: 'message',
      },
      {
        displayName: 'Operation',
        name: 'operation',
        type: 'options',
        noDataExpression: true,
        displayOptions: {
          show: {
            resource: ['message'],
          },
        },
        options: [
          {
            name: 'Send',
            value: 'send',
            description: 'Send a message to Claude',
            action: 'Send a message',
          },
        ],
        default: 'send',
      },
      {
        displayName: 'Operation',
        name: 'operation',
        type: 'options',
        noDataExpression: true,
        displayOptions: {
          show: {
            resource: ['ragQuery'],
          },
        },
        options: [
          {
            name: 'Query Knowledge Base',
            value: 'query',
            description: 'Query with RAG context',
            action: 'Query knowledge base',
          },
        ],
        default: 'query',
      },
      {
        displayName: 'Operation',
        name: 'operation',
        type: 'options',
        noDataExpression: true,
        displayOptions: {
          show: {
            resource: ['agentTask'],
          },
        },
        options: [
          {
            name: 'Execute',
            value: 'execute',
            description: 'Execute an agentic task',
            action: 'Execute agentic task',
          },
        ],
        default: 'execute',
      },
      {
        displayName: 'Model',
        name: 'model',
        type: 'options',
        options: [
          {
            name: 'Claude 3.5 Sonnet',
            value: 'claude-3-5-sonnet-20241022',
          },
          {
            name: 'Claude 3.5 Haiku',
            value: 'claude-3-5-haiku-20241022',
          },
          {
            name: 'Claude 3 Opus',
            value: 'claude-3-opus-20240229',
          },
        ],
        default: 'claude-3-5-sonnet-20241022',
        description: 'The model to use',
      },
      {
        displayName: 'Prompt',
        name: 'prompt',
        type: 'string',
        typeOptions: {
          rows: 4,
        },
        default: '',
        placeholder: 'Enter your prompt here...',
        description: 'The prompt to send to Claude',
      },
      {
        displayName: 'RAG API Endpoint',
        name: 'ragEndpoint',
        type: 'string',
        displayOptions: {
          show: {
            resource: ['ragQuery', 'agentTask'],
          },
        },
        default: 'http://localhost:8000',
        description: 'Your RAG API endpoint URL',
      },
      {
        displayName: 'Knowledge Base ID',
        name: 'knowledgeBaseId',
        type: 'string',
        displayOptions: {
          show: {
            resource: ['ragQuery'],
          },
        },
        default: '',
        description: 'ID of the knowledge base to query',
      },
      {
        displayName: 'Max Tokens',
        name: 'maxTokens',
        type: 'number',
        default: 1024,
        description: 'Maximum number of tokens to generate',
      },
      {
        displayName: 'Temperature',
        name: 'temperature',
        type: 'number',
        typeOptions: {
          minValue: 0,
          maxValue: 1,
          numberPrecision: 2,
        },
        default: 1,
        description: 'Sampling temperature between 0 and 1',
      },
      {
        displayName: 'System Prompt',
        name: 'systemPrompt',
        type: 'string',
        typeOptions: {
          rows: 2,
        },
        default: '',
        placeholder: 'Optional system prompt...',
        description: 'System prompt to set context',
      },
      {
        displayName: 'Additional Fields',
        name: 'additionalFields',
        type: 'collection',
        placeholder: 'Add Field',
        default: {},
        options: [
          {
            displayName: 'Top K',
            name: 'topK',
            type: 'number',
            default: 5,
            description: 'Number of documents to retrieve for RAG',
          },
          {
            displayName: 'Include Sources',
            name: 'includeSources',
            type: 'boolean',
            default: true,
            description: 'Whether to include source documents in response',
          },
          {
            displayName: 'Stream',
            name: 'stream',
            type: 'boolean',
            default: false,
            description: 'Whether to stream the response',
          },
        ],
      },
    ],
  };

  async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
    const items = this.getInputData();
    const returnData: INodeExecutionData[] = [];
    const resource = this.getNodeParameter('resource', 0) as string;
    const operation = this.getNodeParameter('operation', 0) as string;

    const credentials = await this.getCredentials('claudeApi');
    const anthropic = new Anthropic({
      apiKey: credentials.apiKey as string,
    });

    for (let i = 0; i < items.length; i++) {
      try {
        if (resource === 'message' && operation === 'send') {
          const prompt = this.getNodeParameter('prompt', i) as string;
          const model = this.getNodeParameter('model', i) as string;
          const maxTokens = this.getNodeParameter('maxTokens', i) as number;
          const temperature = this.getNodeParameter('temperature', i) as number;
          const systemPrompt = this.getNodeParameter('systemPrompt', i, '') as string;

          const response = await anthropic.messages.create({
            model,
            max_tokens: maxTokens,
            temperature,
            system: systemPrompt || undefined,
            messages: [{ role: 'user', content: prompt }],
          });

          returnData.push({
            json: {
              response: response.content[0].type === 'text' ? response.content[0].text : '',
              usage: response.usage,
              model: response.model,
              stopReason: response.stop_reason,
            },
            pairedItem: { item: i },
          });
        } else if (resource === 'ragQuery' && operation === 'query') {
          const prompt = this.getNodeParameter('prompt', i) as string;
          const ragEndpoint = this.getNodeParameter('ragEndpoint', i) as string;
          const knowledgeBaseId = this.getNodeParameter('knowledgeBaseId', i) as string;
          const additionalFields = this.getNodeParameter('additionalFields', i, {}) as any;

          const axios = require('axios');
          const ragResponse = await axios.post(`${ragEndpoint}/api/rag/query`, {
            query: prompt,
            knowledgeBaseId,
            topK: additionalFields.topK || 5,
            includeSources: additionalFields.includeSources !== false,
          });

          returnData.push({
            json: ragResponse.data,
            pairedItem: { item: i },
          });
        } else if (resource === 'agentTask' && operation === 'execute') {
          const prompt = this.getNodeParameter('prompt', i) as string;
          const ragEndpoint = this.getNodeParameter('ragEndpoint', i) as string;
          const model = this.getNodeParameter('model', i) as string;

          const axios = require('axios');
          const agentResponse = await axios.post(`${ragEndpoint}/api/agent/execute`, {
            task: prompt,
            model,
          });

          returnData.push({
            json: agentResponse.data,
            pairedItem: { item: i },
          });
        }
      } catch (error) {
        if (this.continueOnFail()) {
          returnData.push({
            json: {
              error: error.message,
            },
            pairedItem: { item: i },
          });
          continue;
        }
        throw new NodeOperationError(this.getNode(), error);
      }
    }

    return [returnData];
  }
}
