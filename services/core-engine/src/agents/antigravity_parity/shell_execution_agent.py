"""
ShellExecutionAgent : Agent d'exécution de commandes système et gestion des processus pour HoL AI.
Implémente les capacités de run_command d'Antigravity avec protection contre les commandes destructrices,
gestion de timeout, capture propre des sorties, monitoring des processus et sandboxing.
"""
import os
import sys
import time
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("hol_ai.shell_execution_agent")


class ShellExecutionAgent:
    """Agent expert en exécution de scripts shell et supervision système."""

    BLOCKED_PATTERNS = [
        r"format\s+[a-zA-Z]:",
        r"del\s+/[sfq]\s+[a-zA-Z]:\\windows",
        r"rmdir\s+/[sq]\s+[a-zA-Z]:\\windows",
        r"rm\s+-rf\s+/\s*$",
        r"drop\s+database",
        r":\(\)\s*\{\s*:\|:&\s*\};:",  # Fork bomb
    ]

    @classmethod
    def _is_safe_command(cls, command: str) -> bool:
        """Vérifie qu'une commande n'est pas manifestement destructrice pour l'OS."""
        cmd_clean = command.strip().lower()
        import re
        for pattern in cls.BLOCKED_PATTERNS:
            if re.search(pattern, cmd_clean, re.IGNORECASE):
                return False
        return True

    @classmethod
    def run_command(
        cls,
        command: str,
        timeout_sec: int = 30,
        working_dir: Optional[str] = None,
        is_background: bool = False
    ) -> Dict[str, Any]:
        """
        Exécute une commande terminal de manière sécurisée et retourne stdout, stderr et returncode.
        """
        if not command or not command.strip():
            return {
                "status": "error",
                "error": "Commande vide non autorisée",
                "stdout": "",
                "stderr": "",
                "returncode": -1
            }

        if not cls._is_safe_command(command):
            logger.warning(f"Commande bloquée pour sécurité : {command}")
            return {
                "status": "blocked",
                "error": "Commande bloquée par la politique de sécurité (protection système active).",
                "stdout": "",
                "stderr": "Access Denied: Commande potentiellement destructrice.",
                "returncode": 403
            }

        cwd = str(Path(working_dir).resolve()) if working_dir else os.getcwd()
        t0 = time.time()

        if is_background:
            try:
                # Lancement détaché en arrière-plan
                flags = subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0
                proc = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=cwd,
                    creationflags=flags,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return {
                    "status": "launched_background",
                    "pid": proc.pid,
                    "command": command,
                    "returncode": 0,
                    "verbal_reply": f"Processus lancé en tâche de fond (PID: {proc.pid})."
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "returncode": -1
                }

        try:
            res = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_sec
            )
            elapsed_ms = round((time.time() - t0) * 1000, 1)

            stdout_clean = res.stdout.strip()
            stderr_clean = res.stderr.strip()

            return {
                "status": "success" if res.returncode == 0 else "failed",
                "command": command,
                "returncode": res.returncode,
                "stdout": stdout_clean[:8000],  # Limite d'affichage de sécurité
                "stderr": stderr_clean[:4000],
                "duration_ms": elapsed_ms,
                "working_dir": cwd,
                "verbal_reply": f"Commande exécutée en {elapsed_ms}ms (code {res.returncode})."
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": f"La commande a dépassé le délai maximal imparti ({timeout_sec}s).",
                "stdout": "",
                "stderr": "Execution Timeout",
                "returncode": 124,
                "duration_ms": timeout_sec * 1000
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }

    @classmethod
    def list_running_processes(cls, filter_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Liste les processus système en cours d'exécution.
        """
        procs = []
        try:
            if sys.platform == "win32":
                cmd = ["tasklist", "/FO", "CSV", "/NH"]
                res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
                if res.returncode == 0:
                    import csv, io
                    reader = csv.reader(io.StringIO(res.stdout))
                    for row in reader:
                        if len(row) >= 5:
                            name, pid, s_name, s_num, mem = row[0], row[1], row[2], row[3], row[4]
                            if not filter_name or filter_name.lower() in name.lower():
                                procs.append({
                                    "name": name,
                                    "pid": pid,
                                    "session": s_name,
                                    "memory": mem
                                })
            else:
                cmd = ["ps", "-eo", "pid,comm,%mem"]
                res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
                for line in res.stdout.splitlines()[1:]:
                    parts = line.split()
                    if len(parts) >= 3:
                        if not filter_name or filter_name.lower() in parts[1].lower():
                            procs.append({"pid": parts[0], "name": parts[1], "memory": parts[2]})

            return {
                "status": "success",
                "total": len(procs),
                "processes": procs[:100],
                "verbal_reply": f"{len(procs)} processus répertoriés."
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "processes": []}

    @classmethod
    def kill_process(cls, target: str) -> Dict[str, Any]:
        """
        Arrête un processus par son PID ou son nom.
        """
        try:
            if sys.platform == "win32":
                if target.isdigit():
                    cmd = ["taskkill", "/PID", target, "/F", "/T"]
                else:
                    name = target if target.endswith(".exe") else f"{target}.exe"
                    cmd = ["taskkill", "/IM", name, "/F", "/T"]
            else:
                cmd = ["kill", "-9", target]

            res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
            success = res.returncode == 0
            return {
                "status": "closed" if success else "failed",
                "target": target,
                "returncode": res.returncode,
                "output": res.stdout.strip() or res.stderr.strip(),
                "verbal_reply": f"Processus {target} arrêté avec succès." if success else f"Impossible d'arrêter {target}."
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "target": target}
