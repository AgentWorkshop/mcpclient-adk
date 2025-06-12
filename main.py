import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.genai import types
from starlette.websockets import WebSocketDisconnect

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_NAME = "ADK MCP example"
session_service = InMemorySessionService()
artifacts_service = InMemoryArtifactService()


async def get_tools_async(server_params):
    """Gets tools from MCP Server."""
    tools, exit_stack = await MCPToolset.from_server(connection_params=server_params)
    # MCP requires maintaining a connection to the local MCP Server.
    # Using exit_stack to clean up server connection before exit.
    return tools, exit_stack


async def get_agent_async(server_params):
    """Creates an ADK Agent with tools from MCP Server."""
    tools, exit_stack = await get_tools_async(server_params)
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-pro-preview-03-25")
    root_agent = LlmAgent(
        model=gemini_model,
        name="ai_assistant",
        instruction="You're a helpful assistant. Use tools to get information to answer user questions. Always respond in Traditional Chinese (繁體中文). Please format your answer in markdown format.",
        tools=tools,
    )
    return root_agent, exit_stack


ct_server_params = StdioServerParameters(
    command="python",
    args=["./mcp_server/cocktail.py"],
)


async def run_agent(server_params, session_id, question, websocket=None):
    """Run agent with optional streaming to websocket."""
    query = question
    logging.info(f"[user][{session_id}]: {query}")
    content = types.Content(role="user", parts=[types.Part(text=query)])
    root_agent, exit_stack = await get_agent_async(server_params)
    runner = Runner(
        app_name=APP_NAME,
        agent=root_agent,
        artifact_service=artifacts_service,
        session_service=session_service,
    )
    events_async = runner.run_async(
        session_id=session_id, user_id=session_id, new_message=content
    )

    response = []
    # 用於跟踪上一次發送的文本長度
    last_sent_length = 0
    current_response = ""
    
    try:
        async for event in events_async:
            if event.content.role == "model" and event.content.parts[0].text:
                text_chunk = event.content.parts[0].text
                logging.info(f"[agent][{session_id}]: {text_chunk}")
                response.append(text_chunk)
                
                # 如果提供了websocket，則流式發送
                if websocket:
                    current_response += text_chunk
                    # 只發送新增的部分
                    new_text = current_response[last_sent_length:]
                    if new_text.strip():
                        await websocket.send_text(json.dumps({"message": new_text, "streaming": True}))
                        last_sent_length = len(current_response)
                        await asyncio.sleep(0.01)  # 小延遲以避免過快發送
    finally:
        # 確保在任何情況下都關閉exit_stack
        await exit_stack.aclose()
        logging.info(f"[agent][{session_id}]: Full response assembled. Length: {len(''.join(response))}")
        
        # 如果使用流式傳輸，發送完成標記
        if websocket and response:
            await websocket.send_text(json.dumps({"message": "", "streaming": False, "complete": True}))
    
    return response


async def run_adk_agent_async(websocket, server_params, session_id):
    """Client to agent communication with streaming support"""
    try:
        # Your existing setup for the agent might be here
        logging.info(f"Agent task started for session {session_id}")
        while True:
            text = await websocket.receive_text()
            # 直接將websocket傳遞給run_agent以啟用流式傳輸
            await run_agent(server_params, session_id, text, websocket)
            await asyncio.sleep(0)

    except WebSocketDisconnect:
        # This block executes when the client disconnects
        logging.info(f"Client {session_id} disconnected.")
    except Exception as e:
        # Catch other potential errors in your agent logic
        logging.error(
            f"Error in agent task for session {session_id}: {e}", exc_info=True
        )
        # 嘗試向客戶端發送錯誤消息
        try:
            await websocket.send_text(json.dumps({"message": f"發生錯誤: {str(e)}", "error": True}))
        except:
            pass  # 如果無法發送錯誤消息，則忽略
    finally:
        logging.info(f"Agent task ending for session {session_id}")


# FastAPI web app

app = FastAPI()

STATIC_DIR = Path("static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    """Serves the index.html"""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: int):
    """Client websocket endpoint"""

    # Wait for client connection
    await websocket.accept()
    logging.info(f"Client #{session_id} connected")

    # Start agent session
    session = session_service.create_session(
        app_name=APP_NAME, user_id=session_id, session_id=session_id, state={}
    )

    # Start tasks
    agent_task = asyncio.create_task(
        run_adk_agent_async(websocket, ct_server_params, session_id)
    )

    await asyncio.gather(agent_task)

    # Disconnected
    logging.info(f"Client #{session_id} disconnected")
