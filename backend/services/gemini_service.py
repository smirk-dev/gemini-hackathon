"""
Gemini Service - Vertex AI Only
Handles all interactions with Google Vertex AI Generative Models.
IMPORTANT: This service ONLY uses Vertex AI, not the public Gemini API.
"""

import vertexai
from vertexai.generative_models import (
    GenerativeModel,
    GenerationConfig,
    Tool,
    FunctionDeclaration,
    Part,
)

# GoogleSearchRetrieval was removed / renamed in newer SDK versions
try:
    from vertexai.generative_models import GoogleSearchRetrieval
except ImportError:
    GoogleSearchRetrieval = None

# Handle version compatibility for Type and Schema
try:
    from vertexai.generative_models import Type, Schema
except ImportError:
    try:
        # Try alternate import path
        from vertexai.generative_models.types import Type, Schema
    except (ImportError, AttributeError):
        # Fallback: use google-genai types if available
        try:
            from google.genai.types import Type, Schema
        except (ImportError, AttributeError):
            # Final fallback: create placeholder types
            class Type:
                OBJECT = "object"
                STRING = "string"
                NUMBER = "number"
                INTEGER = "integer"
                BOOLEAN = "boolean"
                ARRAY = "array"

            class Schema:
                def __init__(self, **kwargs):
                    for k, v in kwargs.items():
                        setattr(self, k, v)
from typing import Dict, List, Any, Optional, Callable
import json
import asyncio
import os
from functools import lru_cache

from config.settings import get_settings


# ============================================================================
# Schema Conversion Helpers
# ============================================================================

def _convert_json_schema_to_vertex(schema: Dict[str, Any]) -> Optional[Schema]:
    """Convert JSON Schema format to Vertex AI Schema objects."""
    if not isinstance(schema, dict):
        return schema

    type_mapping = {
        "object": Type.OBJECT,
        "string": Type.STRING,
        "number": Type.NUMBER,
        "integer": Type.INTEGER,
        "boolean": Type.BOOLEAN,
        "array": Type.ARRAY,
    }

    try:
        schema_type = type_mapping.get(schema.get("type", "string"), Type.STRING)
        properties = None
        items = None

        if schema.get("properties") and isinstance(schema["properties"], dict):
            properties = {}
            for k, v in schema["properties"].items():
                if v is not None and isinstance(v, dict):
                    converted = _convert_json_schema_to_vertex(v)
                    if converted is not None:
                        properties[k] = converted
            if not properties:
                properties = None

        if schema.get("items") and isinstance(schema["items"], dict):
            items = _convert_json_schema_to_vertex(schema["items"])

        # Build kwargs dict, only including non-None values to avoid
        # pydantic "extra inputs" validation errors in newer SDK versions
        kwargs: Dict[str, Any] = {"type_": schema_type}
        if schema.get("description"):
            kwargs["description"] = schema["description"]
        if properties is not None:
            kwargs["properties"] = properties
        if items is not None:
            kwargs["items"] = items
        if schema.get("required"):
            kwargs["required"] = schema["required"]
        if schema.get("enum"):
            kwargs["enum"] = schema["enum"]

        return Schema(**kwargs)
    except Exception as e:
        print(f"⚠️ Error converting schema for Vertex AI: {e}")
        import traceback
        traceback.print_exc()
        return None


def _build_vertex_tools(tools: List[Dict[str, Any]]) -> List[Tool]:
    """Build Vertex AI Tool objects from tool definitions.
    
    Args:
        tools: List of tool definitions
        
    Returns:
        List of Vertex AI Tool objects
    """
    try:
        vertex_tools = []
        for tool in tools:
            parameters = None
            if "parameters" in tool:
                parameters = _convert_json_schema_to_vertex(tool["parameters"])
                if parameters is None:
                    # Schema conversion failed, skip this tool
                    print(f"⚠️ Skipping tool {tool['name']} due to schema conversion error")
                    continue

            func_decl = FunctionDeclaration(
                name=tool["name"],
                description=tool.get("description"),
                parameters=parameters,
            )
            vertex_tools.append(Tool(function_declarations=[func_decl]))

        return vertex_tools
    except Exception as e:
        print(f"❌ Error building Vertex AI tools: {e}")
        return []


