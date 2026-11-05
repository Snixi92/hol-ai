"""
Data models for the HoL AI Tool Registry and Public APIs catalog.
Defines schemas for tools, parameters, search queries, and execution results.
Compatible with Pydantic v2.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ToolAuthType(str, Enum):
    """Authentication type required by an API tool."""
    NO_AUTH = "none"
    API_KEY = "api_key"
    OAUTH = "oauth"


class ToolExecutionType(str, Enum):
    """Execution tier and modality for a tool."""
    DIRECT_REST = "direct_rest"        # Curated endpoint with validated parameter schema
    GENERIC_HTTP = "generic_http"      # Uncurated endpoint invoked via generic HTTP client
    DOCUMENTATION = "documentation"    # Informational / external documentation link
    BUILTIN_AGENT = "builtin_agent"    # Internal HoL AI specialized agent


class ParameterLocation(str, Enum):
    """Location of a parameter in the HTTP request."""
    QUERY = "query"
    PATH = "path"
    HEADER = "header"
    BODY = "body"


class ToolParameter(BaseModel):
    """Parameter definition for an executable tool."""
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="Parameter name")
    type: str = Field(default="string", description="Parameter type: string, number, integer, boolean")
    location: ParameterLocation = Field(default=ParameterLocation.QUERY, description="Parameter location")
    required: bool = Field(default=False, description="Whether parameter is mandatory")
    default: Optional[Any] = Field(default=None, description="Default value if not provided")
    description: str = Field(default="", description="Description of the parameter")


class ToolDefinition(BaseModel):
    """Complete structured definition of a public or internal tool."""
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Unique tool identifier, e.g. 'weather_open_meteo'")
    name: str = Field(..., description="Display name of the tool or API")
    category: str = Field(..., description="Category from the catalog, e.g. 'Weather', 'Finance'")
    description: str = Field(..., description="Functional summary of the tool")
    url: str = Field(..., description="Catalog reference URL or documentation link")
    endpoint_url: Optional[str] = Field(default=None, description="Direct REST endpoint if executable")
    http_method: str = Field(default="GET", description="HTTP verb: GET, POST, etc.")
    auth_type: ToolAuthType = Field(default=ToolAuthType.NO_AUTH, description="Authentication type")
    execution_type: ToolExecutionType = Field(default=ToolExecutionType.GENERIC_HTTP, description="Execution type")
    https_support: bool = Field(default=True, description="Whether HTTPS is supported")
    cors_support: str = Field(default="Unknown", description="CORS compliance: Yes, No, Unknown")
    parameters: List[ToolParameter] = Field(default_factory=list, description="Supported parameter list")
    tags: List[str] = Field(default_factory=list, description="Multilingual search tokens (fr, en, es, darija)")
    timeout_sec: float = Field(default=8.0, description="Execution timeout in seconds")
    cache_ttl_sec: int = Field(default=300, description="Cache time-to-live in seconds")
    is_curated: bool = Field(default=False, description="Whether this is a pre-configured curated tool")

    def to_gemini_schema(self) -> Dict[str, Any]:
        """Convert tool definition to OpenAPI/Gemini function declaration schema."""
        properties: Dict[str, Any] = {}
        required: List[str] = []
        for param in self.parameters:
            prop: Dict[str, Any] = {
                "type": param.type,
                "description": param.description
            }
            if param.default is not None:
                prop["default"] = param.default
            properties[param.name] = prop
            if param.required:
                required.append(param.name)

        return {
            "name": self.id,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }


class ToolQueryResult(BaseModel):
    """Ranked search result returned by the registry."""
    model_config = ConfigDict(extra="ignore")

    tool_id: str = Field(..., description="Matched tool ID")
    name: str = Field(..., description="Tool display name")
    category: str = Field(..., description="Tool category")
    description: str = Field(..., description="Tool description")
    relevance_score: float = Field(default=0.0, description="Matching relevance score")
    endpoint_available: bool = Field(default=False, description="Whether a direct endpoint URL is present")
    is_curated: bool = Field(default=False, description="Whether tool is curated")


class ToolExecutionResult(BaseModel):
    """Result of executing a tool via the autonomous execution engine."""
    model_config = ConfigDict(extra="ignore")

    success: bool = Field(..., description="Whether execution succeeded")
    tool_id: str = Field(..., description="ID of the executed tool")
    name: Optional[str] = Field(default="", description="Tool display name")
    data: Optional[Any] = Field(default=None, description="Processed JSON data payload")
    summary_text: Optional[str] = Field(default="", description="Human-readable text summary")
    card: Optional[Dict[str, Any]] = Field(default=None, description="Interactive Cockpit HUD card payload")
    error_code: Optional[str] = Field(default=None, description="Error code on failure")
    error_message: Optional[str] = Field(default=None, description="Detailed error message on failure")
    execution_time_ms: Optional[float] = Field(default=0.0, description="Execution duration in milliseconds")
