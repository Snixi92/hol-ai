"""
Package des agents de parité Meta Muse (Muse AI) pour HoL AI.
Regroupe les 10 agents spécialisés couvrant l'ensemble des fonctionnalités de Meta Muse :
1. SubscriptionAuditorAgent
2. NutritionVisionAgent
3. WorkspaceNavigatorAgent
4. WhatsAppGatewayAgent
5. InstagramConnectorAgent
6. DynamicToolSynthesizerAgent
7. AvatarVoiceRendererAgent
8. VirtualCardVaultAgent
9. SentinelGatekeeperAgent
10. VisualComputerUseAgent
"""

from .subscription_auditor_agent import SubscriptionAuditorAgent
from .nutrition_vision_agent import NutritionVisionAgent
from .workspace_navigator_agent import WorkspaceNavigatorAgent
from .whatsapp_gateway_agent import WhatsAppGatewayAgent
from .instagram_connector_agent import InstagramConnectorAgent
from .dynamic_tool_synthesizer_agent import DynamicToolSynthesizerAgent
from .avatar_voice_renderer_agent import AvatarVoiceRendererAgent
from .virtual_card_vault_agent import VirtualCardVaultAgent
from .sentinel_gatekeeper_agent import SentinelGatekeeperAgent
from .visual_computer_use_agent import VisualComputerUseAgent

__all__ = [
    "SubscriptionAuditorAgent",
    "NutritionVisionAgent",
    "WorkspaceNavigatorAgent",
    "WhatsAppGatewayAgent",
    "InstagramConnectorAgent",
    "DynamicToolSynthesizerAgent",
    "AvatarVoiceRendererAgent",
    "VirtualCardVaultAgent",
    "SentinelGatekeeperAgent",
    "VisualComputerUseAgent",
]
