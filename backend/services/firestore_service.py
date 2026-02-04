"""
Firestore Service
Handles all interactions with Google Cloud Firestore.
"""

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import uuid
from functools import lru_cache

from config.settings import get_settings


class FirestoreService:
    """Service for interacting with Firestore."""
    
    # Collection names
    CONTRACTS = "contracts"
    CLAUSES = "clauses"
    SESSIONS = "sessions"
    MESSAGES = "messages"
    THINKING_LOGS = "thinking_logs"
    DOCUMENTS = "documents"
    
    def __init__(self):
        """Initialize the Firestore service."""
        self.settings = get_settings()
        self._client = None
    
    @property
    def client(self) -> firestore.Client:
        """Get or create the Firestore client."""
        if self._client is None:
            self._client = firestore.Client(
                project=self.settings.google_cloud_project,
                database=self.settings.firestore_database,
            )
        return self._client
    
    # =========================================================================
    # Generic CRUD Operations
    # =========================================================================
    
    async def create_document(
        self,
        collection: str,
        data: Dict[str, Any],
        document_id: Optional[str] = None
    ) -> str:
        """Create a new document in a collection.
        
        Args:
            collection: Collection name
            data: Document data
            document_id: Optional specific document ID
            
        Returns:
            The document ID
        """
        # Add timestamps
        data["created_at"] = firestore.SERVER_TIMESTAMP
        data["updated_at"] = firestore.SERVER_TIMESTAMP
        
        try:
            if document_id:
                doc_ref = self.client.collection(collection).document(document_id)
                await asyncio.wait_for(
                    asyncio.to_thread(doc_ref.set, data),
                    timeout=10.0
                )
                return document_id
            else:
                doc_ref = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.collection(collection).add,
                        data
                    ),
                    timeout=10.0
                )
                return doc_ref[1].id
        except asyncio.TimeoutError:
            print(f"⚠️ Firestore timeout writing to {collection}/{document_id}")
            # Return the document_id anyway for local session management
            return document_id or str(data.get('id', uuid.uuid4()))
    
    async def get_document(
        self,
        collection: str,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a document by ID.
        
        Args:
            collection: Collection name
            document_id: Document ID
            
        Returns:
            Document data or None if not found
        """
        try:
            doc_ref = self.client.collection(collection).document(document_id)
            doc = await asyncio.wait_for(
                asyncio.to_thread(doc_ref.get),
                timeout=10.0
            )
            
            if doc.exists:
                data = doc.to_dict()
                data["id"] = doc.id
                return data
            return None
        except asyncio.TimeoutError:
            print(f"⚠️ Firestore timeout reading {collection}/{document_id}")
            return None
    
    async def update_document(
        self,
        collection: str,
        document_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """Update a document.
        
        Args:
            collection: Collection name
            document_id: Document ID
            data: Fields to update
            
        Returns:
            True if successful
        """
        data["updated_at"] = firestore.SERVER_TIMESTAMP
        
        doc_ref = self.client.collection(collection).document(document_id)
        await asyncio.to_thread(doc_ref.update, data)
        return True
    
    async def delete_document(
        self,
        collection: str,
        document_id: str
    ) -> bool:
        """Delete a document.
        
        Args:
            collection: Collection name
            document_id: Document ID
            
        Returns:
            True if successful
        """
        doc_ref = self.client.collection(collection).document(document_id)
        await asyncio.to_thread(doc_ref.delete)
        return True
    
    async def query_documents(
        self,
        collection: str,
        filters: Optional[List[tuple]] = None,
        order_by: Optional[str] = None,
        order_direction: str = "DESCENDING",
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Query documents in a collection.
        
        Args:
            collection: Collection name
            filters: List of (field, operator, value) tuples
            order_by: Field to order by
            order_direction: "ASCENDING" or "DESCENDING"
            limit: Maximum number of results
            
        Returns:
            List of matching documents
        """
        query = self.client.collection(collection)
        
        # Apply filters
        if filters:
            for field, operator, value in filters:
                query = query.where(filter=FieldFilter(field, operator, value))
        
        # Apply ordering
        if order_by:
            direction = (
                firestore.Query.DESCENDING
                if order_direction == "DESCENDING"
                else firestore.Query.ASCENDING
            )
            query = query.order_by(order_by, direction=direction)
        
        # Apply limit
        if limit:
            query = query.limit(limit)
        
        # Execute query
        docs = await asyncio.to_thread(query.get)
        
        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)
        
        return results
    
    # =========================================================================
    # Contract Operations
    # =========================================================================
    
    async def create_contract(
        self,
        title: str,
        file_url: str,
        content: str,
        contract_type: Optional[str] = None,
        parties: Optional[List[Dict]] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Create a new contract document.
        
        Args:
            title: Contract title
            file_url: GCS URL of the PDF
            content: Extracted text content
            contract_type: Type of contract
            parties: List of parties involved
            session_id: Associated session ID
            
        Returns:
            Contract ID
        """
        data = {
            "title": title,
            "file_url": file_url,
            "content": content,
            "contract_type": contract_type,
            "parties": parties or [],
            "session_id": session_id,
            "status": "pending_analysis",
            "overall_risk_score": None,
            "compliance_status": None,
            "key_dates": [],
            "clauses": [],
        }
        
        return await self.create_document(self.CONTRACTS, data)
    
    async def get_contract(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """Get a contract by ID."""
        return await self.get_document(self.CONTRACTS, contract_id)
    
    async def update_contract_analysis(
        self,
        contract_id: str,
        analysis_results: Dict[str, Any]
    ) -> bool:
        """Update contract with analysis results.
        
        Args:
            contract_id: Contract ID
            analysis_results: Analysis data including:
                - contract_type
                - parties
                - key_dates
                - overall_risk_score
                - compliance_status
                - clauses (list of clause IDs)
                
        Returns:
            True if successful
        """
        update_data = {
            "status": "analyzed",
            **analysis_results
        }
        return await self.update_document(self.CONTRACTS, contract_id, update_data)
    
    async def list_contracts(
        self,
        status: Optional[str] = None,
        contract_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List contracts with optional filters."""
        filters = []
        if status:
            filters.append(("status", "==", status))
        if contract_type:
            filters.append(("contract_type", "==", contract_type))
        
        return await self.query_documents(
            self.CONTRACTS,
            filters=filters if filters else None,
            order_by="created_at",
            limit=limit
        )
    
    # =========================================================================
    # Clause Operations
    # =========================================================================
    
    async def create_clause(
        self,
        contract_id: str,
        clause_type: str,
        content: str,
        section_number: Optional[str] = None,
        risk_level: Optional[str] = None,
        risk_explanation: Optional[str] = None,
        compliance_issues: Optional[List[str]] = None,
    ) -> str:
        """Create a clause document.
        
        Args:
            contract_id: Parent contract ID
            clause_type: Type of clause
            content: Clause text
            section_number: Section identifier
            risk_level: Risk level (low/medium/high/critical)
            risk_explanation: Explanation of risk
            compliance_issues: List of compliance concerns
            
        Returns:
            Clause ID
        """
        data = {
            "contract_id": contract_id,
            "clause_type": clause_type,
            "content": content,
            "section_number": section_number,
            "risk_level": risk_level or "low",
            "risk_explanation": risk_explanation,
            "compliance_issues": compliance_issues or [],
            "recommendations": [],
        }
        
        return await self.create_document(self.CLAUSES, data)
    
    async def get_clauses_for_contract(
        self,
        contract_id: str
    ) -> List[Dict[str, Any]]:
        """Get all clauses for a contract."""
        return await self.query_documents(
            self.CLAUSES,
            filters=[("contract_id", "==", contract_id)],
            order_by="section_number",
            order_direction="ASCENDING"
        )
    
    # =========================================================================
    # Session Operations
    # =========================================================================
    
    async def create_session(
        self,
        session_id: str,
        contract_id: Optional[str] = None,
    ) -> str:
        """Create a new chat session.
        
        Args:
            session_id: Session ID (usually UUID)
            contract_id: Optional associated contract
            
        Returns:
            Session ID
        """
        data = {
            "session_id": session_id,
            "contract_id": contract_id,
            "status": "active",
            "last_activity": firestore.SERVER_TIMESTAMP,
        }
        
        return await self.create_document(self.SESSIONS, data, document_id=session_id)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID."""
        return await self.get_document(self.SESSIONS, session_id)
    
    async def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity timestamp."""
        return await self.update_document(
            self.SESSIONS,
            session_id,
            {"last_activity": firestore.SERVER_TIMESTAMP}
        )
    
    async def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent sessions."""
        return await self.query_documents(
            self.SESSIONS,
            order_by="last_activity",
            limit=limit
        )
    
    # =========================================================================
    # Message Operations
    # =========================================================================
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        agent_name: Optional[str] = None,
        citations: Optional[List[Dict]] = None,
    ) -> str:
        """Add a message to a session.
        
        Args:
            session_id: Session ID
            role: 'user' or 'assistant'
            content: Message content
            agent_name: Name of the agent (for assistant messages)
            citations: List of citation dicts
            
        Returns:
            Message ID
        """
        data = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "agent_name": agent_name,
            "citations": citations or [],
        }
        
        # Also update session activity
        await self.update_session_activity(session_id)
        
        return await self.create_document(self.MESSAGES, data)
    
    async def get_messages(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get messages for a session."""
        return await self.query_documents(
            self.MESSAGES,
            filters=[("session_id", "==", session_id)],
            order_by="created_at",
            order_direction="ASCENDING",
            limit=limit
        )
    
    # =========================================================================
    # Thinking Log Operations
    # =========================================================================
    
    async def log_agent_thinking(
        self,
        session_id: str,
        agent_name: str,
        input_text: str,
        output_text: str,
        reasoning: Optional[str] = None,
        tool_calls: Optional[List[Dict]] = None,
        duration_ms: Optional[int] = None,
    ) -> str:
        """Log agent thinking/reasoning.
        
        Args:
            session_id: Session ID
            agent_name: Name of the agent
            input_text: Input provided to agent
            output_text: Agent's output
            reasoning: Internal reasoning (if available)
            tool_calls: List of tool calls made
            duration_ms: Processing time in milliseconds
            
        Returns:
            Log ID
        """
        data = {
            "session_id": session_id,
            "agent_name": agent_name,
            "input_text": input_text,
            "output_text": output_text,
            "reasoning": reasoning,
            "tool_calls": tool_calls or [],
            "duration_ms": duration_ms,
        }
        
        return await self.create_document(self.THINKING_LOGS, data)
    
    async def get_thinking_logs(
        self,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get thinking logs with optional filters."""
        filters = []
        if session_id:
            filters.append(("session_id", "==", session_id))
        if agent_name:
            filters.append(("agent_name", "==", agent_name))
        
        return await self.query_documents(
            self.THINKING_LOGS,
            filters=filters if filters else None,
            order_by="created_at",
            limit=limit
        )
    
    # =========================================================================
    # Generated Documents Operations
    # =========================================================================
    
    async def create_generated_document(
        self,
        session_id: str,
        contract_id: Optional[str],
        document_type: str,
        title: str,
        file_url: str,
        content_summary: Optional[str] = None,
    ) -> str:
        """Create a generated document record.
        
        Args:
            session_id: Associated session
            contract_id: Associated contract (if any)
            document_type: Type (memo, summary, report, etc.)
            title: Document title
            file_url: GCS URL of the document
            content_summary: Brief summary
            
        Returns:
            Document ID
        """
        data = {
            "session_id": session_id,
            "contract_id": contract_id,
            "document_type": document_type,
            "title": title,
            "file_url": file_url,
            "content_summary": content_summary,
        }
        
        return await self.create_document(self.DOCUMENTS, data)
    
    async def list_documents(
        self,
        session_id: Optional[str] = None,
        contract_id: Optional[str] = None,
        document_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List generated documents."""
        filters = []
        if session_id:
            filters.append(("session_id", "==", session_id))
        if contract_id:
            filters.append(("contract_id", "==", contract_id))
        if document_type:
            filters.append(("document_type", "==", document_type))
        
        return await self.query_documents(
            self.DOCUMENTS,
            filters=filters if filters else None,
            order_by="created_at",
            limit=limit
        )
    
    # =========================================================================
    # Cleanup Operations
    # =========================================================================
    
    async def cleanup_old_sessions(self, days_old: int = 7) -> int:
        """Delete sessions older than specified days.
        
        Args:
            days_old: Delete sessions older than this many days
            
        Returns:
            Number of deleted sessions
        """
        cutoff = datetime.utcnow() - timedelta(days=days_old)
        
        # Query old sessions
        old_sessions = await self.query_documents(
            self.SESSIONS,
            filters=[("last_activity", "<", cutoff)],
            limit=500
        )
        
        count = 0
        for session in old_sessions:
            await self.delete_document(self.SESSIONS, session["id"])
            count += 1
        
        return count


# Create singleton instance
@lru_cache()
def get_firestore_service() -> FirestoreService:
    """Get the singleton Firestore service instance."""
    return FirestoreService()
