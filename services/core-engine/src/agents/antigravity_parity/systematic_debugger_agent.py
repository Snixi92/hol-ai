"""
SystematicDebuggerAgent : Agent de diagnostic d'erreurs, crash-tests et post-mortem pour HoL AI.
Implémente la méthodologie systematic-debugging d'Antigravity :
- Parsing automatisé des traces de pile (stack-traces Python, JavaScript, Shell).
- Localisation du fichier fautif, de la ligne exacte et de l'exception levée.
- Exécution de suites de tests de non-régression (pytest).
- Rédaction d'analyses de cause racine (Root Cause Analysis - RCA).
"""
import re
import time
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("hol_ai.systematic_debugger")


class SystematicDebuggerAgent:
    """Agent expert en débogage méthodique, analyse de traces d'erreur et non-régression."""

    @classmethod
    def parse_stack_trace(cls, error_text: str) -> Dict[str, Any]:
        """
        Extrait les informations clés d'une trace d'erreur (fichiers, lignes, type d'exception).
        """
        if not error_text:
            return {"status": "empty", "error_type": "Unknown", "frames": []}

        frames = []
        # Pattern standard Python Traceback
        py_frame_pattern = r'File "([^"]+)", line (\d+), in ([^\n]+)\n\s+([^\n]+)'
        for m in re.finditer(py_frame_pattern, error_text):
            frames.append({
                "file": m.group(1),
                "line": int(m.group(2)),
                "function": m.group(3).strip(),
                "code": m.group(4).strip()
            })

        # Extraction de la dernière ligne d'erreur (ex: ValueError: invalid literal...)
        last_line = error_text.strip().splitlines()[-1] if error_text.strip() else ""
        error_type = "Exception"
        error_message = last_line
        if ":" in last_line:
            parts = last_line.split(":", 1)
            error_type = parts[0].strip()
            error_message = parts[1].strip()

        culprit_frame = frames[-1] if frames else None

        return {
            "status": "parsed",
            "error_type": error_type,
            "error_message": error_message,
            "total_frames": len(frames),
            "culprit_file": culprit_frame["file"] if culprit_frame else None,
            "culprit_line": culprit_frame["line"] if culprit_frame else None,
            "culprit_code": culprit_frame["code"] if culprit_frame else None,
            "frames": frames
        }

    @classmethod
    def diagnose_and_suggest_fix(
        cls,
        error_text: str,
        associated_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyse une anomalie et formule une hypothèse de cause racine avec plan de remédiation.
        """
        parsed = cls.parse_stack_trace(error_text)
        etype = parsed.get("error_type", "Exception")
        emsg = parsed.get("error_message", "")
        culprit = parsed.get("culprit_file")
        line = parsed.get("culprit_line")

        # Règles heuristiques systématiques
        hypothesis = "Erreur d'exécution standard."
        fix_suggestion = "Vérifier la cohérence des paramètres d'appel."

        if "NameError" in etype:
            var_name = re.search(r"name '([^']+)' is not defined", emsg)
            v = var_name.group(1) if var_name else "inconnue"
            hypothesis = f"La variable ou fonction '{v}' est utilisée avant sa définition ou hors de sa portée."
            fix_suggestion = f"Définir ou importer '{v}' avant son appel à la ligne {line}."
        elif "TypeError" in etype:
            hypothesis = f"Incompatibilité de types lors de l'opération : {emsg}"
            fix_suggestion = "Ajouter une validation de type préalable ou un cast explicite (ex: int(), str())."
        elif "FileNotFoundError" in etype:
            hypothesis = "Le chemin de fichier ciblé n'existe pas sur le système."
            fix_suggestion = "Utiliser Path(p).resolve() et vérifier Path.exists() avant ouverture."
        elif "IndexError" in etype or "KeyError" in etype:
            hypothesis = "Accès à un élément de liste ou clé de dictionnaire inexistante."
            fix_suggestion = "Remplacer l'accès direct par .get(key, default) ou vérifier len() > index."
        elif "UnicodeEncodeError" in etype or "UnicodeDecodeError" in etype:
            hypothesis = "Conflit d'encodage texte (ex: console Windows cp1252 vs emojis UTF-8)."
            fix_suggestion = "Reconfigurer stdout en UTF-8 : sys.stdout.reconfigure(encoding='utf-8', errors='replace')."

        return {
            "status": "diagnosed",
            "error_type": etype,
            "error_message": emsg,
            "culprit_file": culprit,
            "culprit_line": line,
            "hypothesis": hypothesis,
            "fix_suggestion": fix_suggestion,
            "verbal_reply": f"Diagnostic : {etype} à la ligne {line} de {culprit}. Cause identifiée : {hypothesis}"
        }

    @classmethod
    def run_tests(cls, test_target: str = "tests") -> Dict[str, Any]:
        """
        Exécute la suite de tests pytest et extrait le rapport de réussite/échec.
        """
        t0 = time.time()
        try:
            cmd = ["pytest", test_target, "-v", "--tb=short"]
            res = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=60)
            elapsed = round(time.time() - t0, 2)

            stdout = res.stdout
            passed_m = re.search(r"(\d+) passed", stdout)
            failed_m = re.search(r"(\d+) failed", stdout)

            passed = int(passed_m.group(1)) if passed_m else 0
            failed = int(failed_m.group(1)) if failed_m else 0

            return {
                "status": "success" if res.returncode == 0 else "tests_failed",
                "returncode": res.returncode,
                "duration_sec": elapsed,
                "passed": passed,
                "failed": failed,
                "output_snippet": stdout[-2000:] if len(stdout) > 2000 else stdout,
                "verbal_reply": f"Tests terminés en {elapsed}s : {passed} passed, {failed} failed."
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "passed": 0, "failed": 0}
