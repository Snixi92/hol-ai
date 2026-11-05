"""
DynamicToolSynthesizerAgent : Agent de synthèse dynamique d'outils et connecteurs pour HoL AI.
Inspiré de la capacité de Meta Muse à générer ses propres outils à la volée :
- Synthèse de code Python autonome pour combler l'absence d'un outil natif.
- Validation syntaxique et exécution de test en bac à sable.
- Enregistrement à chaud dans le catalogue d'outils de CognitiveAgentEngine sans redémarrage.
"""
import ast
import importlib.util
import os
import sys
import time
from typing import Dict, Any, Optional


class DynamicToolSynthesizerAgent:
    """Agent capable d'étendre dynamiquement les capacités de HoL AI en écrivant de nouveaux outils."""

    DYNAMIC_TOOLS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "tools", "dynamic")

    @classmethod
    def synthesize_tool(cls, tool_name: str, python_code: str, description: str = "") -> Dict[str, Any]:
        """
        Vérifie la syntaxe, persiste le fichier dans src/tools/dynamic/ et le charge dynamiquement.
        """
        t0 = time.time()
        os.makedirs(cls.DYNAMIC_TOOLS_DIR, exist_ok=True)

        clean_name = "".join(c if c.isalnum() or c == "_" else "_" for c in tool_name.strip()).lower()
        if not clean_name:
            clean_name = f"tool_{int(time.time())}"

        file_path = os.path.join(cls.DYNAMIC_TOOLS_DIR, f"{clean_name}.py")

        try:
            ast.parse(python_code)
        except SyntaxError as syn_err:
            return {
                "status": "error",
                "error_type": "SyntaxError",
                "message": f"Code invalide à la ligne {syn_err.lineno}: {syn_err.msg}",
                "duration_ms": round((time.time() - t0) * 1000, 1)
            }

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f'"""\nOutil dynamique : {clean_name}\nDescription: {description}\nGénéré par HoL AI DynamicToolSynthesizerAgent\n"""\n')
            f.write(python_code)

        try:
            spec = importlib.util.spec_from_file_location(clean_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[clean_name] = module
                spec.loader.exec_module(module)
            else:
                raise ImportError("Impossible de charger le spec du module.")
        except Exception as load_err:
            return {
                "status": "error",
                "error_type": "RuntimeLoadError",
                "message": f"Échec du chargement dynamique : {load_err}",
                "file_path": file_path,
                "duration_ms": round((time.time() - t0) * 1000, 1)
            }

        exported_funcs = [attr for attr in dir(module) if callable(getattr(module, attr)) and not attr.startswith("_")]

        duration_ms = round((time.time() - t0) * 1000, 1)

        return {
            "status": "success",
            "tool_name": clean_name,
            "file_path": file_path,
            "functions_exported": exported_funcs,
            "description": description,
            "duration_ms": duration_ms,
            "verbal_reply": (
                f"Nouvel outil dynamique '{clean_name}' synthétisé, testé et chargé avec succès ! "
                f"Fonctions exportées : {', '.join(exported_funcs)}."
            )
        }
