"""
Définition des flux (Streams), files d'attente et groupes de consommateurs Redis.
"""
from src.core.contracts import AgentID

# Noms des streams principaux
STREAM_MANAGER_INBOUND = "stream:manager:inbound"
STREAM_MANAGER_OUTBOUND = "stream:manager:outbound"
STREAM_DEAD_LETTER_QUEUE = "stream:dlq"

# Mappage des streams dédiés pour chaque agent
AGENT_STREAMS = {
    AgentID.AGENT_1_CANVAS: "stream:agent:canvas",
    AgentID.AGENT_2_INGESTION: "stream:agent:ingestion",
    AgentID.AGENT_3_LOGISTICS: "stream:agent:logistics",
    AgentID.AGENT_4_FINANCE: "stream:agent:finance",
    AgentID.AGENT_5_CONTENT: "stream:agent:content",
    AgentID.AGENT_6_EXECUTION: "stream:agent:execution",
}

# Groupes de consommateurs standards
def get_consumer_group(agent_id: AgentID) -> str:
    return f"cg:{agent_id.value}"

def get_stream_for_agent(agent_id: AgentID) -> str:
    if agent_id == AgentID.MANAGER:
        return STREAM_MANAGER_INBOUND
    return AGENT_STREAMS[agent_id]
