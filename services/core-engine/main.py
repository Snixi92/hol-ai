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
    print("=" * 70, flush=True)
    print("🌌 DÉMARRAGE DU SYSTÈME D'EXPLOITATION SPATIAL 'HoL AI'", flush=True)
    print(f"🌐 URL Cockpit Spatial : http://0.0.0.0:{port}", flush=True)
    print(f"📡 WebSocket Gateway   : ws://0.0.0.0:{port}/ws/canvas", flush=True)
    print("=" * 70, flush=True)

    try:
        from src.api.server import app
        print("✅ Module 'src.api.server:app' importé avec succès !", flush=True)
    except Exception as exc:
        print(f"❌ ERREUR CRITIQUE D'IMPORT : {exc}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    run()
