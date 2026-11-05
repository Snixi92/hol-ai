import sys
from pathlib import Path

# Ajouter services/core-engine au sys.path
root_dir = Path(__file__).resolve().parent.parent
core_engine_dir = root_dir / "services" / "core-engine"
if str(core_engine_dir) not in sys.path:
    sys.path.insert(0, str(core_engine_dir))

from src.api.server import app

# Export pour Vercel Serverless
__all__ = ["app"]
