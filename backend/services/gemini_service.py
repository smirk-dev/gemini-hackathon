"""
Gemini Service
Handles all interactions with the Google Gemini API.
"""

import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse
from typing import Dict, List, Any, Optional, Callable
import json
import asyncio
from functools import lru_cache

from config.settings import get_settings, get_gemini_api_key


def _convert_json_schema_to_gemini(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Convert JSON Schema format to Gemini's expected schema format.
    
    Args:
        schema: JSON Schema dict
        
    Returns:
        Gemini-compatible schema dict
    """
    if not isinstance(schema, dict):
        return schema
    
    result = {}
    
    # Convert type field from string to Type enum
    if "type" in schema:
        type_str = schema["type"]
        # Map JSON Schema types to Gemini Type enum values
        type_mapping = {
            "object": "OBJECT",
            "string": "STRING",
            "number": "NUMBER",
            "integer": "INTEGER",
            "boolean": "BOOLEAN",
            "array": "ARRAY",
        }
        result["type_"] = type_mapping.get(type_str, "STRING")
    
    # Copy other fields, converting recursively
    for key, value in schema.items():
        if key == "type":
            continue  # Already handled
        elif key == "properties" and isinstance(value, dict):
            result["properties"] = {
                k: _convert_json_schema_to_gemini(v)
                for k, v in value.items()
            }
        elif key == "items" and isinstance(value, dict):
            result["items"] = _convert_json_schema_to_gemini(value)
        elif key in ["description", "enum", "required", "format"]:
            result[key] = value
    
    return result


def _convert_json_schema_to_vertex(schema: Dict[str, Any]):
    """Convert JSON Schema format to Vertex AI Schema objects."""
    if not isinstance(schema, dict):
        return schema

    try:
        from vertexai.generative_models import Schema, Type
    except ImportError:
        return None

    type_mapping = {
        "object": Type.OBJECT,
        "string": Type.STRING,
        "number": Type.NUMBER,
        "integer": Type.INTEGER,
        "boolean": Type.BOOLEAN,
        "array": Type.ARRAY,
    }

    schema_type = type_mapping.get(schema.get("type", "string"), Type.STRING)
    properties = None
    items = None

    if schema.get("properties") and isinstance(schema["properties"], dict):
        properties = {
            k: _convert_json_schema_to_vertex(v)
            for k, v in schema["properties"].items()
        }

    if schema.get("items") and isinstance(schema["items"], dict):
        items = _convert_json_schema_to_vertex(schema["items"])

    return Schema(
        type_=schema_type,
        description=schema.get("description"),
        properties=properties,
        items=items,
        required=schema.get("required"),
        enum=schema.get("enum"),
    )


def _build_vertex_tools(tools: List[Dict[str, Any]]):
    """Build Vertex AI Tool objects from tool definitions."""
    try:
        from vertexai.generative_models import Tool, FunctionDeclaration
    except ImportError:
        return []

    vertex_tools = []
    for tool in tools:
        parameters = None
        if "parameters" in tool:
            parameters = _convert_json_schema_to_vertex(tool["parameters"])
            if parameters is None:
                return []

        func_decl = FunctionDeclaration(
            name=tool["name"],
            description=tool.get("description"),
            parameters=parameters,
        )
        vertex_tools.append(Tool(function_declarations=[func_decl]))

    return vertex_tools


class GeminiService:
    """Service for interacting with the Gemini API."""
    
    def __init__(self):
        """Initialize the Gemini service."""
        self.settings = get_settings()
        self._configure_api()
        self._model = None
        self._tools: Dict[str, Callable] = {}
        self._tool_declarations: List[Dict] = []
        self.use_vertex = self.settings.use_vertex_ai
    
    def _configure_api(self):
        """Configure the Gemini API with credentials."""
        if self.settings.use_vertex_ai:
            import vertexai
            vertexai.init(project=self.settings.google_cloud_project, location="us-central1")
            print(f"✅ Using Vertex AI (project: {self.settings.google_cloud_project})")
        else:
            api_key = get_gemini_api_key()
            if api_key:
                genai.configure(api_key=api_key)
                print("✅ Using AI Studio with API key")
    
    @property
    def model(self):
        """Get or create the Gemini model instance."""
        if self._model is None:
            # Build generation config
            generation_config = genai.GenerationConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
            )
            
            # Create model with tools if registered
            model_kwargs = {
                "model_name": self.settings.gemini_model,
                "generation_config": generation_config,
            }
            
            # Add tools if any registered
            if self._tool_declarations:
                if self.use_vertex:
                    model_kwargs["tools"] = _build_vertex_tools(self._tool_declarations)
                else:
                    model_kwargs["tools"] = self._tool_declarations
            
            # Add Google Search grounding if enabled
            if self.settings.enable_search_grounding:
                if self.use_vertex:
                    from vertexai.generative_models import Tool
                    google_search = Tool.from_google_search_retrieval()
                else:
                    from google.generativeai.types import Tool
                    google_search = Tool.from_google_search_retrieval()

                if "tools" in model_kwargs:
                    model_kwargs["tools"].append(google_search)
                else:
                    model_kwargs["tools"] = [google_search]
            
            if self.use_vertex:
                from vertexai.generative_models import GenerativeModel
                self._model = GenerativeModel(**model_kwargs)
            else:
                if self.use_vertex:
                    from vertexai.generative_models import GenerativeModel
                    self._model = GenerativeModel(**model_kwargs)
                else:
                    self._model = genai.GenerativeModel(**model_kwargs)
        
        return self._model
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable
    ):
        """Register a tool/function for the model to call.
        
        Args:
            name: The tool name
            description: Description of what the tool does
            parameters: JSON schema for tool parameters
            handler: The function to call when tool is invoked
        """
        self._tools[name] = handler
        
        # Create function declaration for Gemini
        function_declaration = {
            "name": name,
            "description": description,
            "parameters": parameters,
        }
        self._tool_declarations.append(function_declaration)
        
        # Reset model to include new tools
        self._model = None
    
    def register_tools_from_module(self, tool_definitions: List[Dict[str, Any]]):
        """Register multiple tools from a definitions list.
        
        Args:
            tool_definitions: List of tool definition dicts with
                name, description, parameters, and handler
        """
        for tool_def in tool_definitions:
            self.register_tool(
                name=tool_def["name"],
                description=tool_def["description"],
                parameters=tool_def["parameters"],
                handler=tool_def["handler"]
            )
    
    async def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        chat_history: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Generate content using Gemini.
        
        Args:
            prompt: The user prompt
            system_instruction: Optional system instruction
            chat_history: Optional conversation history
            temperature: Optional temperature override
            
        Returns:
            Dict with response text, citations, and metadata
        """
        try:
            # Create model with custom system instruction if provided
            if system_instruction:
                if self.use_vertex:
                    from vertexai.generative_models import GenerativeModel
                    tools = _build_vertex_tools(self._tool_declarations) if self._tool_declarations else None
                    model = GenerativeModel(
                        model_name=self.settings.gemini_model,
                        system_instruction=system_instruction,
                        tools=tools,
                    )
                else:
                    model = genai.GenerativeModel(
                        model_name=self.settings.gemini_model,
                        system_instruction=system_instruction,
                        tools=self._tool_declarations if self._tool_declarations else None,
                    )
            else:
                model = self.model
            
            # Build generation config with temperature override
            gen_config = None
            if temperature is not None:
                if self.use_vertex:
                    from vertexai.generative_models import GenerationConfig
                    gen_config = GenerationConfig(temperature=temperature)
                else:
                    gen_config = genai.GenerationConfig(temperature=temperature)
            
            # Handle chat vs single generation
            if chat_history:
                chat = model.start_chat(history=self._format_history(chat_history))
                response = await asyncio.to_thread(
                    chat.send_message,
                    prompt,
                    generation_config=gen_config
                )
            else:
                response = await asyncio.to_thread(
                    model.generate_content,
                    prompt,
                    generation_config=gen_config
                )
            
            # Process response and handle tool calls
            return await self._process_response(response, model, chat_history)
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "response": None,
                "citations": [],
            }
    
    async def _process_response(
        self,
        response: GenerateContentResponse,
        model: Any,
        chat_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Process Gemini response, handling function calls if needed.
        
        Args:
            response: The Gemini response
            model: The model instance (for follow-up calls)
            chat_history: Optional chat history
            
        Returns:
            Processed response dict
        """
        # Check for function calls
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    # Execute the function call
                    function_call = part.function_call
                    function_name = function_call.name
                    function_args = dict(function_call.args)
                    
                    if function_name in self._tools:
                        # Execute the tool
                        tool_result = await self._execute_tool(
                            function_name, 
                            function_args
                        )
                        
                        # Send function result back to model
                        function_response = genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=function_name,
                                response={"result": json.dumps(tool_result)}
                            )
                        )
                        
                        # Get follow-up response
                        follow_up = await asyncio.to_thread(
                            model.generate_content,
                            [response.candidates[0].content, function_response]
                        )
                        
                        return await self._process_response(
                            follow_up, model, chat_history
                        )
        
        # Extract text response
        response_text = ""
        if response.text:
            response_text = response.text
        
        # Extract citations if available
        citations = self._extract_citations(response)
        
        return {
            "status": "success",
            "response": response_text,
            "citations": citations,
            "usage": self._extract_usage(response),
        }
    
    async def _execute_tool(
        self,
        tool_name: str,
        args: Dict[str, Any]
    ) -> Any:
        """Execute a registered tool.
        
        Args:
            tool_name: Name of the tool to execute
            args: Arguments for the tool
            
        Returns:
            Tool execution result
        """
        handler = self._tools.get(tool_name)
        if handler is None:
            return {"error": f"Tool '{tool_name}' not found"}
        
        # Check if handler is async
        if asyncio.iscoroutinefunction(handler):
            return await handler(**args)
        else:
            return await asyncio.to_thread(handler, **args)
    
    def _format_history(self, chat_history: List[Dict]) -> List[Dict]:
        """Format chat history for Gemini.
        
        Args:
            chat_history: List of message dicts with role and content
            
        Returns:
            Formatted history for Gemini
        """
        formatted = []
        for msg in chat_history:
            role = "user" if msg.get("role") == "user" else "model"
            formatted.append({
                "role": role,
                "parts": [msg.get("content", "")]
            })
        return formatted
    
    def _extract_citations(self, response: GenerateContentResponse) -> List[Dict]:
        """Extract citations from grounding metadata.
        
        Args:
            response: The Gemini response
            
        Returns:
            List of citation dicts with title and uri
        """
        citations = []
        
        try:
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                
                # Check for grounding metadata
                if hasattr(candidate, 'grounding_metadata'):
                    metadata = candidate.grounding_metadata
                    
                    if hasattr(metadata, 'grounding_chunks'):
                        for chunk in metadata.grounding_chunks:
                            if hasattr(chunk, 'web'):
                                citations.append({
                                    "title": chunk.web.title if hasattr(chunk.web, 'title') else "",
                                    "uri": chunk.web.uri if hasattr(chunk.web, 'uri') else "",
                                })
        except Exception:
            pass  # Citations are optional, don't fail on errors
        
        return citations
    
    def _extract_usage(self, response: GenerateContentResponse) -> Dict[str, int]:
        """Extract token usage from response.
        
        Args:
            response: The Gemini response
            
        Returns:
            Dict with token counts
        """
        usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        
        try:
            if hasattr(response, 'usage_metadata'):
                metadata = response.usage_metadata
                usage["prompt_tokens"] = getattr(metadata, 'prompt_token_count', 0)
                usage["completion_tokens"] = getattr(metadata, 'candidates_token_count', 0)
                usage["total_tokens"] = getattr(metadata, 'total_token_count', 0)
        except Exception:
            pass
        
        return usage
    
    async def generate_with_tools(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        use_search_grounding: bool = False,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Generate content with tool calling support.
        
        Args:
            prompt: The user prompt
            system_instruction: Optional system instruction
            tools: Tool definitions (JSON Schema format)
            use_search_grounding: Whether to enable search grounding
            temperature: Optional temperature
            
        Returns:
            Response with text, function_calls, and citations
        """
        try:
            # Build generation config using appropriate SDK
            if self.use_vertex:
                from vertexai.generative_models import GenerationConfig
                gen_config = GenerationConfig(
                    temperature=temperature if temperature is not None else 0.7,
                )
            else:
                gen_config = genai.GenerationConfig(
                    temperature=temperature if temperature is not None else 0.7,
                )
            
            # Build model kwargs
            model_kwargs = {
                "model_name": self.settings.gemini_model,
                "generation_config": gen_config,
            }
            
            if system_instruction:
                model_kwargs["system_instruction"] = system_instruction
            
            # Convert tools to SDK-specific format
            model_tools = []
            if tools:
                if self.use_vertex:
                    model_tools = _build_vertex_tools(tools)
                else:
                    for tool in tools:
                        func_decl = {
                            "name": tool["name"],
                            "description": tool["description"],
                        }
                        if "parameters" in tool:
                            func_decl["parameters"] = _convert_json_schema_to_gemini(tool["parameters"])
                        model_tools.append(func_decl)
            
            if use_search_grounding:
                if self.use_vertex:
                    from vertexai.generative_models import Tool
                else:
                    from google.generativeai.types import Tool
                model_tools.append(Tool.from_google_search_retrieval())
            
            if model_tools:
                model_kwargs["tools"] = model_tools
            
            # Use appropriate SDK based on configuration
            if self.use_vertex:
                from vertexai.generative_models import GenerativeModel
                model = GenerativeModel(**model_kwargs)
            else:
                model = genai.GenerativeModel(**model_kwargs)
            
            # Generate content
            response = await asyncio.to_thread(
                model.generate_content,
                prompt
            )
            
            # Extract function calls
            function_calls = []
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        function_calls.append({
                            "name": fc.name,
                            "arguments": dict(fc.args) if fc.args else {},
                        })
            
            # Extract text
            text = response.text if hasattr(response, 'text') and response.text else ""
            
            # Extract citations
            citations = self._extract_citations(response)
            
            return {
                "text": text,
                "function_calls": function_calls,
                "citations": citations,
                "_response": response,  # Store for continuation
            }
            
        except Exception as e:
            print(f"Error in generate_with_tools: {e}")
            import traceback
            traceback.print_exc()
            return {
                "text": f"Error: {str(e)}",
                "function_calls": [],
                "citations": [],
            }
    
    async def continue_with_function_results(
        self,
        function_results: List[Dict[str, Any]],
        system_instruction: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Continue conversation with function call results.
        
        Args:
            function_results: List of dicts with 'name' and 'result'
            system_instruction: System instruction
            tools: Tool definitions (JSON Schema format)
            
        Returns:
            Response with text, function_calls, citations
        """
        try:
            # Build generation config using appropriate SDK
            if self.use_vertex:
                from vertexai.generative_models import GenerationConfig
                gen_config = GenerationConfig(temperature=0.7)
            else:
                gen_config = genai.GenerationConfig(temperature=0.7)
            
            # Build model
            model_kwargs = {
                "model_name": self.settings.gemini_model,
                "generation_config": gen_config,
            }
            
            if system_instruction:
                model_kwargs["system_instruction"] = system_instruction
            
            # Convert tools to SDK-specific format
            if tools:
                if self.use_vertex:
                    model_kwargs["tools"] = _build_vertex_tools(tools)
                else:
                    model_tools = []
                    for tool in tools:
                        func_decl = {
                            "name": tool["name"],
                            "description": tool["description"],
                        }
                        if "parameters" in tool:
                            func_decl["parameters"] = _convert_json_schema_to_gemini(tool["parameters"])
                        model_tools.append(func_decl)
                    model_kwargs["tools"] = model_tools
            
            if self.use_vertex:
                from vertexai.generative_models import GenerativeModel
                model = GenerativeModel(**model_kwargs)
            else:
                model = genai.GenerativeModel(**model_kwargs)
            
            # Build function response parts
            response_parts = []
            for fr in function_results:
                if self.use_vertex:
                    from vertexai.generative_models import Part, FunctionResponse
                    response_parts.append(
                        Part.from_function_response(
                            name=fr["name"],
                            response={"result": json.dumps(fr["result"])}
                        )
                    )
                else:
                    response_parts.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=fr["name"],
                                response={"result": json.dumps(fr["result"])}
                            )
                        )
                    )
            
            # Generate follow-up
            response = await asyncio.to_thread(
                model.generate_content,
                response_parts
            )
            
            # Extract function calls
            function_calls = []
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        function_calls.append({
                            "name": fc.name,
                            "arguments": dict(fc.args) if fc.args else {},
                        })
            
            # Extract text
            text = response.text if hasattr(response, 'text') and response.text else ""
            
            # Extract citations
            citations = self._extract_citations(response)
            
            return {
                "text": text,
                "function_calls": function_calls,
                "citations": citations,
            }
            
        except Exception as e:
            print(f"Error in continue_with_function_results: {e}")
            import traceback
            traceback.print_exc()
            return {
                "text": f"Error: {str(e)}",
                "function_calls": [],
                "citations": [],
            }
    
    async def generate_structured_output(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        system_instruction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate structured JSON output using response schema.
        
        Args:
            prompt: The user prompt
            response_schema: JSON schema for the expected response
            system_instruction: Optional system instruction
            
        Returns:
            Parsed JSON response
        """
        try:
            if self.use_vertex:
                from vertexai.generative_models import GenerationConfig
                generation_config = GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                )
            else:
                generation_config = genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                )
            
            if self.use_vertex:
                from vertexai.generative_models import GenerativeModel
                model = GenerativeModel(
                    model_name=self.settings.gemini_model,
                    system_instruction=system_instruction,
                    generation_config=generation_config,
                )
            else:
                model = genai.GenerativeModel(
                    model_name=self.settings.gemini_model,
                    system_instruction=system_instruction,
                    generation_config=generation_config,
                )
            
            response = await asyncio.to_thread(
                model.generate_content,
                prompt
            )
            
            # Parse JSON response
            if response.text:
                return {
                    "status": "success",
                    "data": json.loads(response.text),
                }
            
            return {
                "status": "error",
                "error": "No response generated",
            }
            
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "error": f"Failed to parse JSON response: {e}",
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }
    
    async def analyze_document(
        self,
        content: str,
        analysis_type: str,
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze a document with specific analysis type.
        
        Args:
            content: The document content
            analysis_type: Type of analysis (e.g., 'contract', 'risk', 'compliance')
            additional_context: Optional additional context
            
        Returns:
            Analysis results
        """
        prompts = {
            "contract": """Analyze this contract and extract:
                1. Contract type
                2. Parties involved
                3. Key terms and dates
                4. Obligations for each party
                5. Termination conditions
                
                Contract content:
                {content}
                
                {additional_context}
                
                Provide a structured analysis.""",
            
            "risk": """Analyze this document for legal risks:
                1. Identify potentially problematic clauses
                2. Flag ambiguous language
                3. Note missing standard protections
                4. Assess liability exposure
                5. Rate each risk (low/medium/high/critical)
                
                Document content:
                {content}
                
                {additional_context}
                
                Provide detailed risk assessment.""",
            
            "compliance": """Analyze this document for regulatory compliance:
                1. Check GDPR compliance (if applicable)
                2. Check industry-specific regulations
                3. Identify non-compliant sections
                4. Recommend changes for compliance
                
                Document content:
                {content}
                
                {additional_context}
                
                Provide compliance assessment.""",
        }
        
        prompt_template = prompts.get(analysis_type, prompts["contract"])
        prompt = prompt_template.format(
            content=content,
            additional_context=additional_context or ""
        )
        
        return await self.generate_content(prompt)


# Create singleton instance
@lru_cache()
def get_gemini_service() -> GeminiService:
    """Get the singleton Gemini service instance."""
    return GeminiService()
