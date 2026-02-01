"""
LegalMind API Endpoints
FastAPI endpoints for the legal analysis chatbot.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

from managers.chatbot_manager_new import get_chatbot_manager, ChatbotManager
from services.firestore_service import FirestoreService
from services.storage_service import StorageService
from agents.agent_definitions_new import list_agents, AGENT_CONFIGS
from agents.agent_strategies_new import list_workflow_templates

# Create router
router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class ChatMessage(BaseModel):
    """Model for chat messages."""
    session_id: str
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
# Chat Endpoints
# =============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatMessage):
    """Process a chat message and return the agent response.
    
    Args:
        request: Chat message request
        
    Returns:
        Agent response with citations and metadata
    """
    try:
        chatbot = get_chatbot_manager()
        response = await chatbot.process_message(
            session_id=request.session_id,
            user_message=request.message,
            contract_id=request.contract_id,
        )
        return ChatResponse(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/session")
async def create_session():
    """Create a new chat session.
    
    Returns:
        New session information
    """
    try:
        session_id = str(uuid.uuid4())
        chatbot = get_chatbot_manager()
        await chatbot.initialize_session(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/session/{session_id}")
async def get_session(session_id: str):
    """Get session information and history.
    
    Args:
        session_id: The session ID
        
    Returns:
        Session information with message history
    """
    try:
        chatbot = get_chatbot_manager()
        history = await chatbot.get_session_history(session_id)
        
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
async def list_sessions():
    """List all active sessions.
    
    Returns:
        List of session information
    """
    try:
        firestore = FirestoreService()
        sessions = await firestore.list_sessions()
        
        return {
            "success": True,
            "sessions": sessions,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        file_url = await storage.upload_contract(contract_id, file.filename, content)
        
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
        download_url = await storage.get_signed_url(
            f"contracts/{contract_id}/{contract['filename']}"
        )
        
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
