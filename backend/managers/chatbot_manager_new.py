"""
LegalMind Chatbot Manager
Manages chat sessions and agent interactions using Google Gemini.
"""

import uuid
import asyncio
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional

from config.settings import get_settings
from services.gemini_service import GeminiService
from services.firestore_service import FirestoreService
from services.storage_service import StorageService
from agents.agent_definitions_new import (
    CONTRACT_PARSER_AGENT,
    LEGAL_RESEARCH_AGENT,
    COMPLIANCE_CHECKER_AGENT,
    RISK_ASSESSMENT_AGENT,
    LEGAL_MEMO_AGENT,
    ASSISTANT_AGENT,
    get_agent_config,
    get_agent_instructions,
    AGENT_CONFIGS,
)
from agents.agent_strategies_new import (
    select_agent,
    get_agent_sequence,
    AgentOrchestrator,
    should_handoff,
)
from tools.contract_tools import (
    get_contract,
    list_contracts,
    extract_contract_text,
    update_contract_metadata,
    search_contracts,
    TOOL_DEFINITIONS as CONTRACT_TOOL_DEFINITIONS,
)
from tools.clause_tools import (
    extract_clauses,
    get_clause,
    get_contract_clauses,
    update_clause_analysis,
    find_similar_clauses,
    TOOL_DEFINITIONS as CLAUSE_TOOL_DEFINITIONS,
)
from tools.compliance_tools import (
    check_compliance,
    get_compliance_requirements,
    list_compliance_frameworks,
    check_specific_requirement,
    get_compliance_recommendations,
    TOOL_DEFINITIONS as COMPLIANCE_TOOL_DEFINITIONS,
)
from tools.risk_tools import (
    assess_contract_risk,
    assess_clause_risk,
    get_contract_risk_summary,
    compare_contract_risks,
    TOOL_DEFINITIONS as RISK_TOOL_DEFINITIONS,
)
from tools.document_tools import (
    generate_legal_memo,
    generate_contract_summary,
    generate_risk_report,
    list_generated_documents,
    TOOL_DEFINITIONS as DOCUMENT_TOOL_DEFINITIONS,
)
from tools.logging_tools import (
    ThinkingLogger,
    log_thinking,
    get_thinking_logs,
    get_session_trace,
    TOOL_DEFINITIONS as LOGGING_TOOL_DEFINITIONS,
)

# Load environment variables
load_dotenv()


