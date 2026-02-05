"""
LegalMind API Endpoints
FastAPI endpoints for the legal analysis chatbot.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request, Depends, Security
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import asyncio
from datetime import datetime
import io
import logging

from managers.chatbot_manager_new import get_chatbot_manager, ChatbotManager
from config.settings import get_settings
from services.firestore_service import FirestoreService
from services.storage_service import StorageService
from tools.contract_tools import extract_contract_text
from agents.agent_definitions_new import list_agents, AGENT_CONFIGS
from agents.agent_strategies_new import list_workflow_templates

# API key auth (optional in development if not set)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> None:
    settings = get_settings()
    if not settings.api_secret_key:
        return
    if api_key != settings.api_secret_key:
        raise HTTPException(status_code=403, detail="Invalid API key")


# Create router
router = APIRouter(dependencies=[Depends(verify_api_key)])
logger = logging.getLogger(__name__)


# =============================================================================
# Request/Response Models (MUST BE FIRST - used in utility functions)
# =============================================================================

class ChatMessage(BaseModel):
    """Model for chat messages."""
    session_id: Optional[str] = None
    message: str
    contract_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Model for chat responses."""
    success: bool
    message: str
    agent: Optional[str] = None
    agent_id: Optional[str] = None
    citations: Optional[List[Dict[str, Any]]] = None
    tools_used: Optional[List[str]] = None
    session_id: Optional[str] = None
    error: Optional[str] = None


class ContractUpload(BaseModel):
    """Model for contract upload metadata."""
    name: str
    contract_type: Optional[str] = None
    parties: Optional[List[str]] = None
    notes: Optional[str] = None


class ContractResponse(BaseModel):
    """Model for contract responses."""
    success: bool
    contract_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


class WorkflowRequest(BaseModel):
    """Model for workflow execution requests."""
    session_id: str
    workflow_name: str
    contract_id: str


class WorkflowResponse(BaseModel):
    """Model for workflow responses."""
    success: bool
    workflow: Optional[str] = None
    contract_id: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class SessionInfo(BaseModel):
    """Model for session information."""
    session_id: str
    created_at: str
    message_count: int
    active_contract_id: Optional[str] = None


# =============================================================================
# Simple In-Memory Rate Limiting & Request De-dupe
# =============================================================================

_rate_limit_store: Dict[str, List[float]] = {}
_response_cache: Dict[str, Dict[str, Any]] = {}


def _get_client_key(request: Request) -> str:
    """Build a key for rate limiting and caching."""
    return request.client.host if request.client else "unknown"


def _rate_limit_check(request: Request, action: str) -> None:
    """Raise 429 if rate limit exceeded for the client."""
    settings = get_settings()
    limit = max(settings.rate_limit_requests_per_minute, 1)
    window_seconds = 60

    key = f"{_get_client_key(request)}:{action}"
    now = datetime.utcnow().timestamp()
    timestamps = _rate_limit_store.get(key, [])
    # Keep only last minute
    timestamps = [t for t in timestamps if now - t < window_seconds]
    if len(timestamps) >= limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait and retry.")
    timestamps.append(now)
    _rate_limit_store[key] = timestamps


def _get_cache_key(request: ChatMessage) -> str:
    """Create a deterministic cache key for duplicate chat requests."""
    return f"{request.session_id}:{request.contract_id or ''}:{request.message.strip()}"


def _get_cached_response(cache_key: str, ttl_seconds: Optional[int] = None) -> Optional[Dict[str, Any]]:
    entry = _response_cache.get(cache_key)
    if not entry:
        return None
    if ttl_seconds is None:
        ttl_seconds = get_settings().response_cache_ttl_seconds
    if datetime.utcnow().timestamp() - entry["ts"] > ttl_seconds:
        _response_cache.pop(cache_key, None)
        return None
    return entry["response"]


def _set_cached_response(cache_key: str, response: Dict[str, Any]) -> None:
    _response_cache[cache_key] = {
        "ts": datetime.utcnow().timestamp(),
        "response": response,
    }


