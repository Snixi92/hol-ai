"""
ArtifactsUIAgent : Agent de génération d'artefacts visuels et Generative UI pour HoL AI.
Implémente le système d'artefacts d'Antigravity :
- Documents Markdown structurés avec alertes GitHub et formules.
- Diagrammes Mermaid interactifs (flowchart, sequenceDiagram, erDiagram).
- Widgets HTML/CSS/JS autonomes (Generative UI) intégrés directement au cockpit spatial.
- Sauvegarde persistante des artefacts dans le dossier artifacts/.
"""
import os
import re
import time
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("hol_ai.artifacts_ui_agent")


class ArtifactsUIAgent:
    """Agent expert en production d'artefacts documentaires et visualisations interactives."""

    ARTIFACTS_DIR = Path("artifacts").resolve()

    @classmethod
    def _ensure_dir(cls) -> Path:
        cls.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        return cls.ARTIFACTS_DIR

    @classmethod
    def create_artifact(
        cls,
        title: str,
        artifact_type: str,  # 'markdown' | 'mermaid' | 'html_widget' | 'code_diff' | 'data_table'
        content: str,
        summary: str = "",
        user_facing: bool = True
    ) -> Dict[str, Any]:
        """
        Crée un artefact persistant et génère sa carte interactive pour l'affichage cockpit.
        """
        cls._ensure_dir()
        art_id = f"art_{uuid.uuid4().hex[:8]}"

        # Nettoyage nom de fichier
        clean_slug = re.sub(r"[^a-zA-Z0-9_\-]", "_", title.lower())[:40].strip("_") or "artifact"
        ext_map = {
            "markdown": ".md",
            "mermaid": ".mmd",
            "html_widget": ".html",
            "code_diff": ".diff",
            "data_table": ".json"
        }
        ext = ext_map.get(artifact_type.lower(), ".md")
        file_path = cls.ARTIFACTS_DIR / f"{clean_slug}_{art_id[:6]}{ext}"

        try:
            with open(file_path, "w", encoding="utf-8", errors="replace") as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Erreur sauvegarde artefact {file_path} : {e}")

        words_count = len(content.split())
        lines_count = len(content.splitlines())

        return {
            "status": "created",
            "artifact_id": art_id,
            "title": title,
            "type": artifact_type,
            "summary": summary or f"Artefact {artifact_type} : {title}",
            "file_path": str(file_path),
            "file_name": file_path.name,
            "content": content,
            "lines_count": lines_count,
            "words_count": words_count,
            "user_facing": user_facing,
            "created_at": time.time(),
            "verbal_reply": f"Artefact '{title}' ({artifact_type}) généré avec succès ({lines_count} lignes)."
        }

    @classmethod
    def generate_mermaid_diagram(
        cls,
        title: str,
        diagram_code: str,
        diagram_type: str = "flowchart TD"
    ) -> Dict[str, Any]:
        """
        Génère un diagramme Mermaid validé et l'encapsule dans un artefact Markdown.
        """
        code_clean = diagram_code.strip()
        if not any(code_clean.startswith(k) for k in ["flowchart", "graph", "sequenceDiagram", "stateDiagram", "classDiagram", "erDiagram"]):
            code_clean = f"{diagram_type}\n{code_clean}"

        md_content = f"### {title}\n\n```mermaid\n{code_clean}\n```\n"
        return cls.create_artifact(
            title=title,
            artifact_type="mermaid",
            content=md_content,
            summary=f"Diagramme visuel : {title}"
        )

    @classmethod
    def generate_interactive_widget(
        cls,
        title: str,
        html_content: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Crée un widget HTML5 autonome avec style néon-cyberpunk pour le cockpit spatial.
        """
        full_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background: #07090e; color: #f1f5f9; font-family: system-ui, sans-serif; }}
    </style>
</head>
<body class="p-6">
    <div class="max-w-2xl mx-auto bg-slate-900/80 border border-cyan-500/30 rounded-2xl p-6 shadow-2xl backdrop-blur-xl">
        <h2 class="text-xl font-bold text-cyan-400 mb-2">{title}</h2>
        <p class="text-xs text-slate-400 mb-6">{description}</p>
        <div id="widget-container">
            {html_content}
        </div>
    </div>
</body>
</html>"""
        return cls.create_artifact(
            title=title,
            artifact_type="html_widget",
            content=full_html,
            summary=description or f"Widget interactif : {title}"
        )