class GeminiService:
    """Service for interacting with Google Vertex AI Generative Models.
    
    This service EXCLUSIVELY uses Vertex AI and does NOT fall back to the public Gemini API.
    All requests are authenticated via service account credentials.
    """
    
    def __init__(self):
        """Initialize the Gemini service with Vertex AI."""
        self.settings = get_settings()
        print(f"🔍 GeminiService: Initializing with Vertex AI only")
        print(f"   Project: {self.settings.google_cloud_project}")
        print(f"   Model: {self.settings.gemini_model}")
        
        try:
            vertexai.init(
                project=self.settings.google_cloud_project,
                location="us-central1"
            )
            print(f"✅ Vertex AI initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Vertex AI: {e}")
            raise RuntimeError(
                f"Vertex AI initialization failed: {e}. "
                "Ensure the service account has 'roles/aiplatform.user' permission "
                "and GOOGLE_CLOUD_PROJECT environment variable is set."
            ) from e
        
        self._model = None
        self._tools: Dict[str, Callable] = {}
        self._tool_declarations: List[Dict] = []
    
    @property
    def model(self) -> GenerativeModel:
        """Get or create the Vertex AI GenerativeModel instance.
        
        Returns:
            Initialized GenerativeModel instance
        """
        if self._model is None:
            # Build generation config for Vertex AI
            generation_config = GenerationConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
            )
            
            # Create model kwargs
            model_kwargs = {
                "model_name": self.settings.gemini_model,
                "generation_config": generation_config,
            }
            
            # Add tools if registered
            if self._tool_declarations:
                vertex_tools = _build_vertex_tools(self._tool_declarations)
                if vertex_tools:
                    model_kwargs["tools"] = vertex_tools
            
            # Create and cache the model
            self._model = GenerativeModel(**model_kwargs)
            print(f"✅ GenerativeModel created and cached")
        
        return self._model
    
    def register_tool(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a tool function with the service.
        
        Args:
            func: The callable function to register
            name: Tool name (defaults to function name)
            description: Tool description
            parameters: JSON Schema for tool parameters
        """
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"Tool: {tool_name}"
        
        # Store function reference
        self._tools[tool_name] = func
        
        # Register tool declaration for model
        tool_declaration = {
            "name": tool_name,
            "description": tool_description,
        }
        
        if parameters:
            tool_declaration["parameters"] = parameters
        
        self._tool_declarations.append(tool_declaration)
        print(f"✅ Tool registered: {tool_name}")
        
        # Reset cached model to rebuild with new tool
        self._model = None
    
    async def generate_text(self, prompt: str, temperature: Optional[float] = None) -> str:
        """Generate text response from Vertex AI.
        
        Args:
            prompt: Input prompt
            temperature: Optional temperature override (0.0-1.0)
            
        Returns:
            Generated text response
        """
        try:
            # Get or create model
            model = self.model
            
            # Override temperature if provided
            if temperature is not None:
                generation_config = GenerationConfig(
                    temperature=temperature,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=8192,
                )
                model = GenerativeModel(
                    model_name=self.settings.gemini_model,
                    generation_config=generation_config,
                )
            
            # Generate content
            response = await asyncio.to_thread(
                model.generate_content,
                prompt
            )
            
            # Extract and return text
            if response.text:
                return response.text
            else:
                return "No response generated"
                
        except Exception as e:
            print(f"❌ Error in generate_text: {e}")
            raise
    
    async def generate_with_tools(
        self,
        prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        use_search_grounding: bool = False,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Generate response with tool use from Vertex AI.
        
        Args:
            prompt: Input prompt
            tools: Optional list of tool definitions
            use_search_grounding: Whether to enable Google Search grounding
            system_instruction: Optional system instruction for the model
            temperature: Temperature for generation (default 0.7)
            
        Returns:
            Dictionary with response data and tool calls
        """
        try:
            # Build model kwargs
            generation_config = GenerationConfig(
                temperature=temperature,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
            )
            
            model_kwargs = {
                "model_name": self.settings.gemini_model,
                "generation_config": generation_config,
            }
            
            # Add system instruction if provided
            if system_instruction:
                model_kwargs["system_instruction"] = system_instruction
            
            # Add tools
            model_tools = []
            if tools:
                model_tools = _build_vertex_tools(tools)
            
            # Add registered tools
            if self._tool_declarations:
                registered_tools = _build_vertex_tools(self._tool_declarations)
                model_tools.extend(registered_tools)
            
            # Add Google Search grounding if enabled
            if use_search_grounding and GoogleSearchRetrieval is not None:
                try:
                    model_tools.append(Tool(google_search_retrieval=GoogleSearchRetrieval()))
                except Exception as e:
                    print(f"Warning: GoogleSearchRetrieval not available: {e}")
            
            if model_tools:
                model_kwargs["tools"] = model_tools
            
            # Create model
            model = GenerativeModel(**model_kwargs)
            
            # Generate content
            response = await asyncio.to_thread(
                model.generate_content,
                prompt
            )
            
            # Process response - safely extract text (response.text raises ValueError
            # when the response contains function calls instead of text)
            try:
                response_text = response.text if response.text else "No response"
            except (ValueError, AttributeError):
                response_text = ""
            
            result = {
                "success": True,
                "message": response_text,
                "citations": [],
                "tools_used": [],
                "raw_response": response,
            }
            
            # Extract tool calls and function_calls if any
            function_calls = []
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call') and part.function_call is not None:
                                fc_name = getattr(part.function_call, 'name', None)
                                fc_args = getattr(part.function_call, 'args', {})
                                if fc_name:
                                    result["tools_used"].append({
                                        "name": fc_name,
                                        "args": dict(fc_args) if fc_args else {},
                                    })
                                    function_calls.append({
                                        "name": fc_name,
                                        "arguments": dict(fc_args) if fc_args else {},
                                    })
            
            # Add function_calls for chatbot_manager compatibility
            if function_calls:
                result["function_calls"] = function_calls
            
            # Also add "text" key as alias for "message" for compatibility
            result["text"] = result["message"]
            
            return result
            
        except Exception as e:
            print(f"❌ Error in generate_with_tools: {e}")
            import traceback
            traceback.print_exc()
            error_msg = f"Error: {str(e)}"
            return {
                "success": False,
                "message": error_msg,
                "text": error_msg,
                "citations": [],
                "tools_used": [],
            }
    
    async def analyze_contract(self, contract_text: str) -> Dict[str, Any]:
        """Analyze a legal contract using Vertex AI.
        
        Args:
            contract_text: The contract text to analyze
            
        Returns:
            Analysis results
        """
        prompt = f"""Analyze the following legal contract and provide:
1. Summary of key terms
2. Identified risks or concerns
3. Notable provisions and obligations
4. Recommendations

CONTRACT TEXT:
{contract_text}

Please provide a detailed analysis."""
        
        return await self.generate_with_tools(prompt)
    
    async def extract_entities(self, text: str, entity_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Extract entities from text using Vertex AI.
        
        Args:
            text: Text to analyze
            entity_types: Optional list of entity types to extract
            
        Returns:
            Extracted entities
        """
        types_str = ", ".join(entity_types) if entity_types else "named entities"
        prompt = f"""Extract {types_str} from the following text:

TEXT:
{text}

Return the results as a JSON object with entity types as keys and lists of entities as values."""
        
        result = await self.generate_text(prompt)
        
        try:
            entities = json.loads(result)
        except json.JSONDecodeError:
            entities = {"raw_text": result}
        
        return {"success": True, "entities": entities}
    
    async def summarize(self, text: str, max_length: Optional[int] = None) -> str:
        """Summarize text using Vertex AI.
        
        Args:
            text: Text to summarize
            max_length: Optional maximum length for summary
            
        Returns:
            Summary text
        """
        length_constraint = f" in approximately {max_length} words" if max_length else ""
        prompt = f"""Summarize the following text{length_constraint}:

TEXT:
{text}

SUMMARY:"""
        
        return await self.generate_text(prompt)


# Singleton instance
_service_instance: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create the Gemini service singleton.
    
    Returns:
        GeminiService instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = GeminiService()
    return _service_instance
