"""
VisualComputerUseAgent : Agent de Computer-Use visuel pour HoL AI.
Inspiré de la fonctionnalité Computer-Use de Meta Muse :
- Lancement de sessions de navigation visuelle avec retour vidéo screencast.
- Déclenchement de missions autonomes avec observation en direct par l'utilisateur.
- Passage en mode interactif 'Take Over' et arrêt d'urgence.
"""
import asyncio
import concurrent.futures
import time
from typing import Dict, Any, Optional
from src.services.visual_computer_use import VisualComputerUseService


class VisualComputerUseAgent:
    """Agent orchestrateur de la vision et de l'automatisation directe du navigateur."""

    @classmethod
    def launch_browser_stream(cls, url: str = "https://www.google.fr") -> Dict[str, Any]:
        """
        Démarre la session de streaming visuel du navigateur distant.
        """
        t0 = time.time()
        service = VisualComputerUseService.get_instance()

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    res = executor.submit(asyncio.run, service.start_browser(initial_url=url)).result()
            else:
                res = loop.run_until_complete(service.start_browser(initial_url=url))
        except Exception:
            res = asyncio.run(service.start_browser(initial_url=url))

        res["duration_ms"] = round((time.time() - t0) * 1000, 1)
        res["websocket_endpoint"] = "/ws/browser-stream"
        res["verbal_reply"] = (
            f"Navigateur virtuel démarré sur {res.get('url', url)}. "
            "Le flux vidéo temps réel est connecté à ton dashboard avec le bouton 'Take Over' !"
        )
        return res

    @classmethod
    def execute_navigation_task(cls, instruction: str) -> Dict[str, Any]:
        """
        Exécute une tâche autonome de navigation dans le navigateur sous les yeux de l'utilisateur.
        """
        t0 = time.time()
        service = VisualComputerUseService.get_instance()

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    res = executor.submit(asyncio.run, service.run_autonomous_navigation(prompt=instruction)).result()
            else:
                res = loop.run_until_complete(service.run_autonomous_navigation(prompt=instruction))
        except Exception:
            res = asyncio.run(service.run_autonomous_navigation(prompt=instruction))

        res["duration_ms"] = round((time.time() - t0) * 1000, 1)
        return res
