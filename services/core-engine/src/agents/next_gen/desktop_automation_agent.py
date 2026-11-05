"""
DesktopAutomationAgent : Contrôle Graphique et Automatisation du Bureau Windows pour HoL AI.
Permet d'interagir nativement avec l'OS Windows : lister les fenêtres actives, focaliser une application,
lancer des programmes, simuler des raccourcis clavier et surveiller l'état matériel avec garde-fous Sentinel.
"""
import os
import sys
import time
import shutil
import platform
import tempfile
import subprocess
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("hol_ai.desktop_automation")

# Applications Windows courantes et leurs commandes d'exécution
APP_CATALOG = {
    "lenovo vantage": ["powershell", "-NoProfile", "-Command", "Start-Process 'lenovovantage:'"],
    "vantage": ["powershell", "-NoProfile", "-Command", "Start-Process 'lenovovantage:'"],
    "calculatrice": ["calc.exe"],
    "calculator": ["calc.exe"],
    "calc": ["calc.exe"],
    "bloc-notes": ["notepad.exe"],
    "notepad": ["notepad.exe"],
    "explorateur": ["explorer.exe"],
    "explorer": ["explorer.exe"],
    "fichiers": ["explorer.exe"],
    "chrome": ["chrome.exe"],
    "google chrome": ["chrome.exe"],
    "edge": ["msedge.exe"],
    "microsoft edge": ["msedge.exe"],
    "spotify": ["powershell", "-NoProfile", "-Command", "Start-Process 'spotify:'"],
    "discord": ["powershell", "-NoProfile", "-Command", "Start-Process 'discord:'"],
    "paramètres": ["powershell", "-NoProfile", "-Command", "Start-Process 'ms-settings:'"],
    "settings": ["powershell", "-NoProfile", "-Command", "Start-Process 'ms-settings:'"],
    "terminal": ["wt.exe"],
    "cmd": ["cmd.exe"],
    "invite de commandes": ["cmd.exe"],
    "powershell": ["powershell.exe"],
    "taskmgr": ["taskmgr.exe"],
    "gestionnaire des tâches": ["taskmgr.exe"]
}

# Garde-fous Sentinel : processus et commandes système protégés contre toute fermeture ou altération
PROTECTED_PROCESSES = {
    "csrss", "smss", "wininit", "services", "lsass", "svchost",
    "winlogon", "dwm", "explorer", "system", "idle", "registry"
}


