"""
LegalMind FastAPI Application
Main application entry point for the legal analysis API.
"""

import uuid
import json
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from config.settings import get_settings
from managers.chatbot_manager_new import get_chatbot_manager
from api.endpoints_new import router
from utils.error_handlers import (
    api_error_handler,
    validation_exception_handler,
    general_exception_handler,
    APIError,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    print("Starting LegalMind API...")
    settings = get_settings()
    print(f"Project ID: {settings.google_cloud_project}")
    print(f"Environment: {'Development' if settings.debug else 'Production'}")
    
    # Initialize chatbot manager (with timeout to prevent indefinite hangs)
    print("Initializing ChatbotManager...")
    try:
        # Run chatbot initialization in a thread with timeout
        def init_chatbot():
            try:
                return get_chatbot_manager()
            except Exception as e:
                print(f"⚠️ Error initializing ChatbotManager: {e}")
                return None
        
        # Try to initialize with 10 second timeout
        await asyncio.wait_for(
            asyncio.to_thread(init_chatbot),
            timeout=10.0
        )
        print("✅ ChatbotManager initialized")
    except asyncio.TimeoutError:
        print("⚠️ ChatbotManager initialization timed out - continuing with limited functionality")
    except Exception as e:
        print(f"⚠️ ChatbotManager initialization warning: {e}")
    
    yield
    
    # Shutdown
    print("Shutting down LegalMind API...")
    
    # Clean up chat sessions
    try:
        chatbot = get_chatbot_manager()
        await asyncio.wait_for(
            chatbot.cleanup_old_sessions(max_age_minutes=0),
            timeout=5.0
        )
    except asyncio.TimeoutError:
        print("⚠️ Session cleanup timed out")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")
    
    await asyncio.sleep(0.5)
    print("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="LegalMind API",
    description="AI-powered legal contract analysis and research",
    version="1.0.0",
    lifespan=lifespan,
)

# Add GZIP compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add CORS middleware
settings = get_settings()
allowed_origins = [
    origin.strip()
    for origin in settings.allowed_origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug or not allowed_origins else allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API router (no prefix - backend is a standalone service)
app.include_router(router)


# Global exception handlers for better error responses
from fastapi import Request
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def handle_validation_exception(request: Request, exc: RequestValidationError):
    return await validation_exception_handler(request, exc)

@app.exception_handler(APIError)
async def handle_api_error(request: Request, exc: APIError):
    return await api_error_handler(request, exc)

@app.exception_handler(Exception)
async def handle_general_exception(request: Request, exc: Exception):
    return await general_exception_handler(request, exc)


# WebSocket endpoint for real-time chat
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat interactions."""
    await websocket.accept()
    
    session_id = None
    chatbot = get_chatbot_manager()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Get or create session ID
            session_id = message_data.get("session_id")
            if not session_id:
                session_id = str(uuid.uuid4())
            
            message = message_data.get("message", "")
            contract_id = message_data.get("contract_id")
            
            # Send acknowledgment
            await websocket.send_text(json.dumps({
                "type": "ack",
                "session_id": session_id,
                "status": "processing",
            }))
            
            # Process message
            response = await chatbot.process_message(
                session_id=session_id,
                user_message=message,
                contract_id=contract_id,
            )
            
            # Send response
            await websocket.send_text(json.dumps({
                "type": "response",
                **response,
            }))
    
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {session_id}")
    except json.JSONDecodeError as e:
        print(f"Invalid JSON received: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": "Invalid JSON format",
            }))
        except:
            pass
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": str(e),
            }))
        except:
            pass


# WebSocket endpoint for workflow streaming
@app.websocket("/ws/workflow")
async def websocket_workflow(websocket: WebSocket):
    """WebSocket endpoint for streaming workflow progress."""
    await websocket.accept()
    
    chatbot = get_chatbot_manager()
    
    try:
        # Receive workflow request
        data = await websocket.receive_text()
        request = json.loads(data)
        
        session_id = request.get("session_id", str(uuid.uuid4()))
        workflow_name = request.get("workflow_name")
        contract_id = request.get("contract_id")
        
        if not workflow_name or not contract_id:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": "workflow_name and contract_id are required",
            }))
            return
        
        # Send start notification
        await websocket.send_text(json.dumps({
            "type": "start",
            "workflow": workflow_name,
            "contract_id": contract_id,
            "session_id": session_id,
        }))
        
        # Run workflow with progress updates
        from agents.agent_strategies_new import get_workflow_template
        from agents.agent_definitions_new import get_agent_config
        
        template = get_workflow_template(workflow_name)
        if not template:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": f"Unknown workflow: {workflow_name}",
            }))
            return
        
        # Initialize session
        session = await chatbot.initialize_session(session_id)
        session["active_contract_id"] = contract_id
        
        results = []
        total_agents = len(template["agents"])
        
        for i, agent_name in enumerate(template["agents"]):
            # Send progress update
            await websocket.send_text(json.dumps({
                "type": "progress",
                "agent": agent_name,
                "step": i + 1,
                "total": total_agents,
                "status": "running",
            }))
            
            # Get agent config and execute
            agent_config = get_agent_config(agent_name)
            tools = chatbot._get_tools_for_agent(agent_name)
            
            prompt = f"Analyze the contract with ID {contract_id} for your specific purpose."
            context = await chatbot._build_context(session, prompt)
            
            response = await chatbot._call_agent(
                agent_name=agent_name,
                instructions=agent_config["instructions"],
                user_message=prompt,
                context=context,
                tools=tools,
                use_search="search_grounding" in agent_config.get("tools", []),
                session_id=session_id,
                temperature=agent_config.get("temperature", 0.5),
            )
            
            results.append({
                "agent": agent_config["name"],
                "agent_id": agent_name,
                "message": response["message"],
                "citations": response.get("citations", []),
            })
            
            # Send agent completion
            await websocket.send_text(json.dumps({
                "type": "agent_complete",
                "agent": agent_config["name"],
                "agent_id": agent_name,
                "step": i + 1,
                "total": total_agents,
                "message": response["message"][:500] + "..." if len(response["message"]) > 500 else response["message"],
            }))
        
        # Send completion
        await websocket.send_text(json.dumps({
            "type": "complete",
            "workflow": workflow_name,
            "results": results,
        }))
        
    except WebSocketDisconnect:
        print("Workflow WebSocket disconnected")
    except Exception as e:
        print(f"Workflow WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": str(e),
            }))
        except:
            pass


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "LegalMind API",
        "version": "1.0.0",
        "description": "AI-powered legal contract analysis and research",
        "docs_url": "/docs",
        "endpoints": {
            "chat": "/api/chat",
            "contracts": "/api/contracts",
            "workflows": "/api/workflow",
            "agents": "/api/agents",
            "health": "/api/health",
        },
    }


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "api.app_new:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
