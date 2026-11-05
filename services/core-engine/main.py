"""
Point d'entrée du serveur FastAPI / WebSocket pour HoL AI.
"""
import sys
from pathlib import Path

# Force UTF-8 stdout sur les consoles Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Inclusion du chemin racine
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import uvicorn


def run():
    print("=" * 70)
    print("🌌 DÉMARRAGE DU SYSTÈME D'EXPLOITATION SPATIAL 'HoL AI'")
    print("🌐 URL Cockpit Spatial : http://127.0.0.1:8000")
    print("📡 WebSocket Gateway   : ws://127.0.0.1:8000/ws/canvas")
    print("=" * 70)
    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )


if __name__ == "__main__":
    run()
