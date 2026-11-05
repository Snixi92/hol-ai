import pytest
from unittest.mock import patch, MagicMock
from src.services.cognitive_engine import CognitiveAgentEngine


@pytest.mark.asyncio
async def test_cognitive_engine_tools_available():
    # Verify that the tools exist and can be called
    from src.services.app_launcher import AppLauncherService
    from src.services.code_app_generator import CodeAppGeneratorService
    from src.services.chart_generator import ChartGeneratorService
    from src.services.social_media_agent import SocialMediaAgentService

    # App launcher tool
    res_app = AppLauncherService.launch_application("discord", target_screen="haut", simulate=True)
    assert res_app["status"] in ["launched", "opened"]
    assert "discord" in res_app["app"]

    # Code app tool
    res_code = CodeAppGeneratorService.generate_app_template("morpion", open_browser=False)
    assert res_code["status"] == "created"
    assert "/apps/morpion/index.html" in res_code["preview_url"]

    # Chart tool
    res_chart = ChartGeneratorService.create_chart("Adoption IA", labels=["2023", "2024"], values=[6.0, 10.0])
    assert res_chart["status"] == "ok"
    assert len(res_chart["data_points"]) == 2

    # Social tool
    res_social = SocialMediaAgentService.create_post("LinkedIn", "Nouvelle IA")
    assert res_social["platform"] == "LinkedIn"

    # Antigravity Parity Agents
    from src.agents.antigravity_parity import (
        DevCodeAgent,
        ShellExecutionAgent,
        WebResearchAgent,
        SubagentOrchestratorAgent,
        ArtifactsUIAgent,
        SystematicDebuggerAgent,
        ArchitectPlannerAgent
    )

    # 1. DevCodeAgent
    res_dev = DevCodeAgent.read_file("main.py", start_line=1, end_line=5)
    assert res_dev["status"] == "success"

    # 2. ShellExecutionAgent
    res_shell = ShellExecutionAgent.run_command("python --version")
    assert res_shell["status"] == "success"

    # 3. WebResearchAgent
    res_web = WebResearchAgent.search_web("Python test", max_results=1)
    assert res_web["status"] in ["success", "error"]

    # 4. SubagentOrchestratorAgent
    res_sub = await SubagentOrchestratorAgent.spawn_subagent("Test Role", "Test task")
    assert res_sub["status"] == "completed"

    # 5. ArtifactsUIAgent
    res_art = ArtifactsUIAgent.create_artifact("Test Art", "markdown", "# Contenu")
    assert res_art["status"] == "created"

    # 6. SystematicDebuggerAgent
    res_diag = SystematicDebuggerAgent.diagnose_and_suggest_fix("ZeroDivisionError: division by zero")
    assert res_diag["status"] == "diagnosed"

    # 7. ArchitectPlannerAgent
    res_arch = ArchitectPlannerAgent.generate_implementation_plan("Test Plan", "Objectif test")
    assert res_arch["status"] == "planned"
