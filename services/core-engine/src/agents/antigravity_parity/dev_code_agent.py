"""
DevCodeAgent : Agent d'ingénierie logicielle et de manipulation de fichiers pour HoL AI.
Implémente les capacités de lecture, écriture, édition chirurgicale, recherche de fichiers
et exploration d'arborescence identiques à Antigravity (read_file, write_file, edit_file, list_dir, search_dir).
"""
import os
import re
import difflib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("hol_ai.dev_code_agent")


class DevCodeAgent:
    """Agent expert en lecture, écriture, édition et exploration de code."""

    @classmethod
    def read_file(
        cls,
        path: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lit le contenu d'un fichier texte avec support des plages de lignes (1-based).
        """
        target_path = Path(path).resolve()
        if not target_path.exists():
            return {
                "status": "error",
                "error": f"Fichier introuvable : {target_path}",
                "content": "",
                "total_lines": 0
            }

        if target_path.is_dir():
            return {
                "status": "error",
                "error": f"Le chemin spécifié est un répertoire, pas un fichier : {target_path}",
                "content": "",
                "total_lines": 0
            }

        # Lecture résiliente avec fallback d'encodages
        content = ""
        for encoding in ["utf-8", "cp1252", "latin-1"]:
            try:
                with open(target_path, "r", encoding=encoding, errors="replace") as f:
                    content = f.read()
                break
            except Exception:
                continue

        lines = content.splitlines(keepends=True)
        total_lines = len(lines)

        s_line = max(1, start_line) if start_line is not None else 1
        e_line = min(total_lines, end_line) if end_line is not None else total_lines

        if s_line > total_lines:
            selected_content = ""
        else:
            selected_content = "".join(lines[s_line - 1 : e_line])

        return {
            "status": "success",
            "path": str(target_path),
            "file_name": target_path.name,
            "total_lines": total_lines,
            "start_line": s_line,
            "end_line": e_line,
            "content": selected_content,
            "verbal_reply": f"Fichier {target_path.name} lu avec succès ({e_line - s_line + 1} lignes)."
        }

    @classmethod
    def write_file(
        cls,
        path: str,
        content: str,
        overwrite: bool = True,
        append: bool = False
    ) -> Dict[str, Any]:
        """
        Crée ou remplace un fichier avec création automatique des dossiers parents.
        """
        target_path = Path(path).resolve()

        if target_path.exists() and not overwrite and not append:
            return {
                "status": "error",
                "error": f"Le fichier existe déjà et overwrite=False : {target_path}",
                "path": str(target_path)
            }

        target_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"

        try:
            with open(target_path, mode, encoding="utf-8", errors="replace") as f:
                f.write(content)

            lines_count = len(content.splitlines())
            action = "ajouté" if append else "écrit"
            return {
                "status": "success",
                "path": str(target_path),
                "file_name": target_path.name,
                "bytes_written": len(content.encode("utf-8")),
                "lines_count": lines_count,
                "verbal_reply": f"Fichier {target_path.name} {action} avec succès ({lines_count} lignes)."
            }
        except Exception as e:
            logger.error(f"Erreur écriture fichier {target_path} : {e}")
            return {
                "status": "error",
                "error": str(e),
                "path": str(target_path)
            }

    @classmethod
    def edit_file(
        cls,
        path: str,
        target: str,
        replacement: str
    ) -> Dict[str, Any]:
        """
        Effectue un remplacement chirurgical d'un bloc de texte existant dans un fichier.
        """
        target_path = Path(path).resolve()
        if not target_path.exists():
            return {
                "status": "error",
                "error": f"Fichier introuvable pour édition : {target_path}",
                "path": str(target_path)
            }

        try:
            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                old_content = f.read()

            if target not in old_content:
                # Calcul d'un diff d'aide au diagnostic
                close = difflib.get_close_matches(target[:60], old_content.splitlines(), n=1)
                hint = f" Indice : ligne proche trouvée : '{close[0]}'" if close else ""
                return {
                    "status": "error",
                    "error": f"La cible spécifiée n'a pas été trouvée dans le fichier.{hint}",
                    "path": str(target_path)
                }

            occurrences = old_content.count(target)
            new_content = old_content.replace(target, replacement)

            with open(target_path, "w", encoding="utf-8", errors="replace") as f:
                f.write(new_content)

            return {
                "status": "success",
                "path": str(target_path),
                "file_name": target_path.name,
                "occurrences_replaced": occurrences,
                "verbal_reply": f"Édition chirurgicale réussie sur {target_path.name} ({occurrences} occurrence(s) remplacée(s))."
            }
        except Exception as e:
            logger.error(f"Erreur édition fichier {target_path} : {e}")
            return {
                "status": "error",
                "error": str(e),
                "path": str(target_path)
            }

    @classmethod
    def list_directory(
        cls,
        path: str = ".",
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """
        Explore un répertoire et retourne la liste hiérarchique des fichiers et dossiers.
        """
        root_dir = Path(path).resolve()
        if not root_dir.exists() or not root_dir.is_dir():
            return {
                "status": "error",
                "error": f"Dossier introuvable : {root_dir}",
                "entries": []
            }

        entries = []
        try:
            for root, dirs, files in os.walk(root_dir):
                # Filtrer les dossiers indésirables (.git, __pycache__, node_modules)
                dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", "node_modules", ".venv", "venv"]]
                rel_root = Path(root).relative_to(root_dir)
                depth = len(rel_root.parts)
                if depth >= max_depth:
                    continue

                for d in dirs:
                    entries.append({
                        "name": d,
                        "type": "directory",
                        "rel_path": str((rel_root / d).as_posix()),
                        "depth": depth + 1
                    })

                for f in files:
                    full_f = Path(root) / f
                    size = full_f.stat().st_size if full_f.exists() else 0
                    entries.append({
                        "name": f,
                        "type": "file",
                        "rel_path": str((rel_root / f).as_posix()),
                        "size_bytes": size,
                        "depth": depth + 1
                    })

            return {
                "status": "success",
                "root": str(root_dir),
                "total_entries": len(entries),
                "entries": entries[:200],  # Limite de sécurité
                "verbal_reply": f"Arborescence explorée : {len(entries)} éléments découverts."
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "entries": []}

    @classmethod
    def search_directory(
        cls,
        path: str = ".",
        pattern: str = "*",
        file_content_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recherche des fichiers par nom de pattern (glob) ou par contenu textuel.
        """
        root_dir = Path(path).resolve()
        if not root_dir.exists():
            return {"status": "error", "error": f"Dossier introuvable : {root_dir}", "matches": []}

        matches = []
        try:
            for p in root_dir.rglob(pattern):
                if any(ignored in p.parts for ignored in [".git", "__pycache__", "node_modules"]):
                    continue
                if p.is_file():
                    content_matched = True
                    match_snippet = ""
                    if file_content_query:
                        try:
                            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                                c = f.read()
                                if file_content_query.lower() in c.lower():
                                    idx = c.lower().find(file_content_query.lower())
                                    start = max(0, idx - 40)
                                    match_snippet = c[start : idx + 80].replace("\n", " ")
                                else:
                                    content_matched = False
                        except Exception:
                            content_matched = False

                    if content_matched:
                        matches.append({
                            "path": str(p),
                            "name": p.name,
                            "rel_path": str(p.relative_to(root_dir).as_posix()),
                            "size_bytes": p.stat().st_size,
                            "snippet": match_snippet
                        })
                        if len(matches) >= 50:
                            break

            return {
                "status": "success",
                "query": {"pattern": pattern, "content_query": file_content_query},
                "total_matches": len(matches),
                "matches": matches,
                "verbal_reply": f"Recherche terminée : {len(matches)} fichier(s) correspondant(s)."
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "matches": []}