class DesktopAutomationAgent:
    """Agent expert de l'automatisation Windows et du pilotage du bureau."""

    _apps_cache: tuple[float, List[Dict[str, Any]]] = (0.0, [])
    CACHE_TTL_SECONDS: float = 2.0

    @classmethod
    def list_running_applications(cls) -> List[Dict[str, Any]]:
        """
        Liste toutes les fenêtres applicatives visibles sur le bureau Windows avec leur PID et titre.
        Muni d'un cache court pour protéger les boucles de stress-tests.
        """
        now = time.time()
        if hasattr(cls, "_apps_cache") and (now - cls._apps_cache[0]) < cls.CACHE_TTL_SECONDS:
            return list(cls._apps_cache[1])

        temp_dir = tempfile.gettempdir()
        ps_file = os.path.join(temp_dir, f"hol_list_wins_{os.getpid()}.ps1")

        ps_script = """
Get-Process | Where-Object { $_.MainWindowTitle.Length -gt 0 } | ForEach-Object {
    [PSCustomObject]@{
        Id = $_.Id
        ProcessName = $_.ProcessName
        Title = $_.MainWindowTitle
    }
} | ConvertTo-Json -Compress
"""
        try:
            with open(ps_file, "w", encoding="utf-8") as f:
                f.write(ps_script)

            res = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_file],
                capture_output=True,
                text=True,
                timeout=10
            )

            import json
            raw_out = res.stdout.strip()
            if not raw_out:
                cls._apps_cache = (now, [])
                return []
            parsed = json.loads(raw_out)
            result = []
            if isinstance(parsed, dict):
                result = [parsed]
            elif isinstance(parsed, list):
                result = parsed
            cls._apps_cache = (now, result)
            return result
        except Exception as e:
            logger.error(f"Erreur listage fenêtres: {e}")
            return []
        finally:
            if os.path.exists(ps_file):
                try:
                    os.remove(ps_file)
                except Exception:
                    pass

    list_open_windows = list_running_applications

    @classmethod
    def launch_application(cls, app_name: str) -> Dict[str, Any]:
        """
        Lance une application bureautique ou du Windows Store en toute sécurité.
        """
        clean_name = app_name.lower().strip()
        cmd = None
        for key, val in APP_CATALOG.items():
            if key in clean_name or clean_name in key:
                cmd = val
                break

        if not cmd:
            # Recherche générique dans le PATH
            exe_found = shutil.which(clean_name) or shutil.which(f"{clean_name}.exe")
            if exe_found:
                cmd = [exe_found]
            else:
                # Tentative Start-Process PowerShell
                cmd = ["powershell", "-NoProfile", "-Command", f"Start-Process '{clean_name}'"]

        try:
            proc = subprocess.Popen(cmd, shell=False)
            return {
                "success": True,
                "app_name": app_name,
                "command_executed": " ".join(cmd),
                "pid": proc.pid,
                "message": f"Application '{app_name}' lancée avec succès."
            }
        except Exception as e:
            logger.error(f"Erreur lancement application '{app_name}': {e}")
            return {"success": False, "error": str(e), "app_name": app_name}

    @classmethod
    def focus_window(cls, window_title_or_process: str) -> Dict[str, Any]:
        """
        Met au premier plan une application en cours d'exécution.
        """
        clean_target = window_title_or_process.replace('"', '""').replace("'", "''")
        temp_dir = tempfile.gettempdir()
        ps_file = os.path.join(temp_dir, f"hol_focus_{os.getpid()}.ps1")

        ps_script = f"""
$wshell = New-Object -ComObject WScript.Shell
$proc = Get-Process | Where-Object {{ $_.MainWindowTitle -like '*{clean_target}*' -or $_.ProcessName -like '*{clean_target}*' }} | Select-Object -First 1
if ($proc) {{
    $wshell.AppActivate($proc.Id) | Out-Null
    Write-Output "FOCUSED:$($proc.ProcessName):$($proc.Id)"
}} else {{
    Write-Output "NOT_FOUND"
}}
"""
        try:
            with open(ps_file, "w", encoding="utf-8") as f:
                f.write(ps_script)

            res = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_file],
                capture_output=True,
                text=True,
                timeout=8
            )
            out = res.stdout.strip()
            if out.startswith("FOCUSED:"):
                parts = out.split(":")
                return {"success": True, "process": parts[1], "pid": int(parts[2]) if len(parts) > 2 else 0}
            return {"success": False, "error": f"Fenêtre '{window_title_or_process}' non trouvée"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if os.path.exists(ps_file):
                try:
                    os.remove(ps_file)
                except Exception:
                    pass

    @classmethod
    def send_keystrokes(cls, keys: str, target_window: Optional[str] = None) -> Dict[str, Any]:
        """
        Envoie des touches de clavier ou raccourcis à la fenêtre cible ou active.
        """
        temp_dir = tempfile.gettempdir()
        ps_file = os.path.join(temp_dir, f"hol_keys_{os.getpid()}.ps1")

        activate_block = ""
        if target_window:
            clean_win = target_window.replace("'", "''")
            activate_block = f"""
$p = Get-Process | Where-Object {{ $_.MainWindowTitle -like '*{clean_win}*' -or $_.ProcessName -like '*{clean_win}*' }} | Select-Object -First 1
if ($p) {{ $wshell.AppActivate($p.Id) | Out-Null; Start-Sleep -Milliseconds 200 }}
"""

        clean_keys = keys.replace("'", "''")
        ps_script = f"""
$wshell = New-Object -ComObject WScript.Shell
{activate_block}
$wshell.SendKeys('{clean_keys}')
Write-Output "KEYS_SENT"
"""
        try:
            with open(ps_file, "w", encoding="utf-8") as f:
                f.write(ps_script)

            res = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_file],
                capture_output=True,
                text=True,
                timeout=8
            )
            return {"success": "KEYS_SENT" in res.stdout, "keys": keys}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if os.path.exists(ps_file):
                try:
                    os.remove(ps_file)
                except Exception:
                    pass

    @classmethod
    def close_application(cls, process_or_title: str, force: bool = False) -> Dict[str, Any]:
        """
        Ferme une application en respectant les gardes-fous Sentinel (aucun processus système critique).
        """
        clean_target = process_or_title.lower().strip()
        if clean_target in PROTECTED_PROCESSES:
            return {
                "success": False,
                "error": f"Sécurité Sentinel : Le processus '{clean_target}' est un composant Windows vital protégé."
            }

        flag = "-Force" if force else ""
        temp_dir = tempfile.gettempdir()
        ps_file = os.path.join(temp_dir, f"hol_close_{os.getpid()}.ps1")

        ps_script = f"""
$procs = Get-Process | Where-Object {{ $_.ProcessName -like '*{clean_target}*' -or $_.MainWindowTitle -like '*{clean_target}*' }}
$closed = 0
foreach ($p in $procs) {{
    Stop-Process -Id $p.Id {flag} -ErrorAction SilentlyContinue
    $closed++
}}
Write-Output "CLOSED:$closed"
"""
        try:
            with open(ps_file, "w", encoding="utf-8") as f:
                f.write(ps_script)

            res = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            out = res.stdout.strip()
            count = int(out.split(":")[1]) if "CLOSED:" in out else 0
            return {"success": count > 0, "closed_count": count, "target": process_or_title}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if os.path.exists(ps_file):
                try:
                    os.remove(ps_file)
                except Exception:
                    pass

    @classmethod
    def get_hardware_telemetry(cls) -> Dict[str, Any]:
        """
        Récupère l'état matériel et les métriques système du PC hôte (CPU, RAM, OS, écran).
        """
        try:
            import psutil
            mem = psutil.virtual_memory()
            cpu_pct = psutil.cpu_percent(interval=0.1)
            battery = psutil.sensors_battery()
            battery_info = {
                "percent": battery.percent if battery else None,
                "plugged": battery.power_plugged if battery else None
            } if battery else None
        except Exception:
            mem = None
            cpu_pct = None
            battery_info = None

        return {
            "os": f"Windows {platform.release()} ({platform.version()})",
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_usage_percent": cpu_pct,
            "memory_total_gb": round(mem.total / (1024**3), 2) if mem else None,
            "memory_used_gb": round(mem.used / (1024**3), 2) if mem else None,
            "memory_percent": mem.percent if mem else None,
            "battery": battery_info,
            "timestamp": time.time()
        }
