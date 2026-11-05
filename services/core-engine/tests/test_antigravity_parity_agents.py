"""
Suite de tests unitaires pour les 7 Agents de Parité Antigravity de HoL AI.
Vérifie :
1. DevCodeAgent : lecture, écriture, édition chirurgicale, recherche d'arborescence.
2. ShellExecutionAgent : exécution terminal sécurisée, blocage de commandes destructrices, listing processus.
3. WebResearchAgent : recherche live, extraction lisible d'URL.
4. SubagentOrchestratorAgent : instanciation de sous-agents et exécution concurrente.
5. ArtifactsUIAgent : création d'artefacts persistants (Markdown, Mermaid, widgets HTML).
6. SystematicDebuggerAgent : parsing de stack-traces et propositions de correction.
7. ArchitectPlannerAgent : génération de plans d'implémentation et audit d'architecture.
"""
import pytest
import os
from pathlib import Path
from src.agents.antigravity_parity import (
    DevCodeAgent,
    ShellExecutionAgent,
    WebResearchAgent,
    SubagentOrchestratorAgent,
    ArtifactsUIAgent,
    SystematicDebuggerAgent,
    ArchitectPlannerAgent
)


@pytest.fixture
def tmp_workspace(tmp_path):
    """Crée un espace de travail temporaire pour les tests de fichiers."""
    test_file = tmp_path / "hello.py"
    test_file.write_text("def hello():\n    print('Hello World')\n", encoding="utf-8")
    return tmp_path


# --- 1. DevCodeAgent Tests ---
def test_dev_code_agent_lifecycle(tmp_workspace):
    file_path = str(tmp_workspace / "demo.txt")

    # Write
    write_res = DevCodeAgent.write_file(file_path, "Ligne 1\nLigne 2 à modifier\nLigne 3")
    assert write_res["status"] == "success"
    assert write_res["lines_count"] == 3

    # Read
    read_res = DevCodeAgent.read_file(file_path, start_line=2, end_line=3)
    assert read_res["status"] == "success"
    assert "Ligne 2" in read_res["content"]

    # Edit
    edit_res = DevCodeAgent.edit_file(file_path, target="Ligne 2 à modifier", replacement="Ligne 2 MODIFIÉE")
    assert edit_res["status"] == "success"
    assert edit_res["occurrences_replaced"] == 1

    # Verify Edit
    read_mod = DevCodeAgent.read_file(file_path)
    assert "Ligne 2 MODIFIÉE" in read_mod["content"]

    # List
    list_res = DevCodeAgent.list_directory(str(tmp_workspace))
    assert list_res["status"] == "success"
    assert list_res["total_entries"] >= 2

    # Search
    search_res = DevCodeAgent.search_directory(str(tmp_workspace), pattern="*.txt", file_content_query="MODIFIÉE")
    assert search_res["status"] == "success"
    assert len(search_res["matches"]) == 1


# --- 2. ShellExecutionAgent Tests ---
def test_shell_execution_safe_and_blocked():
    # Safe command
    cmd_res = ShellExecutionAgent.run_command("python -c \"print('ANTIGRAVITY_PARITY_OK')\"")
    assert cmd_res["status"] == "success"
    assert "ANTIGRAVITY_PARITY_OK" in cmd_res["stdout"]

    # Blocked dangerous command
    blocked_res = ShellExecutionAgent.run_command("rm -rf /")
    assert blocked_res["status"] == "blocked"
    assert blocked_res["returncode"] == 403

    # Process list
    proc_res = ShellExecutionAgent.list_running_processes(filter_name="python")
    assert proc_res["status"] == "success"
    assert proc_res["total"] >= 1


# --- 3. WebResearchAgent Tests ---
def test_web_research_agent():
    # Search query
    res = WebResearchAgent.search_web("Python programming language", max_results=2)
    assert res["status"] in ["success", "error"]
    if res["status"] == "success":
        assert len(res["results"]) > 0

    # Invalid URL handling
    err_res = WebResearchAgent.read_url_content("ftp://invalid-url.local")
    assert err_res["status"] == "error"


