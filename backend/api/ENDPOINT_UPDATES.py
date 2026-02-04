"""
Chat Endpoint Updates with Timeout & Error Handling
Apply these patches to endpoints_new.py
"""

# Add these imports at the top of backend/api/endpoints_new.py (after existing imports):
# from utils.request_helpers import with_timeout
# import logging
# logger = logging.getLogger(__name__)

# Replace the @router.post("/chat") endpoint with this improved version:

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

        cache_key = _get_cache_key(request)
        cached = _get_cached_response(cache_key)
        if cached:
            return ChatResponse(**cached)

        chatbot = get_chatbot_manager()
        
        # Add timeout of 30 seconds for chat processing
        try:
            response = await asyncio.wait_for(
                chatbot.process_message(
                    session_id=request.session_id,
                    user_message=request.message,
                    contract_id=request.contract_id,
                ),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            logger.error(f"Chat request timed out for session {request.session_id}")
            raise HTTPException(
                status_code=504,
                detail="Request timeout - the analysis took too long. Please try again."
            )
        
        if response.get("success"):
            _set_cached_response(cache_key, response)
        return ChatResponse(**response)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your message. Please try again."
        )


# For the @router.post("/chat/session") endpoint, add timeout too:

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
        
        try:
            await asyncio.wait_for(
                chatbot.initialize_session(session_id),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            logger.warning(f"Session initialization timed out for {session_id}")
            # Return response anyway - session exists locally even if Firestore write timed out
        
        return {
            "success": True,
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to create session. Please try again."
        )