# =============================================================================
# Chat Endpoints
# =============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatMessage, http_request: Request):
    """Process a chat message and return the agent response.
    
    Args:
        request: Chat message request
        
    Returns:
        Agent response with citations and metadata
    """
    try:
        _rate_limit_check(http_request, "chat")
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # Generate session ID if not provided
        session_id = request.session_id
        if not session_id:
            session_id = str(uuid.uuid4())

        cache_key = _get_cache_key(request)
        cached = _get_cached_response(cache_key)
        if cached:
            return ChatResponse(**cached)

        chatbot = get_chatbot_manager()
        try:
            response = await asyncio.wait_for(
                chatbot.process_message(
                    session_id=session_id,
                    user_message=request.message,
                    contract_id=request.contract_id,
                ),
                timeout=30.0,
            )
        except asyncio.TimeoutError:
            logger.error("Chat request timed out for session %s", session_id)
            raise HTTPException(
                status_code=504,
                detail="Request timeout - the analysis took too long. Please try again.",
            )
        if response.get("success"):
            _set_cached_response(cache_key, response)
        return ChatResponse(**response)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in chat endpoint: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your message. Please try again.",
        )


@router.post("/chat/session")
async def create_session(http_request: Request):
    """Create a new chat session.
    
    Returns:
        New session information
    """
    try:
        _rate_limit_check(http_request, "session")
        session_id = str(uuid.uuid4())
        chatbot = get_chatbot_manager()
        
        # Initialize session with timeout
        try:
            await asyncio.wait_for(
                chatbot.initialize_session(session_id),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            logger.warning("Session initialization timed out for %s", session_id)
            # Return response anyway - session exists locally even if Firestore write timed out
        
        return {
            "success": True,
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating session: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to create session. Please try again.",
        )


@router.get("/chat/session/{session_id}")
async def get_session(session_id: str, limit: int = 100):
    """Get session information and history.
    
    Args:
        session_id: The session ID
        
    Returns:
        Session information with message history
    """
    try:
        chatbot = get_chatbot_manager()
        history = await chatbot.get_session_history(session_id, limit=limit)
        
        firestore = FirestoreService()
        session = await firestore.get_session(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "session": session,
            "messages": history,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/session/{session_id}")
async def delete_session(session_id: str):
    """Close and delete a chat session.
    
    Args:
        session_id: The session ID
        
    Returns:
        Deletion confirmation
    """
    try:
        chatbot = get_chatbot_manager()
        await chatbot.close_session(session_id)
        
        return {
            "success": True,
            "message": f"Session {session_id} closed",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/sessions")
async def list_sessions(limit: int = 50):
    """List all active sessions.
    
    Returns:
        List of session information
    """
    try:
        firestore = FirestoreService()
        sessions = await firestore.list_sessions(limit=limit)
        
        return {
            "success": True,
            "sessions": sessions,
        }
    except Exception as e:
        logger.error("Error listing sessions: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch sessions. Please try again.")


# =============================================================================
# Contract Endpoints
# =============================================================================

@router.post("/contracts/upload", response_model=ContractResponse)
async def upload_contract(
    file: UploadFile = File(...),
    name: str = Form(...),
    contract_type: Optional[str] = Form(None),
    parties: Optional[str] = Form(None),  # JSON string
    notes: Optional[str] = Form(None),
):
    """Upload a new contract document.
    
    Args:
        file: The contract file (PDF)
        name: Contract name
        contract_type: Type of contract
        parties: JSON string of party names
        notes: Additional notes
        
    Returns:
        Upload confirmation with contract ID
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Generate contract ID
        contract_id = str(uuid.uuid4())
        
        # Upload to Cloud Storage
        storage = StorageService()
        content = await file.read()
        file_url = await storage.upload_contract_pdf(
            io.BytesIO(content),
            contract_id,
            file.filename,
        )
        
        # Parse parties if provided
        party_list = None
        if parties:
            import json
            try:
                party_list = json.loads(parties)
            except:
                party_list = [p.strip() for p in parties.split(',')]
        
        # Save metadata to Firestore
        firestore = FirestoreService()
        contract_data = {
            "id": contract_id,
            "name": name,
            "filename": file.filename,
            "file_url": file_url,
            "type": contract_type,
            "parties": party_list,
            "notes": notes,
            "uploaded_at": datetime.now().isoformat(),
            "status": "uploaded",
        }
        await firestore.create_contract(contract_id, contract_data)

        # Trigger background text extraction for analysis readiness
        async def _extract_text():
            try:
                result = await extract_contract_text(contract_id)
                if result.get("status") == "success":
                    await firestore.update_document(
                        firestore.CONTRACTS,
                        contract_id,
                        {"status": "text_extracted"},
                    )
            except Exception as e:
                print(f"⚠️ Background extraction failed for {contract_id}: {e}")

        asyncio.create_task(_extract_text())
        
        return ContractResponse(
            success=True,
            contract_id=contract_id,
            message=f"Contract '{name}' uploaded successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts")
async def list_contracts(
    status: Optional[str] = None,
    contract_type: Optional[str] = None,
):
    """List all contracts.
    
    Args:
        status: Filter by status
        contract_type: Filter by type
        
    Returns:
        List of contracts
    """
    try:
        firestore = FirestoreService()
        filters = {}
        if status:
            filters["status"] = status
        if contract_type:
            filters["type"] = contract_type
            
        contracts = await firestore.list_contracts(filters)
        
        return {
            "success": True,
            "contracts": contracts,
            "count": len(contracts),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/{contract_id}")
async def get_contract(contract_id: str):
    """Get contract details.
    
    Args:
        contract_id: The contract ID
        
    Returns:
        Contract details and metadata
    """
    try:
        firestore = FirestoreService()
        contract = await firestore.get_contract(contract_id)
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        return {
            "success": True,
            "contract": contract,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/contracts/{contract_id}")
async def delete_contract(contract_id: str):
    """Delete a contract.
    
    Args:
        contract_id: The contract ID
        
    Returns:
        Deletion confirmation
    """
    try:
        firestore = FirestoreService()
        storage = StorageService()
        
        # Get contract to find file path
        contract = await firestore.get_contract(contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        # Delete from storage
        if contract.get("file_url"):
            await storage.delete_file(f"contracts/{contract_id}/{contract['filename']}")
        
        # Delete from Firestore
        await firestore.delete_contract(contract_id)
        
        return {
            "success": True,
            "message": f"Contract {contract_id} deleted",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/{contract_id}/download")
async def download_contract(contract_id: str):
    """Get a download URL for a contract.
    
    Args:
        contract_id: The contract ID
        
    Returns:
        Signed download URL
    """
    try:
        firestore = FirestoreService()
        contract = await firestore.get_contract(contract_id)
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        storage = StorageService()
        blob_path = contract.get("file_url")
        if not blob_path:
            blob_path = f"{storage.settings.gcs_contracts_folder}/{contract['filename']}"

        download_url = await storage.get_signed_url(blob_path)
        
        return {
            "success": True,
            "download_url": download_url,
            "filename": contract["filename"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/{contract_id}/clauses")
async def get_contract_clauses(contract_id: str):
    """Get all extracted clauses for a contract.
    
    Args:
        contract_id: The contract ID
        
    Returns:
        List of clauses with analysis
    """
    try:
        firestore = FirestoreService()
        clauses = await firestore.get_contract_clauses(contract_id)
        
        return {
            "success": True,
            "contract_id": contract_id,
            "clauses": clauses,
            "count": len(clauses),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Workflow Endpoints
# =============================================================================

@router.post("/workflow/run", response_model=WorkflowResponse)
async def run_workflow(request: WorkflowRequest):
    """Execute a predefined workflow on a contract.
    
    Args:
        request: Workflow execution request
        
    Returns:
        Workflow execution results
    """
    try:
        chatbot = get_chatbot_manager()
        result = await chatbot.run_workflow(
            session_id=request.session_id,
            workflow_name=request.workflow_name,
            contract_id=request.contract_id,
        )
        return WorkflowResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow/templates")
async def get_workflow_templates():
    """Get available workflow templates.
    
    Returns:
        List of workflow templates
    """
    templates = list_workflow_templates()
    return {
        "success": True,
        "templates": templates,
    }


# =============================================================================
# Agent Endpoints
# =============================================================================

@router.get("/agents")
async def get_agents():
    """Get list of available agents.
    
    Returns:
        List of agents with their capabilities
    """
    agents = list_agents()
    return {
        "success": True,
        "agents": agents,
    }


@router.get("/agents/{agent_id}")
async def get_agent_info(agent_id: str):
    """Get information about a specific agent.
    
    Args:
        agent_id: The agent ID
        
    Returns:
        Agent details and capabilities
    """
    if agent_id not in AGENT_CONFIGS:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    config = AGENT_CONFIGS[agent_id]
    return {
        "success": True,
        "agent": {
            "id": agent_id,
            "name": config["name"],
            "tools": config["tools"],
            "instructions": config["instructions"][:500] + "...",  # Truncate
        },
    }


# =============================================================================
# Thinking Logs Endpoints
# =============================================================================

@router.get("/thinking-logs/{session_id}")
async def get_thinking_logs(session_id: str):
    """Get thinking logs for a session.
    
    Args:
        session_id: The session ID
        
    Returns:
        List of thinking log entries
    """
    try:
        firestore = FirestoreService()
        logs = await firestore.get_thinking_logs(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "logs": logs,
            "count": len(logs),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Document Generation Endpoints
# =============================================================================

@router.get("/documents")
async def list_documents(contract_id: Optional[str] = None):
    """List generated documents.
    
    Args:
        contract_id: Optional filter by contract
        
    Returns:
        List of documents
    """
    try:
        firestore = FirestoreService()
        filters = {}
        if contract_id:
            filters["contract_id"] = contract_id
            
        documents = await firestore.list_documents(filters)
        
        return {
            "success": True,
            "documents": documents,
            "count": len(documents),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}/download")
async def download_document(document_id: str):
    """Get download URL for a generated document.
    
    Args:
        document_id: The document ID
        
    Returns:
        Signed download URL
    """
    try:
        firestore = FirestoreService()
        document = await firestore.get_document(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        storage = StorageService()
        download_url = await storage.get_signed_url(document["file_path"])
        
        return {
            "success": True,
            "download_url": download_url,
            "filename": document.get("filename", "document.docx"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Compliance Endpoints
# =============================================================================

@router.get("/compliance/frameworks")
async def get_compliance_frameworks():
    """Get available compliance frameworks.
    
    Returns:
        List of compliance frameworks
    """
    from tools.compliance_tools import COMPLIANCE_FRAMEWORKS
    
    frameworks = [
        {
            "id": fw_id,
            "name": fw["name"],
            "description": fw["description"],
            "requirement_count": len(fw["requirements"]),
        }
        for fw_id, fw in COMPLIANCE_FRAMEWORKS.items()
    ]
    
    return {
        "success": True,
        "frameworks": frameworks,
    }


@router.get("/compliance/check/{contract_id}")
async def check_contract_compliance(
    contract_id: str,
    framework: Optional[str] = None,
):
    """Check contract compliance against frameworks.
    
    Args:
        contract_id: The contract ID
        framework: Optional specific framework
        
    Returns:
        Compliance check results
    """
    try:
        from tools.compliance_tools import check_compliance
        
        result = await check_compliance(
            contract_id=contract_id,
            framework=framework,
        )
        
        return {
            "success": True,
            "contract_id": contract_id,
            "compliance": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Risk Assessment Endpoints
# =============================================================================

@router.get("/risk/assess/{contract_id}")
async def assess_contract_risk(contract_id: str):
    """Get risk assessment for a contract.
    
    Args:
        contract_id: The contract ID
        
    Returns:
        Risk assessment results
    """
    try:
        from tools.risk_tools import assess_contract_risk as assess_risk
        
        result = await assess_risk(contract_id=contract_id)
        
        return {
            "success": True,
            "contract_id": contract_id,
            "risk_assessment": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Health Check
# =============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint.
    
    Returns:
        Service health status
    """
    return {
        "status": "healthy",
        "service": "LegalMind API",
        "timestamp": datetime.now().isoformat(),
    }