# --- 4. SubagentOrchestratorAgent Tests ---
@pytest.mark.asyncio
async def test_subagent_orchestrator():
    task = {
        "role": "Code Reviewer",
        "task_prompt": "Analyse ce snippet : print('Hello')",
        "system_instruction": "Sois bref."
    }
    single_res = await SubagentOrchestratorAgent.spawn_subagent(
        role=task["role"],
        task_prompt=task["task_prompt"],
        system_instruction=task["system_instruction"]
    )
    assert single_res["status"] == "completed"
    assert single_res["role"] == "Code Reviewer"
    assert len(single_res["result"]) > 0

    # Parallel dispatch
    parallel_res = await SubagentOrchestratorAgent.dispatch_parallel_subagents([
        {"role": "Agent 1", "task_prompt": "Tâche 1"},
        {"role": "Agent 2", "task_prompt": "Tâche 2"}
    ])
    assert parallel_res["status"] == "success"
    assert parallel_res["total_subagents"] == 2
    assert "Synthèse Multi-Agents" in parallel_res["executive_synthesis"]


# --- 5. ArtifactsUIAgent Tests ---
def test_artifacts_ui_agent():
    # Markdown Artifact
    art_res = ArtifactsUIAgent.create_artifact(
        title="Rapport d'audit",
        artifact_type="markdown",
        content="# Audit Antigravity\nTout est opérationnel.",
        user_facing=True
    )
    assert art_res["status"] == "created"
    assert Path(art_res["file_path"]).exists()

    # Mermaid Artifact
    mermaid_res = ArtifactsUIAgent.generate_mermaid_diagram(
        title="Architecture HoL AI",
        diagram_code="A[Client] --> B[Cognitive Engine] --> C[Tools]"
    )
    assert mermaid_res["status"] == "created"
    assert "mermaid" in mermaid_res["content"]

    # HTML Widget
    widget_res = ArtifactsUIAgent.generate_interactive_widget(
        title="Compteur Interactif",
        html_content="<button class='bg-cyan-500 p-2'>Cliquez-moi</button>"
    )
    assert widget_res["status"] == "created"
    assert "<!DOCTYPE html>" in widget_res["content"]


# --- 6. SystematicDebuggerAgent Tests ---
def test_systematic_debugger_agent():
    raw_traceback = """Traceback (most recent call last):
  File "C:\\app\\main.py", line 42, in process_data
    result = compute_values(items)
  File "C:\\app\\utils.py", line 18, in compute_values
    return sum(items) / len(items)
ZeroDivisionError: division by zero
"""
    parsed = SystematicDebuggerAgent.parse_stack_trace(raw_traceback)
    assert parsed["status"] == "parsed"
    assert parsed["error_type"] == "ZeroDivisionError"
    assert parsed["culprit_file"] == "C:\\app\\utils.py"
    assert parsed["culprit_line"] == 18

    # Diagnosis & Fix Suggestion
    diag = SystematicDebuggerAgent.diagnose_and_suggest_fix(raw_traceback)
    assert diag["status"] == "diagnosed"
    assert diag["error_type"] == "ZeroDivisionError"


# --- 7. ArchitectPlannerAgent Tests ---
def test_architect_planner_agent():
    plan_res = ArchitectPlannerAgent.generate_implementation_plan(
        title="Migration Cloud",
        objective="Migrer les microservices sur Kubernetes",
        constraints=["Zéro downtime"]
    )
    assert plan_res["status"] == "planned"
    assert plan_res["phases_count"] == 4
    assert "Phase 1 : Découverte" in plan_res["plan_content"]

    # Codebase Audit
    audit_res = ArchitectPlannerAgent.audit_codebase_structure("src")
    assert audit_res["status"] == "audited"
    assert audit_res["stats"]["total_files"] > 0
