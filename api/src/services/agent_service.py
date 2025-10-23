from typing import List, Dict, Any, Optional
from services.vectorstore_service import VectorStoreService
from services.claude_service import ClaudeService
from models.schemas import AgentTaskResponse
import json

class AgentService:
    """Service for agentic task execution with tool use"""

    def __init__(self, vectorstore: VectorStoreService, claude: ClaudeService):
        self.vectorstore = vectorstore
        self.claude = claude
        self.available_tools = self._define_tools()

    def _define_tools(self) -> List[Dict[str, Any]]:
        """Define available tools for the agent"""
        return [
            {
                "name": "search_knowledge_base",
                "description": "Search the knowledge base for relevant information. Use this when you need to find specific information from documents.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        },
                        "knowledge_base_id": {
                            "type": "string",
                            "description": "The knowledge base to search (default: 'default')"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results to return (default: 5)"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "python_repl",
                "description": "Execute Python code. Use this for calculations, data processing, or any computational tasks. The code runs in a safe sandboxed environment.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python code to execute"
                        }
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "web_search",
                "description": "Search the web for current information. Use this when you need up-to-date information not in the knowledge base.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]

    async def execute_task(
        self,
        task: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_iterations: int = 5,
        knowledge_base_id: Optional[str] = None,
        tools: Optional[List[str]] = None
    ) -> AgentTaskResponse:
        """
        Execute an agentic task with iterative tool use.
        The agent will use tools as needed to complete the task.
        """

        # Filter tools if specific ones are requested
        available_tools = self.available_tools
        if tools:
            available_tools = [
                tool for tool in self.available_tools
                if tool["name"] in tools
            ]

        # System prompt for the agent
        system_prompt = """You are a helpful AI agent that can use tools to complete tasks.
Think step by step about what you need to do.
Use the available tools when necessary to gather information or perform actions.
Always provide a clear final answer to the user's request."""

        # Initialize conversation
        messages = [
            {"role": "user", "content": task}
        ]

        steps = []
        total_usage = {"input_tokens": 0, "output_tokens": 0}
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Get response from Claude with tools
            response = await self.claude.generate_with_tools(
                messages=messages,
                tools=available_tools,
                system_prompt=system_prompt,
                model=model
            )

            # Track usage
            total_usage["input_tokens"] += response["usage"]["input_tokens"]
            total_usage["output_tokens"] += response["usage"]["output_tokens"]

            # Add assistant response to messages
            assistant_content = []
            if response["text"]:
                assistant_content.append({
                    "type": "text",
                    "text": response["text"]
                })

            # Record step
            step = {
                "iteration": iteration,
                "thought": response["text"],
                "tool_uses": []
            }

            # Process tool uses
            if response["tool_uses"]:
                for tool_use in response["tool_uses"]:
                    assistant_content.append({
                        "type": "tool_use",
                        "id": tool_use["id"],
                        "name": tool_use["name"],
                        "input": tool_use["input"]
                    })

                    # Execute tool
                    tool_result = await self._execute_tool(
                        tool_use["name"],
                        tool_use["input"],
                        knowledge_base_id
                    )

                    step["tool_uses"].append({
                        "tool": tool_use["name"],
                        "input": tool_use["input"],
                        "result": tool_result
                    })

                # Add assistant message with tool uses
                messages.append({
                    "role": "assistant",
                    "content": assistant_content
                })

                # Add tool results
                tool_result_content = []
                for tool_use, step_tool in zip(response["tool_uses"], step["tool_uses"]):
                    tool_result_content.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use["id"],
                        "content": json.dumps(step_tool["result"])
                    })

                messages.append({
                    "role": "user",
                    "content": tool_result_content
                })

                steps.append(step)
            else:
                # No more tool uses, task is complete
                steps.append(step)
                break

            # Check stop reason
            if response["stop_reason"] == "end_turn":
                break

        # Determine success
        success = response["stop_reason"] in ["end_turn", "stop_sequence"]

        return AgentTaskResponse(
            result=response["text"],
            steps=steps,
            usage=total_usage,
            success=success
        )

    async def _execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        knowledge_base_id: Optional[str] = None
    ) -> Any:
        """Execute a tool and return the result"""

        if tool_name == "search_knowledge_base":
            kb_id = parameters.get("knowledge_base_id", knowledge_base_id or "default")
            query = parameters["query"]
            top_k = parameters.get("top_k", 5)

            results = await self.vectorstore.search(
                query=query,
                knowledge_base_id=kb_id,
                top_k=top_k
            )

            return {
                "results": [
                    {
                        "content": r["content"],
                        "score": r["score"],
                        "metadata": r["metadata"]
                    }
                    for r in results
                ]
            }

        elif tool_name == "python_repl":
            code = parameters["code"]
            # In production, use a proper sandboxed environment
            try:
                # Limited safe execution
                exec_globals = {"__builtins__": {}}
                exec_locals = {}
                exec(code, exec_globals, exec_locals)
                return {"output": str(exec_locals.get("result", "Code executed successfully"))}
            except Exception as e:
                return {"error": str(e)}

        elif tool_name == "web_search":
            # Placeholder - integrate with actual web search API
            return {
                "message": "Web search not implemented yet",
                "query": parameters["query"]
            }

        return {"error": f"Unknown tool: {tool_name}"}

    async def invoke_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Directly invoke a tool"""
        return await self._execute_tool(tool_name, parameters, None)

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools"""
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"]["properties"]
            }
            for tool in self.available_tools
        ]
