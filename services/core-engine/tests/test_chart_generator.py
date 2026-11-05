import pytest
from src.services.chart_generator import ChartGeneratorService


def test_create_bar_chart():
    res = ChartGeneratorService.create_chart(
        title="Adoption de l'IA en entreprise en France",
        chart_type="bar",
        labels=["2022", "2023", "2024", "2026 (Est.)"],
        values=[4.2, 6.1, 9.8, 16.5],
        unit="%"
    )

    assert res["title"] == "Adoption de l'IA en entreprise en France"
    assert res["chart_type"] == "bar"
    assert len(res["data_points"]) == 4
    assert res["data_points"][2]["label"] == "2024"
    assert res["data_points"][2]["value"] == 9.8
    assert res["unit"] == "%"
    assert "visual_svg" in res or "chart_config" in res


def test_chart_handles_empty_or_zero_values():
    res = ChartGeneratorService.create_chart(
        title="Test vide",
        chart_type="line",
        labels=[],
        values=[]
    )
    assert res["status"] in ["ok", "fallback"]
    assert res["chart_type"] == "line"
