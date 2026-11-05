"""
Générateur et bac à sable de code applicatif autonome (HTML/CSS/JS) pour Jarvis.
Permet à l'agent de coder des mini-applications, jeux (morpion, calculatrice, etc.),
de sauvegarder les fichiers en local et de les ouvrir directement dans le navigateur.
"""
import os
import re
import sys
import logging
import webbrowser
from typing import Dict, Any, Optional

logger = logging.getLogger("hol_ai.code_app_generator")


class CodeAppGeneratorService:
    """Service de génération de code et de déploiement local d'applications."""

    # Répertoire racine où les applications générées sont hébergées
    BASE_APPS_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "api", "static", "apps")
    )

    @classmethod
    def _sanitize_app_name(cls, name: str) -> str:
        """Nettoie le nom de l'application pour un chemin de dossier sécurisé."""
        clean = re.sub(r"[^a-zA-Z0-9_\-]", "_", name.lower().strip())
        return clean or "app_generated"

    @classmethod
    def get_template_for(cls, app_type: str) -> Dict[str, str]:
        """Retourne un template riche si l'agent n'a pas fourni de code spécifique."""
        t = app_type.lower()
        if "morpion" in t or "tic" in t:
            return {
                "description": "Jeu de Morpion (Tic-Tac-Toe) interactif avec score et effets néon",
                "html": """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Morpion Cyberpunk - Jarvis Apps</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="container">
    <h1>JARVIS // MORPION CYBERPUNK</h1>
    <div id="status" class="status">Tour du joueur : <span id="current-player" class="neon-cyan">X</span></div>
    <div class="grid" id="board">
      <div class="cell" data-index="0"></div>
      <div class="cell" data-index="1"></div>
      <div class="cell" data-index="2"></div>
      <div class="cell" data-index="3"></div>
      <div class="cell" data-index="4"></div>
      <div class="cell" data-index="5"></div>
      <div class="cell" data-index="6"></div>
      <div class="cell" data-index="7"></div>
      <div class="cell" data-index="8"></div>
    </div>
    <button id="reset-btn" class="glow-btn">NOUVELLE PARTIE</button>
  </div>
  <script src="script.js"></script>
</body>
</html>""",
                "css": """* { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }
body { background: #070913; color: #e2e8f0; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
.container { background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(0, 243, 255, 0.3); border-radius: 16px; padding: 32px; text-align: center; box-shadow: 0 0 35px rgba(0, 243, 255, 0.15); }
h1 { font-size: 1.5rem; letter-spacing: 2px; color: #00f3ff; margin-bottom: 16px; text-shadow: 0 0 10px rgba(0, 243, 255, 0.5); }
.status { font-size: 1.1rem; margin-bottom: 24px; }
.neon-cyan { color: #00f3ff; font-weight: bold; text-shadow: 0 0 8px #00f3ff; }
.neon-pink { color: #ff007f; font-weight: bold; text-shadow: 0 0 8px #ff007f; }
.grid { display: grid; grid-template-columns: repeat(3, 100px); grid-template-rows: repeat(3, 100px); gap: 12px; margin: 0 auto 24px auto; }
.cell { background: #111827; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 2.5rem; font-weight: bold; cursor: pointer; transition: all 0.2s ease; }
.cell:hover { background: #1f2937; border-color: #00f3ff; box-shadow: 0 0 15px rgba(0, 243, 255, 0.3); transform: scale(1.02); }
.glow-btn { background: linear-gradient(135deg, #00f3ff, #0066ff); color: #000; border: none; padding: 12px 24px; font-weight: bold; border-radius: 8px; cursor: pointer; letter-spacing: 1px; transition: all 0.3s ease; box-shadow: 0 0 15px rgba(0, 243, 255, 0.4); }
.glow-btn:hover { transform: translateY(-2px); box-shadow: 0 0 25px rgba(0, 243, 255, 0.8); }""",
                "js": """let board = ['', '', '', '', '', '', '', '', ''];
let currentPlayer = 'X';
let gameActive = true;
const winningConditions = [
  [0, 1, 2], [3, 4, 5], [6, 7, 8],
  [0, 3, 6], [1, 4, 7], [2, 5, 8],
  [0, 4, 8], [2, 4, 6]
];
const statusDisplay = document.getElementById('status');
const playerDisplay = document.getElementById('current-player');
const cells = document.querySelectorAll('.cell');

function handleCellClick(e) {
  const cell = e.target;
  const index = parseInt(cell.getAttribute('data-index'));
  if (board[index] !== '' || !gameActive) return;

  board[index] = currentPlayer;
  cell.textContent = currentPlayer;
  cell.classList.add(currentPlayer === 'X' ? 'neon-cyan' : 'neon-pink');

  checkResult();
}

function checkResult() {
  let roundWon = false;
  for (let condition of winningConditions) {
    let a = board[condition[0]];
    let b = board[condition[1]];
    let c = board[condition[2]];
    if (a === '' || b === '' || c === '') continue;
    if (a === b && b === c) { roundWon = true; break; }
  }

  if (roundWon) {
    statusDisplay.innerHTML = `<span class="${currentPlayer === 'X' ? 'neon-cyan' : 'neon-pink'}">${currentPlayer} A GAGNÉ ! 🎉</span>`;
    gameActive = false;
    return;
  }

  if (!board.includes('')) {
    statusDisplay.innerHTML = '<span class="neon-cyan">MATCH NUL ! 🤝</span>';
    gameActive = false;
    return;
  }

  currentPlayer = currentPlayer === 'X' ? 'O' : 'X';
  playerDisplay.textContent = currentPlayer;
  playerDisplay.className = currentPlayer === 'X' ? 'neon-cyan' : 'neon-pink';
}

function resetGame() {
  board = ['', '', '', '', '', '', '', '', ''];
  currentPlayer = 'X';
  gameActive = true;
  statusDisplay.innerHTML = 'Tour du joueur : <span id="current-player" class="neon-cyan">X</span>';
  cells.forEach(cell => { cell.textContent = ''; cell.className = 'cell'; });
}

cells.forEach(c => c.addEventListener('click', handleCellClick));
document.getElementById('reset-btn').addEventListener('click', resetGame);"""
            }

        # Default fallback web app
        return {
            "description": f"Application Web Interactive ({app_type})",
            "html": f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{app_type.title()} - Jarvis Code Studio</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="box">
    <h1>🚀 {app_type.title()}</h1>
    <p>Application générée avec succès par HoL AI Jarvis Engine.</p>
    <button onclick="alert('Action exécutée !')">Cliquez-moi</button>
  </div>
  <script src="script.js"></script>
</body>
</html>""",
            "css": "body { background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; font-family: sans-serif; } .box { background: #1e293b; padding: 30px; border-radius: 12px; border: 1px solid #38bdf8; text-align: center; } button { background: #38bdf8; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 15px; }",
            "js": "console.log('App lancée avec succès.');"
        }

    @classmethod
    def create_and_preview_app(
        cls,
        app_name: str,
        description: str,
        html_content: str,
        css_content: str = "",
        js_content: str = "",
        open_browser: bool = False
    ) -> Dict[str, Any]:
        """
        Crée les fichiers physiques de l'application en local et prépare l'URL de prévisualisation.
        """
        safe_name = cls._sanitize_app_name(app_name)
        app_dir = os.path.join(cls.BASE_APPS_DIR, safe_name)
        os.makedirs(app_dir, exist_ok=True)

        html_file = os.path.join(app_dir, "index.html")
        css_file = os.path.join(app_dir, "style.css")
        js_file = os.path.join(app_dir, "script.js")

        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        if css_content:
            with open(css_file, "w", encoding="utf-8") as f:
                f.write(css_content)

        if js_content:
            with open(js_file, "w", encoding="utf-8") as f:
                f.write(js_content)

        preview_url = f"/apps/{safe_name}/index.html"
        full_http_url = f"http://localhost:8000/apps/{safe_name}/index.html"

        if open_browser:
            try:
                webbrowser.open(full_http_url)
            except Exception as e:
                logger.warning(f"Erreur d'ouverture dans le navigateur : {e}")

        verbal_reply = (
            f"L'application du {app_name} est prête, monsieur. "
            f"Les fichiers HTML, CSS et JavaScript sont créés en local. "
            f"Vous pouvez lancer la page immédiatement."
        )

        return {
            "status": "created",
            "app_name": safe_name,
            "description": description or f"Application {safe_name}",
            "preview_url": preview_url,
            "full_http_url": full_http_url,
            "files": {
                "html": html_file,
                "css": css_file if css_content else None,
                "js": js_file if js_content else None
            },
            "verbal_reply": verbal_reply
        }

    @classmethod
    def generate_app_template(cls, app_type: str, open_browser: bool = False) -> Dict[str, Any]:
        """Génère une application prête à l'emploi basée sur un modèle complet."""
        template = cls.get_template_for(app_type)
        return cls.create_and_preview_app(
            app_name=app_type,
            description=template["description"],
            html_content=template["html"],
            css_content=template["css"],
            js_content=template["js"],
            open_browser=open_browser
        )
