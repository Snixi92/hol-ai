"""
Package des Agents de Parité Antigravity pour HoL AI.
Confère à HoL AI 100% des super-pouvoirs d'Antigravity :
- DevCodeAgent : Opérations sur fichiers, code, édition chirurgicale, arborescence.
- ShellExecutionAgent : Exécution de commandes terminal, surveillance processus, sandbox.
- WebResearchAgent : Recherche web en direct, scraping propre de pages, synthèse multi-sources.
- SubagentOrchestratorAgent : Création et délégation à des sous-agents spécialisés en parallèle.
- ArtifactsUIAgent : Génération d'artefacts visuels (Mermaid, Markdown, widgets interactifs HTML/JS).
- SystematicDebuggerAgent : Diagnostic de stack-traces, exécution de tests et patchs ciblés.
- ArchitectPlannerAgent : Élaboration de plans d'implémentation par phases et audit d'architecture.
"""
from src.agents.antigravity_parity.dev_code_agent import DevCodeAgent
from src.agents.antigravity_parity.shell_execution_agent import ShellExecutionAgent
from src.agents.antigravity_parity.web_research_agent import WebResearchAgent
from src.agents.antigravity_parity.subagent_orchestrator_agent import SubagentOrchestratorAgent
from src.agents.antigravity_parity.artifacts_ui_agent import ArtifactsUIAgent
from src.agents.antigravity_parity.systematic_debugger_agent import SystematicDebuggerAgent
from src.agents.antigravity_parity.architect_planner_agent import ArchitectPlannerAgent

__all__ = [
    "DevCodeAgent",
    "ShellExecutionAgent",
    "WebResearchAgent",
    "SubagentOrchestratorAgent",
    "ArtifactsUIAgent",
    "SystematicDebuggerAgent",
    "ArchitectPlannerAgent"
]