class ChatbotManager:
    """Manages interactive chat sessions with LegalMind agents."""
    
    def __init__(self):
        """Initialize the chatbot manager."""
        self.settings = get_settings()
        
        # Initialize services
        self.gemini = GeminiService()
        self.firestore = FirestoreService()
        self.storage = StorageService()
        
        # Initialize thinking logger
        self.thinking_logger = ThinkingLogger()
        
        # Session management
        self.chat_sessions: Dict[str, Dict[str, Any]] = {}
        self._session_lock = asyncio.Lock()
        self._processing_locks: Dict[str, asyncio.Lock] = {}
        
        # Build tool registry
        self._build_tool_registry()
        
        print("ChatbotManager initialized successfully")
    
    def _build_tool_registry(self):
        """Build the registry of available tools and their handlers."""
        self.tool_handlers = {
            # Contract tools
            "get_contract": get_contract,
            "list_contracts": list_contracts,
            "extract_contract_text": extract_contract_text,
            "update_contract_metadata": update_contract_metadata,
            "search_contracts": search_contracts,
            # Clause tools
            "extract_clauses": extract_clauses,
            "get_clause": get_clause,
            "get_contract_clauses": get_contract_clauses,
            "update_clause_analysis": update_clause_analysis,
            "find_similar_clauses": find_similar_clauses,
            # Compliance tools
            "check_compliance": check_compliance,
            "get_compliance_requirements": get_compliance_requirements,
            "list_compliance_frameworks": list_compliance_frameworks,
            "check_specific_requirement": check_specific_requirement,
            "get_compliance_recommendations": get_compliance_recommendations,
            # Risk tools
            "assess_contract_risk": assess_contract_risk,
            "assess_clause_risk": assess_clause_risk,
            "get_contract_risk_summary": get_contract_risk_summary,
            "compare_contract_risks": compare_contract_risks,
            # Document tools
            "generate_legal_memo": generate_legal_memo,
            "generate_contract_summary": generate_contract_summary,
            "generate_risk_report": generate_risk_report,
            "list_generated_documents": list_generated_documents,
            # Logging tools
            "log_thinking": log_thinking,
            "get_thinking_logs": get_thinking_logs,
            "get_session_trace": get_session_trace,
        }
        
        # Map tool groups to definitions
        self.tool_definitions = {
            "contract_tools": CONTRACT_TOOL_DEFINITIONS,
            "clause_tools": CLAUSE_TOOL_DEFINITIONS,
            "compliance_tools": COMPLIANCE_TOOL_DEFINITIONS,
            "risk_tools": RISK_TOOL_DEFINITIONS,
            "document_tools": DOCUMENT_TOOL_DEFINITIONS,
            "logging_tools": LOGGING_TOOL_DEFINITIONS,
        }
    
    def _get_tools_for_agent(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get tool definitions for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            List of tool definitions
        """
        config = get_agent_config(agent_name)
        tool_groups = config.get("tools", [])
        
        tools = []
        for group in tool_groups:
            if group == "search_grounding":
                # Search grounding is handled separately by Gemini
                continue
            if group in self.tool_definitions:
                tools.extend(self.tool_definitions[group])
        
        return tools
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool by name with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        handler = self.tool_handlers.get(tool_name)
        if not handler:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            # Most handlers are async
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**arguments)
            else:
                result = handler(**arguments)
            return result
        except Exception as e:
            print(f"Error executing tool {tool_name}: {e}")
            return {"error": str(e)}
    
    async def initialize_session(self, session_id: str) -> Dict[str, Any]:
        """Initialize or retrieve a chat session.
        
        Args:
            session_id: The session ID
            
        Returns:
            Session data dictionary
        """
        # Check if session exists
        if session_id in self.chat_sessions:
            session = self.chat_sessions[session_id]
            session["last_activity"] = datetime.now()
            return session
        
        async with self._session_lock:
            # Double-check after acquiring lock
            if session_id in self.chat_sessions:
                return self.chat_sessions[session_id]
            
            print(f"Creating new session: {session_id}")
            
            # Create session in Firestore
            session_data = {
                "id": session_id,
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "message_count": 0,
                "active_contract_id": None,
            }
            await self.firestore.create_session(session_id, session_data)
            
            # Local session state
            session = {
                "id": session_id,
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
                "messages": [],
                "active_contract_id": None,
                "orchestrator": AgentOrchestrator(),
                "current_agent": ASSISTANT_AGENT,
            }
            
            self.chat_sessions[session_id] = session
            self._processing_locks[session_id] = asyncio.Lock()
            
            return session
    
    async def process_message(
        self,
        session_id: str,
        user_message: str,
        contract_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process a user message and return the agent response.
        
        Args:
            session_id: The session ID
            user_message: The user's message
            contract_id: Optional contract ID for context
            
        Returns:
            Response dictionary with agent message and metadata
        """
        # Initialize or get session
        session = await self.initialize_session(session_id)
        
        # Get processing lock for this session
        if session_id not in self._processing_locks:
            self._processing_locks[session_id] = asyncio.Lock()
        
        async with self._processing_locks[session_id]:
            try:
                return await self._process_message_internal(
                    session, user_message, contract_id
                )
            except Exception as e:
                print(f"Error processing message: {e}")
                import traceback
                traceback.print_exc()
                return {
                    "success": False,
                    "error": str(e),
                    "message": "I encountered an error processing your request. Please try again.",
                }
    
    async def _process_message_internal(
        self,
        session: Dict[str, Any],
        user_message: str,
        contract_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Internal message processing logic.
        
        Args:
            session: Session data
            user_message: User's message
            contract_id: Optional contract ID
            
        Returns:
            Response dictionary
        """
        session_id = session["id"]
        
        # Update contract context if provided
        if contract_id:
            session["active_contract_id"] = contract_id
        
        # Store user message
        message_id = str(uuid.uuid4())
        user_msg_data = {
            "id": message_id,
            "session_id": session_id,
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat(),
        }
        await self.firestore.add_message(session_id, user_msg_data)
        session["messages"].append(user_msg_data)
        
        # Select agent based on query
        selection = select_agent(user_message, {
            "contract_id": session.get("active_contract_id"),
            "history": session["messages"],
        })
        
        agent_name = selection.agent_name
        print(f"Selected agent: {agent_name} (confidence: {selection.confidence:.2f})")
        
        # Log thinking
        await self.thinking_logger.log_thinking(
            session_id=session_id,
            agent_name=agent_name,
            thinking=f"Selected agent based on query classification: {selection.reason}",
        )
        
        # Get agent configuration
        agent_config = get_agent_config(agent_name)
        tools = self._get_tools_for_agent(agent_name)
        
        # Build context
        context = await self._build_context(session, user_message)
        
        # Determine if we need search grounding
        use_search = "search_grounding" in agent_config.get("tools", [])
        
        # Call Gemini
        response = await self._call_agent(
            agent_name=agent_name,
            instructions=agent_config["instructions"],
            user_message=user_message,
            context=context,
            tools=tools,
            use_search=use_search,
            session_id=session_id,
            temperature=agent_config.get("temperature", 0.5),
        )
        
        # Store assistant message
        assistant_msg_data = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "role": "assistant",
            "agent": agent_name,
            "content": response["message"],
            "timestamp": datetime.now().isoformat(),
            "citations": response.get("citations", []),
        }
        await self.firestore.add_message(session_id, assistant_msg_data)
        session["messages"].append(assistant_msg_data)
        
        # Update session
        session["last_activity"] = datetime.now()
        session["current_agent"] = agent_name
        
        return {
            "success": True,
            "message": response["message"],
            "agent": agent_config["name"],
            "agent_id": agent_name,
            "citations": response.get("citations", []),
            "tools_used": response.get("tools_used", []),
            "session_id": session_id,
        }
    
    async def _build_context(
        self,
        session: Dict[str, Any],
        user_message: str,
    ) -> str:
        """Build context string for the agent.
        
        Args:
            session: Session data
            user_message: Current user message
            
        Returns:
            Context string
        """
        context_parts = []
        
        # Add active contract context
        if session.get("active_contract_id"):
            contract = await self.firestore.get_contract(session["active_contract_id"])
            if contract:
                context_parts.append(f"Active Contract: {contract.get('name', 'Unknown')}")
                context_parts.append(f"Contract Type: {contract.get('type', 'Unknown')}")
                if contract.get("parties"):
                    context_parts.append(f"Parties: {', '.join(contract['parties'])}")
        
        # Add recent conversation history (last 5 messages)
        recent_messages = session.get("messages", [])[-10:]
        if recent_messages:
            context_parts.append("\nRecent Conversation:")
            for msg in recent_messages:
                role = "User" if msg["role"] == "user" else "Assistant"
                content = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
                context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    async def _call_agent(
        self,
        agent_name: str,
        instructions: str,
        user_message: str,
        context: str,
        tools: List[Dict[str, Any]],
        use_search: bool,
        session_id: str,
        temperature: float = 0.5,
    ) -> Dict[str, Any]:
        """Call an agent with the Gemini API.
        
        Args:
            agent_name: Name of the agent
            instructions: Agent instructions
            user_message: User's message
            context: Context string
            tools: Tool definitions
            use_search: Whether to use search grounding
            session_id: Session ID for logging
            temperature: Model temperature
            
        Returns:
            Response dictionary with message and metadata
        """
        # Build the system prompt
        system_prompt = f"""{instructions}

## Current Context
{context}
"""
        
        # Log thinking
        await self.thinking_logger.log_thinking(
            session_id=session_id,
            agent_name=agent_name,
            thinking=f"Processing user query with {len(tools)} available tools. Search grounding: {use_search}",
        )
        
        try:
            # Call Gemini with function calling
            response = await self.gemini.generate_with_tools(
                prompt=user_message,
                system_instruction=system_prompt,
                tools=tools if tools else None,
                use_search_grounding=use_search,
                temperature=temperature,
            )
            
            # Process function calls if any
            tools_used = []
            final_response = response
            
            # Handle function calling loop
            max_iterations = 5
            iteration = 0
            
            while response.get("function_calls") and iteration < max_iterations:
                iteration += 1
                function_calls = response["function_calls"]
                
                # Execute each function call
                function_results = []
                for fc in function_calls:
                    tool_name = fc["name"]
                    arguments = fc.get("arguments", {})
                    
                    print(f"Executing tool: {tool_name}")
                    tools_used.append(tool_name)
                    
                    # Log tool execution
                    await self.thinking_logger.log_thinking(
                        session_id=session_id,
                        agent_name=agent_name,
                        thinking=f"Executing tool: {tool_name} with args: {json.dumps(arguments)[:200]}",
                    )
                    
                    # Execute the tool
                    result = await self._execute_tool(tool_name, arguments)
                    function_results.append({
                        "name": tool_name,
                        "result": result,
                    })
                
                # Continue conversation with function results
                response = await self.gemini.continue_with_function_results(
                    function_results=function_results,
                    system_instruction=system_prompt,
                    tools=tools,
                )
                
                if response.get("text"):
                    final_response = response
            
            # Extract final text and citations
            message_text = final_response.get("text", "I'm sorry, I couldn't generate a response.")
            citations = final_response.get("citations", [])
            
            return {
                "message": message_text,
                "citations": citations,
                "tools_used": tools_used,
            }
            
        except Exception as e:
            print(f"Error calling agent {agent_name}: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "message": f"I encountered an error while processing your request: {str(e)}",
                "citations": [],
                "tools_used": [],
            }
    
    async def run_workflow(
        self,
        session_id: str,
        workflow_name: str,
        contract_id: str,
    ) -> Dict[str, Any]:
        """Run a predefined workflow on a contract.
        
        Args:
            session_id: Session ID
            workflow_name: Name of the workflow template
            contract_id: Contract to analyze
            
        Returns:
            Workflow results
        """
        from agents.agent_strategies_new import get_workflow_template
        
        template = get_workflow_template(workflow_name)
        if not template:
            return {"success": False, "error": f"Unknown workflow: {workflow_name}"}
        
        session = await self.initialize_session(session_id)
        session["active_contract_id"] = contract_id
        
        results = {}
        messages = []
        
        for agent_name in template["agents"]:
            agent_config = get_agent_config(agent_name)
            tools = self._get_tools_for_agent(agent_name)
            
            # Build workflow prompt
            prompt = f"Analyze the contract with ID {contract_id} for your specific purpose."
            context = await self._build_context(session, prompt)
            
            response = await self._call_agent(
                agent_name=agent_name,
                instructions=agent_config["instructions"],
                user_message=prompt,
                context=context,
                tools=tools,
                use_search="search_grounding" in agent_config.get("tools", []),
                session_id=session_id,
                temperature=agent_config.get("temperature", 0.5),
            )
            
            results[agent_name] = response
            messages.append({
                "agent": agent_config["name"],
                "content": response["message"],
            })
        
        return {
            "success": True,
            "workflow": workflow_name,
            "contract_id": contract_id,
            "results": results,
            "messages": messages,
        }
    
    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get the message history for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of messages
        """
        messages = await self.firestore.get_session_messages(session_id)
        return messages
    
    async def close_session(self, session_id: str):
        """Close and clean up a session.
        
        Args:
            session_id: Session ID to close
        """
        async with self._session_lock:
            if session_id in self.chat_sessions:
                del self.chat_sessions[session_id]
            if session_id in self._processing_locks:
                del self._processing_locks[session_id]
        
        print(f"Session {session_id} closed")
    
    async def cleanup_old_sessions(self, max_age_minutes: int = 60):
        """Clean up sessions older than the specified age.
        
        Args:
            max_age_minutes: Maximum session age in minutes
        """
        now = datetime.now()
        sessions_to_remove = []
        
        for session_id, session in self.chat_sessions.items():
            last_activity = session.get("last_activity")
            if last_activity:
                age = (now - last_activity).total_seconds() / 60
                if age > max_age_minutes:
                    sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            await self.close_session(session_id)
        
        if sessions_to_remove:
            print(f"Cleaned up {len(sessions_to_remove)} old sessions")


# Global instance
_chatbot_manager: Optional[ChatbotManager] = None


def get_chatbot_manager() -> ChatbotManager:
    """Get or create the global ChatbotManager instance.
    
    Returns:
        ChatbotManager instance
    """
    global _chatbot_manager
    if _chatbot_manager is None:
        _chatbot_manager = ChatbotManager()
    return _chatbot_manager
