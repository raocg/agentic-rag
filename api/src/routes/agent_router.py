from fastapi import APIRouter, HTTPException, Depends
from models.schemas import AgentTaskRequest, AgentTaskResponse
from services.agent_service import AgentService
from services.vectorstore_service import VectorStoreService
from services.claude_service import ClaudeService

router = APIRouter()

def get_agent_service():
    """Dependency to get Agent service instance"""
    vectorstore = VectorStoreService()
    claude = ClaudeService()
    return AgentService(vectorstore, claude)

@router.post("/execute", response_model=AgentTaskResponse)
async def execute_agent_task(
    request: AgentTaskRequest,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    Execute an agentic task using Claude with tool use capabilities.
    The agent can iteratively use tools to complete complex tasks.
    """
    try:
        response = await agent_service.execute_task(
            task=request.task,
            model=request.model,
            max_iterations=request.max_iterations,
            knowledge_base_id=request.knowledge_base_id,
            tools=request.tools
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools")
async def list_available_tools(
    agent_service: AgentService = Depends(get_agent_service)
):
    """List all available tools for the agent"""
    try:
        tools = agent_service.get_available_tools()
        return {"tools": tools}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tools/{tool_name}/invoke")
async def invoke_tool(
    tool_name: str,
    parameters: dict,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    Directly invoke a specific tool with given parameters.
    Useful for testing tools individually.
    """
    try:
        result = await agent_service.invoke_tool(tool_name, parameters)
        return {"tool": tool_name, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
