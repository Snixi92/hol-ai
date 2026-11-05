"""
Contrats d'échange de données inter-agents (A2A Protocol) pour HoL AI.
Schémas Pydantic v2 stricts avec sérialisation universelle JSON.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class AgentID(str, Enum):
    MANAGER = "manager"
    AGENT_1_CANVAS = "agent_1_canvas"
    AGENT_2_INGESTION = "agent_2_ingestion"
    AGENT_3_LOGISTICS = "agent_3_logistics"
    AGENT_4_FINANCE = "agent_4_finance"
    AGENT_5_CONTENT = "agent_5_content"
    AGENT_6_EXECUTION = "agent_6_execution"


class PriorityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class StatusEnum(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


class ActionType(str, Enum):
    # Agent 1 (Canvas)
    CREATE_CANVAS_NODE = "CREATE_CANVAS_NODE"
    UPDATE_CANVAS_NODE = "UPDATE_CANVAS_NODE"
    CONNECT_NODES = "CONNECT_NODES"
    FETCH_WORKSPACE_STATE = "FETCH_WORKSPACE_STATE"

    # Agent 2 (Ingestion & Mémoire)
    INGEST_MULTIMODAL = "INGEST_MULTIMODAL"
    OCR_DOCUMENT = "OCR_DOCUMENT"
    TRANSCRIBE_AUDIO = "TRANSCRIBE_AUDIO"
    SEMANTIC_SEARCH = "SEMANTIC_SEARCH"

    # Agent 3 (Logistique & Sourcing)
    TRACK_SHIPMENT = "TRACK_SHIPMENT"
    SCRAPE_PRICE = "SCRAPE_PRICE"
    FIND_SUPPLIERS = "FIND_SUPPLIERS"
    WATCH_PRICE_DROP = "WATCH_PRICE_DROP"
    EXECUTE_PURCHASE = "EXECUTE_PURCHASE"

    # Agent 4 (Finance & Audit)
    AUDIT_MARGINS = "AUDIT_MARGINS"
    RECONCILE_TRANSACTIONS = "RECONCILE_TRANSACTIONS"
    EXTRACT_INVOICE_DATA = "EXTRACT_INVOICE_DATA"
    AUDIT_SUBSCRIPTIONS = "AUDIT_SUBSCRIPTIONS"
    CANCEL_SUBSCRIPTION = "CANCEL_SUBSCRIPTION"

    # Agent 5 (Content & Social Engine)
    DETECT_TRENDS = "DETECT_TRENDS"
    GENERATE_SCRIPT = "GENERATE_SCRIPT"
    PUBLISH_TELEGRAM = "PUBLISH_TELEGRAM"
    AUDIT_META_ADS = "AUDIT_META_ADS"
    GENERATE_AFFILIATE_DROP = "GENERATE_AFFILIATE_DROP"

    # Agent 6 (Anti-Procrastination & Exécution Autonome & Tâches Quotidiennes)
    BREAKDOWN_GOAL = "BREAKDOWN_GOAL"
    SCHEDULE_TASK = "SCHEDULE_TASK"
    TRIGGER_NUDGE = "TRIGGER_NUDGE"
    START_AUTONOMOUS_WATCHER = "START_AUTONOMOUS_WATCHER"
    BOOK_RESERVATION = "BOOK_RESERVATION"
    CLEAN_INBOX = "CLEAN_INBOX"
    RECIPE_TO_GROCERY = "RECIPE_TO_GROCERY"
    SECURE_VM_AUDIT = "SECURE_VM_AUDIT"
    MANAGE_CALENDAR = "MANAGE_CALENDAR"
    EXECUTE_SANDBOX_CODE = "EXECUTE_SANDBOX_CODE"
    APPROVE_ACTION = "APPROVE_ACTION"


class SourceDescriptor(BaseModel):
    agent_id: AgentID
    instance_id: str = "default"
    role: str = "worker"


class TargetDescriptor(BaseModel):
    agent_id: AgentID
    action: ActionType

    @property
    def inbox_channel(self) -> str:
        from src.broker.topics import get_stream_for_agent
        return get_stream_for_agent(self.agent_id)


class LanguageContext(BaseModel):
    detected: str = "fr"
    code_switching_targets: List[str] = Field(default_factory=lambda: ["fr", "en", "ar"])


class ContextModel(BaseModel):
    user_id: str
    session_id: str
    canvas_id: Optional[str] = None
    language: LanguageContext = Field(default_factory=LanguageContext)
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def metadata(self) -> Dict[str, Any]:
        return self.extra_metadata


class ExecutionMetadata(BaseModel):
    max_retries: int = 3
    retry_count: int = 0
    timeout_ms: int = 15000
    token_budget: int = 4096


class ExecutionMetrics(BaseModel):
    duration_ms: int
    tokens_consumed: int = 0
    cost_usd: float = 0.0


class A2AMessage(BaseModel):
    """
    Enveloppe standardisée universelle pour tout message émis vers un agent.
    """
    message_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: Optional[UUID] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: SourceDescriptor
    target: TargetDescriptor
    priority: PriorityEnum = PriorityEnum.MEDIUM
    context: ContextModel = Field(default_factory=lambda: ContextModel(user_id="default_user", session_id="default_sess"))
    metadata: ExecutionMetadata = Field(default_factory=ExecutionMetadata)
    payload: Dict[str, Any] = Field(default_factory=dict)

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, data: str) -> "A2AMessage":
        return cls.model_validate_json(data)


class A2AResponse(BaseModel):
    """
    Enveloppe de retour émise par un agent vers le superviseur.
    """
    message_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID
    causation_id: UUID
    source: SourceDescriptor
    status: StatusEnum
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    execution_metrics: ExecutionMetrics
    result: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, data: str) -> "A2AResponse":
        return cls.model_validate_json(data)


# Re-exports pour compatibilité DAG et modularité
from src.orchestrator.planner import SubTask, ExecutionPlan, CyclicDependencyError, DependencyError
