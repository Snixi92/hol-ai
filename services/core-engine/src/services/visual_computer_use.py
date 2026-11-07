"""
VisualComputerUseService : Service de Computer-Use visuel avec streaming vidéo temps réel et prise en main interactive (Take Over).
Inspiré de la fonctionnalité Computer-Use de Meta Muse :
- Pilotage Chromium via Playwright avec capture ultra-rapide par Chrome DevTools Protocol (CDP Screencast).
- Diffusion de trames JPEG vers les clients WebSockets avec curseur IA visible.
- Réception et transmission des actions utilisateur lors du passage en mode 'Take Over' (clic, souris, clavier).
- Bouton d'arrêt d'urgence (Emergency Stop) et navigation autonome pas-à-pas.
"""
import asyncio
import base64
import logging
import time
from typing import Dict, Any, List, Optional, Set
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page, CDPSession
except ImportError:
    async_playwright, Browser, BrowserContext, Page, CDPSession = None, None, None, None, None

logger = logging.getLogger("hol_ai.visual_computer_use")


class VisualComputerUseService:
    """Service singleton gérant la session Playwright, le screencast CDP et les entrées interactives."""

    _instance: Optional["VisualComputerUseService"] = None

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.cdp: Optional[CDPSession] = None
        self.is_running: bool = False
        self.mode: str = "ai_autonomous"  # "ai_autonomous", "human_takeover", "stopped"
        self.latest_frame_base64: Optional[str] = None
        self.active_websockets: Set[Any] = set()
        self.cursor_position: Dict[str, int] = {"x": 640, "y": 400}
        self.current_url: str = "about:blank"
        self.last_status: str = "Inactif"
        self.is_task_running: bool = False
        self._heartbeat_task: Optional[asyncio.Task] = None

    @classmethod
    def get_instance(cls) -> "VisualComputerUseService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def _broadcast_status(self, status: str, loading: bool = False) -> None:
        """Transmet une mise à jour d'état/chargement à tous les clients."""
        self.last_status = status
        if not self.active_websockets:
            return
        payload = {
            "type": "status_update",
            "status": status,
            "loading": loading,
            "url": self.current_url,
            "mode": self.mode
        }
        dead_sockets = set()
        for ws in self.active_websockets:
            try:
                await ws.send_json(payload)
            except Exception:
                dead_sockets.add(ws)
        self.active_websockets.difference_update(dead_sockets)

    async def _screencast_heartbeat(self):
        """Boucle de secours assurant un flux vidéo fluide régulier (1 FPS minimum garanti)."""
        while self.is_running:
            try:
                await asyncio.sleep(1.0)
                if self.is_running and self.page and self.active_websockets:
                    screenshot_bytes = await self.page.screenshot(type="jpeg", quality=65)
                    self.latest_frame_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                    await self._broadcast_frame(self.latest_frame_base64)
            except Exception:
                pass

    async def start_browser(self, initial_url: str = "https://www.google.fr") -> Dict[str, Any]:
        """Démarre le navigateur Chromium et active le screencast CDP."""
        if self.is_running and self.page is not None:
            if initial_url and initial_url != self.current_url:
                await self._broadcast_status(f"Navigation vers {initial_url}...", loading=True)
                await self.page.goto(initial_url)
                self.current_url = initial_url
                try:
                    s_bytes = await self.page.screenshot(type="jpeg", quality=75)
                    self.latest_frame_base64 = base64.b64encode(s_bytes).decode("utf-8")
                    await self._broadcast_frame(self.latest_frame_base64)
                except Exception:
                    pass
                await self._broadcast_status(f"Prêt sur {self.current_url}", loading=False)
            return {"status": "already_running", "url": self.current_url}

        if not async_playwright:
            logger.warning("Playwright non disponible pour VisualComputerUseService.")
            return {"status": "error", "message": "Playwright non disponible dans cet environnement."}

        try:
            await self._broadcast_status("Lancement du moteur Chromium (Playwright)...", loading=True)
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            self.context = await self.browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            self.page = await self.context.new_page()
            await self._broadcast_status(f"Chargement initial de {initial_url}...", loading=True)
            await self.page.goto(initial_url, timeout=30000)
            self.current_url = self.page.url

            # Capture immédiate de la toute première frame pour affichage instantané !
            try:
                first_frame_bytes = await self.page.screenshot(type="jpeg", quality=75)
                self.latest_frame_base64 = base64.b64encode(first_frame_bytes).decode("utf-8")
                await self._broadcast_frame(self.latest_frame_base64)
            except Exception as ex:
                logger.warning(f"Capture initiale échouée : {ex}")

            # Configuration du screencast Chrome DevTools Protocol
            self.cdp = await self.context.new_cdp_session(self.page)

            async def _on_screencast_frame(event):
                frame_data = event.get("data")
                session_id = event.get("sessionId")
                if frame_data:
                    self.latest_frame_base64 = frame_data
                    await self._broadcast_frame(frame_data)
                try:
                    await self.cdp.send("Page.screencastFrameAck", {"sessionId": session_id})
                except Exception:
                    pass

            self.cdp.on("Page.screencastFrame", lambda ev: asyncio.create_task(_on_screencast_frame(ev)))
            await self.cdp.send("Page.startScreencast", {
                "format": "jpeg",
                "quality": 75,
                "maxWidth": 1280,
                "maxHeight": 800,
                "everyNthFrame": 1
            })

            self.is_running = True
            self.last_status = f"Prêt sur {self.current_url}"
            await self._broadcast_status(self.last_status, loading=False)

            # Lancement de la boucle de secours pour garantir 1 frame minimum même sur page statique
            if self._heartbeat_task is None or self._heartbeat_task.done():
                self._heartbeat_task = asyncio.create_task(self._screencast_heartbeat())

            return {"status": "started", "url": self.current_url}

        except Exception as e:
            logger.error(f"Échec démarrage VisualComputerUseService : {e}")
            self.last_status = f"Erreur : {e}"
            await self._broadcast_status(self.last_status, loading=False)
            return {"status": "error", "error": str(e)}

    async def _broadcast_frame(self, frame_b64: str) -> None:
        """Transmet la trame à tous les clients WebSockets actifs."""
        if not self.active_websockets:
            return
        payload = {
            "type": "screencast_frame",
            "frame": frame_b64,
            "cursor": self.cursor_position,
            "mode": self.mode,
            "url": self.current_url,
            "status": self.last_status
        }
        dead_sockets = set()
        for ws in self.active_websockets:
            try:
                await ws.send_json(payload)
            except Exception:
                dead_sockets.add(ws)
        self.active_websockets.difference_update(dead_sockets)

    async def handle_user_input(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute une action envoyée par l'utilisateur en mode Take Over."""
        if not self.is_running or not self.page:
            return {"status": "error", "message": "Navigateur inactif"}

        action_type = action_data.get("type")
        x = action_data.get("x")
        y = action_data.get("y")

        try:
            if action_type == "mouse_move" and x is not None and y is not None:
                self.cursor_position = {"x": int(x), "y": int(y)}
                await self.page.mouse.move(int(x), int(y))
                return {"status": "ok"}

            elif action_type == "mouse_click" and x is not None and y is not None:
                self.cursor_position = {"x": int(x), "y": int(y)}
                btn = action_data.get("button", "left")
                await self.page.mouse.click(int(x), int(y), button=btn)
                # Capture rapide pour feedback visuel immédiat
                await asyncio.sleep(0.1)
                try:
                    s_bytes = await self.page.screenshot(type="jpeg", quality=75)
                    self.latest_frame_base64 = base64.b64encode(s_bytes).decode("utf-8")
                    await self._broadcast_frame(self.latest_frame_base64)
                except Exception:
                    pass
                return {"status": "ok", "action": "click"}

            elif action_type == "key_down":
                key = action_data.get("key", "")
                if key:
                    await self.page.keyboard.press(key)
                await asyncio.sleep(0.1)
                try:
                    s_bytes = await self.page.screenshot(type="jpeg", quality=75)
                    self.latest_frame_base64 = base64.b64encode(s_bytes).decode("utf-8")
                    await self._broadcast_frame(self.latest_frame_base64)
                except Exception:
                    pass
                return {"status": "ok", "key": key}

            elif action_type == "type_text":
                text = action_data.get("text", "")
                if text:
                    await self.page.keyboard.type(text)
                await asyncio.sleep(0.1)
                try:
                    s_bytes = await self.page.screenshot(type="jpeg", quality=75)
                    self.latest_frame_base64 = base64.b64encode(s_bytes).decode("utf-8")
                    await self._broadcast_frame(self.latest_frame_base64)
                except Exception:
                    pass
                return {"status": "ok", "typed": text}

            elif action_type == "navigate":
                target_url = action_data.get("url", "")
                if target_url:
                    if not target_url.startswith("http"):
                        target_url = "https://" + target_url
                    await self._broadcast_status(f"Navigation vers {target_url}...", loading=True)
                    await self.page.goto(target_url, timeout=25000)
                    self.current_url = self.page.url
                    # Capture immédiate de l'écran après navigation pour affichage garanti !
                    try:
                        s_bytes = await self.page.screenshot(type="jpeg", quality=75)
                        self.latest_frame_base64 = base64.b64encode(s_bytes).decode("utf-8")
                        await self._broadcast_frame(self.latest_frame_base64)
                    except Exception as ex:
                        logger.warning(f"Screenshot post-navigation échoué : {ex}")
                    await self._broadcast_status(f"Prêt sur {self.current_url}", loading=False)
                return {"status": "ok", "url": self.current_url}

            elif action_type == "scroll":
                dy = action_data.get("dy", 100)
                await self.page.mouse.wheel(0, int(dy))
                return {"status": "ok"}

            elif action_type == "set_mode":
                new_mode = action_data.get("mode", "ai_autonomous")
                self.mode = new_mode
                return {"status": "ok", "mode": self.mode}

            elif action_type == "emergency_stop":
                self.mode = "stopped"
                self.is_task_running = False
                self.last_status = "ARRÊT D'URGENCE ACTIVÉ"
                return {"status": "stopped"}

        except Exception as e:
            logger.warning(f"Erreur action interactive : {e}")
            return {"status": "error", "error": str(e)}

        return {"status": "ignored"}

    async def run_autonomous_navigation(self, prompt: str) -> Dict[str, Any]:
        """Exécute une tâche autonome dans le navigateur pendant que l'utilisateur regarde."""
        if not self.is_running:
            await self.start_browser()

        self.is_task_running = True
        self.mode = "ai_autonomous"
        self.last_status = f"Mission en cours : {prompt[:50]}..."

        actions_log = []

        try:
            # Exemple déterministe d'automatisation
            prompt_lower = prompt.lower()
            if "amazon" in prompt_lower:
                self.last_status = "Navigation vers Amazon.fr..."
                await self.page.goto("https://www.amazon.fr", timeout=30000)
                self.current_url = self.page.url
                actions_log.append("Page Amazon chargée")
                await asyncio.sleep(1)

                # Simuler le curseur se déplaçant vers la barre de recherche
                self.cursor_position = {"x": 500, "y": 60}
                await asyncio.sleep(0.5)

            elif "leboncoin" in prompt_lower:
                self.last_status = "Navigation vers Leboncoin..."
                await self.page.goto("https://www.leboncoin.fr", timeout=30000)
                self.current_url = self.page.url
                actions_log.append("Page Leboncoin chargée")
                await asyncio.sleep(1)

            else:
                self.last_status = "Recherche Google..."
                await self.page.goto("https://www.google.fr", timeout=30000)
                self.current_url = self.page.url
                actions_log.append("Moteur de recherche ouvert")

                # Remplir le champ de recherche
                try:
                    search_input = await self.page.query_selector("textarea, input[name='q']")
                    if search_input:
                        box = await search_input.bounding_box()
                        if box:
                            self.cursor_position = {"x": int(box["x"] + box["width"] / 2), "y": int(box["y"] + box["height"] / 2)}
                            await asyncio.sleep(0.5)
                        await search_input.fill(prompt)
                        actions_log.append(f"Texte saisi : {prompt}")
                        await self.page.keyboard.press("Enter")
                        actions_log.append("Recherche envoyée")
                        await asyncio.sleep(1.5)
                        self.current_url = self.page.url
                except Exception as query_err:
                    actions_log.append(f"Notice: {query_err}")

            self.last_status = f"Mission terminée sur {self.current_url}"
            self.is_task_running = False

            return {
                "status": "success",
                "prompt": prompt,
                "current_url": self.current_url,
                "actions_executed": actions_log,
                "verbal_reply": f"J'ai exécuté l'action sur le navigateur distant : {', '.join(actions_log)}."
            }

        except Exception as e:
            self.is_task_running = False
            self.last_status = f"Échec mission : {e}"
            return {
                "status": "error",
                "error": str(e),
                "actions_executed": actions_log,
                "verbal_reply": f"Erreur lors de la navigation autonome : {e}"
            }

    async def close_browser(self) -> None:
        """Arrête le navigateur et libère les ressources."""
        try:
            if self.cdp:
                await self.cdp.send("Page.stopScreencast")
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception:
            pass
        self.is_running = False
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
        self.last_status = "Arrêté"
