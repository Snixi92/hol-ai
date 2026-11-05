"""
Point d'entrée du serveur FastAPI / WebSocket pour HoL AI.
Compatible Local, Docker, Render ($PORT=10000) et Cloud.
"""
import os
import sys
from pathlib import Path

# Force UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Inclusion du chemin racine
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import uvicorn


def run():
    port = int(os.environ.get("PORT", 8000))
    print("=" * 70)
    print("🌌 DÉMARRAGE DU SYSTÈME D'EXPLOITATION SPATIAL 'HoL AI'")
    print(f"🌐 URL Cockpit Spatial : http://0.0.0.0:{port}")
    print(f"📡 WebSocket Gateway   : ws://0.0.0.0:{port}/ws/canvas")
    print("=" * 70)
    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False
    )


if __name__ == "__main__":
    run()
