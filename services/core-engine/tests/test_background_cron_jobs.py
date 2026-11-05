"""
Tests unitaires pour le Gardien d'Arrière-Plan & les 3 Cron Jobs autonomes (Phase 5).
Vérifie la planification et l'exécution de :
- Synthèse matinale (08h00)
- Point mi-journée (13h00)
- Bilan financier et revenus nocturne (22h00)
"""
import pytest
from src.services.background_watcher import BackgroundGuardian, CRON_DEFINITIONS


@pytest.fixture
def guardian_instance():
    guardian = BackgroundGuardian()
    return guardian


def test_cron_jobs_configuration(guardian_instance):
    """Vérifie la présence et la configuration des 3 Cron Jobs autonomes."""
    cron_jobs = guardian_instance.cron_jobs
    assert len(cron_jobs) == 3

    job_ids = [j["id"] for j in cron_jobs]
    assert "cron_08h00_morning_summary" in job_ids
    assert "cron_13h00_midday_checkpoint" in job_ids
    assert "cron_22h00_nightly_finance" in job_ids

    # Vérification des heures et expressions cron
    morning_job = next(j for j in cron_jobs if j["id"] == "cron_08h00_morning_summary")
    assert morning_job["scheduled_time"] == "08:00"
    assert morning_job["cron_expression"] == "0 8 * * *"
    assert "Synthèse matinale" in morning_job["name"]

    midday_job = next(j for j in cron_jobs if j["id"] == "cron_13h00_midday_checkpoint")
    assert midday_job["scheduled_time"] == "13:00"
    assert midday_job["cron_expression"] == "0 13 * * *"
    assert "Point mi-journée" in midday_job["name"]

    nightly_job = next(j for j in cron_jobs if j["id"] == "cron_22h00_nightly_finance")
    assert nightly_job["scheduled_time"] == "22:00"
    assert nightly_job["cron_expression"] == "0 22 * * *"
    assert "Bilan financier" in nightly_job["name"]


def test_execute_morning_summary_cron(guardian_instance):
    """Vérifie l'exécution autonome de la synthèse matinale de 08h00."""
    result = guardian_instance.execute_cron_job("cron_08h00_morning_summary")
    assert result["job_id"] == "cron_08h00_morning_summary"
    assert "Synthèse Matinale" in result["title"]
    assert "inbox_overview" in result
    assert "top_priorities_today" in result
    assert len(result["top_priorities_today"]) >= 3
    assert "price_watch_highlights" in result

    # Vérification de la mise à jour de l'état
    job = next(j for j in guardian_instance.cron_jobs if j["id"] == "cron_08h00_morning_summary")
    assert job["execution_count"] == 1
    assert job["last_run"] is not None
    assert len(guardian_instance.cron_history) == 1


def test_execute_midday_checkpoint_cron(guardian_instance):
    """Vérifie l'exécution autonome du point mi-journée de 13h00."""
    result = guardian_instance.execute_cron_job("cron_13h00_midday_checkpoint")
    assert result["job_id"] == "cron_13h00_midday_checkpoint"
    assert "Point Stratégique Mi-Journée" in result["title"]
    assert "live_sales_momentum" in result
    assert result["live_sales_momentum"]["blended_roas"] >= 3.0
    assert "afternoon_adjustments" in result


def test_execute_nightly_finance_cron(guardian_instance):
    """Vérifie l'exécution autonome du bilan financier nocturne de 22h00."""
    result = guardian_instance.execute_cron_job("cron_22h00_nightly_finance")
    assert result["job_id"] == "cron_22h00_nightly_finance"
    assert "Bilan Financier & Revenus Nocturne" in result["title"]
    assert "daily_financial_ledger" in result
    ledger = result["daily_financial_ledger"]
    assert ledger["gross_revenue_eur"] > 0
    assert ledger["net_profit_eur"] > 0
    assert ledger["net_profit_margin_pct"] > 40
    assert "treasury_optimizations" in result
    assert "Security" in result["security_lock"] or "sécurisée" in result["security_lock"]


def test_cron_automatic_time_trigger(guardian_instance):
    """Vérifie le déclenchement autonome par détection de l'heure planifiée."""
    assert guardian_instance.cron_jobs[0]["execution_count"] == 0

    # Simulation du passage à 08:00
    guardian_instance._check_cron_jobs("08:00")
    assert guardian_instance.cron_jobs[0]["execution_count"] == 1

    # Une seconde vérification à la même minute ne doit pas redéclencher
    guardian_instance._check_cron_jobs("08:00")
    assert guardian_instance.cron_jobs[0]["execution_count"] == 1


def test_guardian_status_contains_cron_jobs_and_history(guardian_instance):
    """Vérifie que l'état exposé pour l'API / WebSocket contient les cron jobs et l'historique."""
    guardian_instance.execute_cron_job("cron_13h00_midday_checkpoint")
    status = guardian_instance.get_status()

    assert "cron_jobs" in status
    assert len(status["cron_jobs"]) == 3
    assert "cron_history" in status
    assert len(status["cron_history"]) >= 1
    assert status["cron_history"][0]["job_id"] == "cron_13h00_midday_checkpoint"
