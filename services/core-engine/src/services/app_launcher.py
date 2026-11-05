"""
Service de lancement et de fermeture universelle d'applications Windows pour Jarvis.
Indexe dynamiquement ABSOLUMENT TOUTES les applications installées sur le système
(via Get-StartApps, registre et raccourcis) et permet de les ouvrir ou fermer à la voix.
"""
import os
import sys
import json
import shutil
import logging
import difflib
import unicodedata
import webbrowser
import subprocess
from typing import Dict, Any, List, Optional

logger = logging.getLogger("hol_ai.app_launcher")


def normalize_text(text: str) -> str:
    """Supprime les accents, minuscules, caractères spéciaux pour matching tolérant."""
    if not text:
        return ""
    nfkd = unicodedata.normalize('NFKD', text.lower())
    ascii_text = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return "".join(c for c in ascii_text if c.isalnum() or c.isspace()).strip()


class AppLauncherService:
    """Contrôleur universel de processus et d'applications Windows."""

    # Applications prioritaires et correspondances de processus
    KNOWN_PROCESS_MAPPINGS: Dict[str, List[str]] = {
        "calculatrice": ["CalculatorApp", "calc"],
        "calculator": ["CalculatorApp", "calc"],
        "calculette": ["CalculatorApp", "calc"],
        "bloc-notes": ["Notepad", "notepad"],
        "bloc notes": ["Notepad", "notepad"],
        "notepad": ["Notepad", "notepad"],
        "discord": ["Discord", "discord"],
        "spotify": ["Spotify", "spotify"],
        "chrome": ["chrome"],
        "google chrome": ["chrome"],
        "firefox": ["firefox"],
        "edge": ["msedge"],
        "microsoft edge": ["msedge"],
        "steam": ["steam", "steamwebhelper", "steamservice"],
        "lenovo": ["LenovoVantage", "LenovoVantageService"],
        "vantage": ["LenovoVantage", "LenovoVantageService"],
        "lenovo vantage": ["LenovoVantage", "LenovoVantageService"],
        "parametres": ["SystemSettings"],
        "reglages": ["SystemSettings"],
        "configuration": ["SystemSettings"],
        "photos": ["Microsoft.Photos"],
        "mes photos": ["Microsoft.Photos"],
        "galerie": ["Microsoft.Photos"],
        "gestionnaire des taches": ["Taskmgr", "taskmgr"],
        "gestionnaire de taches": ["Taskmgr", "taskmgr"],
        "taches": ["Taskmgr", "taskmgr"],
        "taskmgr": ["Taskmgr", "taskmgr"],
        "paint": ["mspaint", "PaintApp"],
        "dessin": ["mspaint", "PaintApp"],
        "musique": ["Spotify", "spotify"],
        "chanson": ["Spotify", "spotify"],
        "playlist": ["Spotify", "spotify"],
        "navigateur": ["chrome", "msedge", "firefox"],
        "internet": ["chrome", "msedge", "firefox"],
        "web": ["chrome", "msedge", "firefox"],
        "mail": ["OUTLOOK", "outlook", "HxOutlook"],
        "mails": ["OUTLOOK", "outlook", "HxOutlook"],
        "mes mails": ["OUTLOOK", "outlook", "HxOutlook"],
        "boite mail": ["OUTLOOK", "outlook", "HxOutlook"],
        "camera": ["WindowsCamera"],
        "webcam": ["WindowsCamera"],
        "micro": ["SoundRec"],
        "dictaphone": ["SoundRec"],
        "vscode": ["Code", "code"],
        "vs code": ["Code", "code"],
        "code": ["Code", "code"],
        "visual studio code": ["Code", "code"],
        "word": ["WINWORD", "winword"],
        "excel": ["EXCEL", "excel"],
        "powerpoint": ["POWERPNT", "powerpnt"],
        "outlook": ["OUTLOOK", "outlook"],
        "terminal": ["WindowsTerminal", "powershell", "cmd"],
        "powershell": ["powershell"],
        "cmd": ["cmd"],
        "antigravity": ["Antigravity"],
        "ea": ["EADesktop", "EALauncher"],
        "epic": ["EpicGamesLauncher"],
        "vlc": ["vlc"],
        "whatsapp": ["WhatsApp"],
        "telegram": ["Telegram"],
        "fortnite": ["FortniteClient-Win64-Shipping", "FortniteLauncher", "EpicGamesLauncher"],
        "gta": ["GTA5", "PlayGTAV", "RockstarService"],
        "gta 5": ["GTA5", "PlayGTAV", "RockstarService"],
        "gta v": ["GTA5", "PlayGTAV", "RockstarService"],
        "gta5": ["GTA5", "PlayGTAV", "RockstarService"],
        "grand theft auto": ["GTA5", "PlayGTAV", "RockstarService"],
        "rdr": ["RDR2", "PlayRDR2"],
        "rdr2": ["RDR2", "PlayRDR2"],
        "rdr 2": ["RDR2", "PlayRDR2"],
        "red dead": ["RDR2", "PlayRDR2"],
        "roblox": ["RobloxPlayerBeta", "RobloxStudioBeta"],
        "lm studio": ["LM Studio", "lmstudio"],
        "nuvio": ["Nuvio", "electron"],
        "openiv": ["OpenIV"],
        "wiztree": ["WizTree", "WizTree64"],
        "megasync": ["MEGAsync"],
        "nvidia": ["NVIDIA App", "NVDisplay.Container"],
        "rockstar": ["Launcher", "RockstarService"],
        "ubisoft": ["upc", "UbisoftConnect"]
    }

    APP_REGISTRY: Dict[str, Dict[str, Any]] = {
        "discord": {
            "exe": ["discord.exe", "Discord.exe"],
            "protocol": "discord://",
            "web_url": "https://discord.com/app",
            "name": "Discord"
        },
        "spotify": {
            "exe": ["spotify.exe", "Spotify.exe"],
            "protocol": "spotify://",
            "web_url": "https://open.spotify.com",
            "name": "Spotify"
        },
        "chrome": {
            "exe": ["chrome.exe", "googlechrome.exe"],
            "protocol": None,
            "web_url": "https://google.com",
            "name": "Google Chrome"
        },
        "instagram": {
            "exe": [],
            "protocol": None,
            "web_url": "https://instagram.com",
            "name": "Instagram"
        },
        "emails": {
            "exe": ["outlook.exe"],
            "protocol": "mailto:",
            "web_url": "https://mail.google.com",
            "name": "Boîte Emails (Gmail)"
        },
        "gmail": {
            "exe": [],
            "protocol": None,
            "web_url": "https://mail.google.com",
            "name": "Gmail"
        },
        "vscode": {
            "exe": ["code.cmd", "code.exe", "Code.exe"],
            "protocol": "vscode://",
            "web_url": "https://vscode.dev",
            "name": "Visual Studio Code"
        },
        "calculatrice": {
            "exe": ["calc.exe"],
            "protocol": "calculator:",
            "web_url": None,
            "name": "Calculatrice Windows"
        },
        "terminal": {
            "exe": ["wt.exe", "powershell.exe"],
            "protocol": None,
            "web_url": None,
            "name": "Terminal Windows"
        },
        "notion": {
            "exe": ["notion.exe", "Notion.exe"],
            "protocol": "notion://",
            "web_url": "https://notion.so",
            "name": "Notion"
        },
        "youtube": {
            "exe": [],
            "protocol": None,
            "web_url": "https://youtube.com",
            "name": "YouTube"
        },
        "fichiers": {
            "exe": ["explorer.exe"],
            "protocol": None,
            "web_url": None,
            "name": "Explorateur de fichiers"
        },
        "explorateur": {
            "exe": ["explorer.exe"],
            "protocol": None,
            "web_url": None,
            "name": "Explorateur de fichiers"
        },
        "parametres": {
            "exe": ["SystemSettings.exe"],
            "protocol": "ms-settings:",
            "web_url": None,
            "name": "Paramètres Windows"
        },
        "photos": {
            "exe": [],
            "protocol": "ms-photos:",
            "web_url": None,
            "name": "Photos Windows"
        },
        "gestionnaire des taches": {
            "exe": ["taskmgr.exe"],
            "protocol": None,
            "web_url": None,
            "name": "Gestionnaire des tâches"
        },
        "paint": {
            "exe": ["mspaint.exe"],
            "protocol": "ms-paint:",
            "web_url": None,
            "name": "Paint"
        },
        "camera": {
            "exe": [],
            "protocol": "microsoft.windows.camera:",
            "web_url": None,
            "name": "Caméra Windows"
        },
        "steam": {
            "exe": ["steam.exe", r"C:\Program Files (x86)\Steam\Steam.exe", r"C:\Program Files\Steam\Steam.exe"],
            "protocol": "steam://open/main",
            "web_url": "https://store.steampowered.com",
            "name": "Steam"
        },
        "lenovo vantage": {
            "exe": [],
            "protocol": "shell:AppsFolder\\E046963F.LenovoCompanion_k1h2ywk1493x8!App",
            "web_url": None,
            "name": "Lenovo Vantage"
        },
        "vantage": {
            "exe": [],
            "protocol": "shell:AppsFolder\\E046963F.LenovoCompanion_k1h2ywk1493x8!App",
            "web_url": None,
            "name": "Lenovo Vantage"
        }
    }

    _cached_start_apps: Optional[List[Dict[str, str]]] = None

    KNOWN_FOLDER_GUIDS: Dict[str, str] = {
        "{7C5A40EF-A0FB-4BFC-874A-C0F2E0B9FA8E}": os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        "{6D809377-6AF0-444B-8957-A3773F02200E}": os.environ.get("ProgramFiles", r"C:\Program Files"),
        "{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}": os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32"),
        "{D65231B0-B2F1-4857-A4CE-A8E7C6EA7D27}": os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "SysWOW64"),
        "{F38BF404-1D43-42F2-9305-67DE0B28FC23}": os.environ.get("SystemRoot", r"C:\Windows"),
        "{F1B32785-6FBA-4FCF-9D55-7B8E7F157091}": os.environ.get("LOCALAPPDATA", os.path.expanduser("~/AppData/Local")),
        "{3EB685FD-984F-4FFB-8620-1FBF315E1102}": os.environ.get("APPDATA", os.path.expanduser("~/AppData/Roaming")),
        "{0139D44E-6AFE-49F2-8690-3DAFCAE6FFB8}": os.path.join(os.environ.get("ProgramData", r"C:\ProgramData"), r"Microsoft\Windows\Start Menu\Programs"),
        "{A77F5D77-2E2B-44C3-A6A2-ABA601054A51}": os.path.join(os.environ.get("APPDATA", os.path.expanduser("~/AppData/Roaming")), r"Microsoft\Windows\Start Menu\Programs"),
    }

    @classmethod
    def resolve_app_path_from_guid(cls, app_id: str) -> Optional[str]:
        """Convertit un app_id Windows basé sur GUID en chemin absolu existant sur le disque."""
        if not app_id:
            return None
        for guid, base_path in cls.KNOWN_FOLDER_GUIDS.items():
            if app_id.startswith(guid):
                rel_path = app_id[len(guid):].lstrip("\\/")
                candidate = os.path.join(base_path, rel_path)
                if os.path.exists(candidate):
                    return candidate
        if os.path.exists(app_id):
            return app_id
        return None

    ALIASES: Dict[str, str] = {
        "gta": "grand theft auto",
        "gta 5": "grand theft auto",
        "gta v": "grand theft auto",
        "gta5": "grand theft auto",
        "rdr": "red dead redemption",
        "rdr2": "red dead redemption",
        "rdr 2": "red dead redemption",
        "calc": "calculatrice",
        "calculette": "calculatrice",
        "calcul": "calculatrice",
        "compte": "calculatrice",
        "notepad": "bloc-notes",
        "note": "bloc-notes",
        "notes": "bloc-notes",
        "carnet": "bloc-notes",
        "carnet de notes": "bloc-notes",
        # Fichiers & Explorateur
        "fichiers": "explorateur",
        "fichier": "explorateur",
        "mes fichiers": "explorateur",
        "les fichiers": "explorateur",
        "mes documents": "explorateur",
        "documents": "explorateur",
        "mon dossier": "explorateur",
        "mes dossiers": "explorateur",
        "telechargements": "explorateur",
        "mes telechargements": "explorateur",
        "corbeille": "explorateur",
        "explorateur de fichiers": "explorateur",
        "explorer": "explorateur",
        # Musique
        "musique": "spotify",
        "ma musique": "spotify",
        "chanson": "spotify",
        "chansons": "spotify",
        "playlist": "spotify",
        "son": "spotify",
        # Navigateur & Internet
        "navigateur": "chrome",
        "mon navigateur": "chrome",
        "internet": "chrome",
        "web": "chrome",
        "google": "chrome",
        # Paramètres
        "parametres": "parametres",
        "mes parametres": "parametres",
        "reglages": "parametres",
        "mes reglages": "parametres",
        "configuration": "parametres",
        # Photos
        "photos": "photos",
        "mes photos": "photos",
        "galerie": "photos",
        # Tâches
        "gestionnaire des taches": "gestionnaire des taches",
        "gestionnaire de taches": "gestionnaire des taches",
        "taches": "gestionnaire des taches",
        "taskmgr": "gestionnaire des taches",
        # Dessin
        "dessin": "paint",
        "dessiner": "paint",
    }

    @classmethod
    def get_installed_start_apps(cls) -> List[Dict[str, str]]:
        """Scanne dynamiquement toutes les applications enregistrées dans Windows (StartApps + Raccourcis Bureau)."""
        if cls._cached_start_apps is not None:
            return cls._cached_start_apps

        apps: List[Dict[str, str]] = []
        if sys.platform == "win32":
            # 1. Scanner Get-StartApps (Windows 11 Start Menu, UWP, MSIX, etc.)
            try:
                cmd = 'powershell -NoProfile -Command "Get-StartApps | ConvertTo-Json -Compress"'
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
                if res.stdout.strip():
                    raw = json.loads(res.stdout)
                    if isinstance(raw, list):
                        for item in raw:
                            if isinstance(item, dict) and "Name" in item and "AppID" in item:
                                apps.append({
                                    "name": item["Name"],
                                    "app_id": item["AppID"],
                                    "norm_name": normalize_text(item["Name"]),
                                    "type": "start_app"
                                })
            except Exception as e:
                logger.warning(f"Impossible de scanner Get-StartApps : {e}")

            # 2. Scanner les raccourcis du Bureau utilisateur et public (.lnk et .url pour les jeux et logiciels)
            desktop_folders = [os.path.expanduser('~/Desktop'), 'C:/Users/Public/Desktop']
            for folder in desktop_folders:
                if os.path.exists(folder):
                    try:
                        for f in os.listdir(folder):
                            if f.endswith('.lnk') or f.endswith('.url'):
                                clean_name = f.replace('.lnk', '').replace('.url', '')
                                apps.append({
                                    "name": clean_name,
                                    "app_id": os.path.join(folder, f),
                                    "norm_name": normalize_text(clean_name),
                                    "type": "shortcut"
                                })
                    except Exception as e:
                        logger.warning(f"Impossible de scanner le bureau {folder} : {e}")

        cls._cached_start_apps = apps
        return apps

    @classmethod
    def find_installed_app(cls, app_query: str) -> Optional[Dict[str, str]]:
        """Recherche une application parmi TOUTES les applications installées (fuzzy, aliases & exact)."""
        norm_query = normalize_text(app_query)
        if not norm_query:
            return None

        # Résolution alias
        resolved_query = cls.ALIASES.get(norm_query, norm_query)

        # 1. Scanner toutes les applications répertoriées
        apps = cls.get_installed_start_apps()

        # A. Correspondance exacte sur query ou alias
        for a in apps:
            if a["norm_name"] == norm_query or a["norm_name"] == resolved_query:
                return a

        # B. Mot complet ou préfixe
        for a in apps:
            words = a["norm_name"].split()
            if norm_query in words or resolved_query in words or a["norm_name"].startswith(norm_query) or a["norm_name"].startswith(resolved_query):
                return a

        # C. Contenance simple
        for a in apps:
            if norm_query in a["norm_name"] or resolved_query in a["norm_name"]:
                return a
            if a["norm_name"] in norm_query or a["norm_name"] in resolved_query:
                return a

        # D. Fuzzy matching (tolérance fautes de frappe avec seuil strict >= 0.75)
        names_dict = {a["norm_name"]: a for a in apps}
        matches = difflib.get_close_matches(norm_query, names_dict.keys(), n=1, cutoff=0.75)
        if matches:
            return names_dict[matches[0]]

        matches_alias = difflib.get_close_matches(resolved_query, names_dict.keys(), n=1, cutoff=0.75)
        if matches_alias:
            return names_dict[matches_alias[0]]

        return None

    @classmethod
    def resolve_app_command(cls, app_name: str) -> Optional[str]:
        """Résout la commande ou l'URL associée à un nom d'application."""
        key = normalize_text(app_name)
        for k, info in cls.APP_REGISTRY.items():
            if k in key or key in k:
                for exe in info.get("exe", []):
                    found = shutil.which(exe)
                    if found:
                        return found
                if info.get("protocol"):
                    return info["protocol"]
                if info.get("web_url"):
                    return info["web_url"]

        # Chercher dans StartApps
        installed = cls.find_installed_app(app_name)
        if installed:
            return f"shell:AppsFolder\\{installed['app_id']}"

        return None

    @classmethod
    def launch_application(
        cls,
        app_name: str,
        target_screen: str = "principal",
        simulate: bool = False
    ) -> Dict[str, Any]:
        """
        Lance N'IMPORTE QUELLE application installée sur le PC Windows ou l'ouvre sur un écran cible.
        """
        key = normalize_text(app_name)
        matched_info = None
        for k, info in cls.APP_REGISTRY.items():
            if k == key or k in key.split() or key in k.split():
                matched_info = info
                break

        installed = cls.find_installed_app(app_name)
        # Préférer le registre officiel si disponible
        if matched_info:
            app_display_name = matched_info["name"]
        elif installed:
            app_display_name = installed["name"]
        else:
            app_display_name = app_name.title()

        web_url = matched_info.get("web_url") if matched_info else None
        protocol = matched_info.get("protocol") if matched_info else None
        exe_list = matched_info.get("exe", []) if matched_info else [f"{app_name}.exe"]

        # Cas spécial natif Windows : Explorateur de fichiers
        is_explorer = key in [
            "fichiers", "fichier", "mes fichiers", "mon fichier", "les fichiers",
            "explorateur", "explorateur de fichiers", "explorer", "dossier", "dossiers",
            "mes dossiers", "mon dossier", "documents", "mes documents",
            "telechargements", "mes telechargements"
        ] or "fichier" in key or "explorateur" in key

        launched = False
        method = "none"

        if is_explorer:
            app_display_name = "Explorateur de fichiers"
            if not simulate and sys.platform == "win32":
                try:
                    subprocess.Popen(["explorer.exe"])
                    launched = True
                    method = "windows_explorer"
                except Exception as e:
                    logger.warning(f"Échec ouverture explorateur : {e}")

        if not simulate and sys.platform == "win32" and not launched:
            # 1. Si chemin direct résolu depuis GUID StartApps (ex: Steam.exe)
            if installed and installed.get("app_id"):
                resolved_exe = cls.resolve_app_path_from_guid(installed["app_id"])
                if resolved_exe and os.path.exists(resolved_exe):
                    try:
                        os.startfile(resolved_exe)
                        launched = True
                        method = f"resolved_guid_exe ({resolved_exe})"
                    except Exception as e:
                        logger.warning(f"Échec startfile resolved_exe : {e}")

            # 2. Tenter via raccourci Bureau (.lnk ou .url pour les jeux et launchers)
            if not launched and installed and (installed.get("type") == "shortcut" or installed.get("app_id", "").endswith((".lnk", ".url"))):
                try:
                    os.startfile(installed["app_id"])
                    launched = True
                    method = f"desktop_shortcut ({installed['name']})"
                except Exception as e:
                    logger.warning(f"Échec lancement raccourci pour {installed['name']} : {e}")

            # 3. Tenter os.startfile sur shell:AppsFolder (pour TOUTES les applications UWP comme Lenovo Vantage, Calculatrice)
            if not launched and installed and installed.get("app_id"):
                try:
                    os.startfile(f"shell:AppsFolder\\{installed['app_id']}")
                    launched = True
                    method = f"windows_start_apps_startfile ({installed['name']})"
                except Exception as e:
                    logger.debug(f"Échec startfile shell:AppsFolder pour {installed['name']} : {e}")

            # 4. Tenter le protocole Windows (os.startfile : steam://, discord://, spotify://, ms-settings:, etc.)
            if not launched and protocol:
                try:
                    os.startfile(protocol)
                    launched = True
                    method = f"os_protocol ({protocol})"
                except Exception as e:
                    logger.debug(f"Protocole non géré {protocol}: {e}")

            # 5. Tenter l'exécutable local sur PATH ou chemin absolu
            if not launched:
                for exe in exe_list:
                    if os.path.isabs(exe) and os.path.exists(exe):
                        try:
                            os.startfile(exe)
                            launched = True
                            method = f"local_abs_exe ({exe})"
                            break
                        except Exception as e:
                            logger.warning(f"Échec abs exe {exe} : {e}")
                    found = shutil.which(exe)
                    if found:
                        try:
                            subprocess.Popen([found], shell=False)
                            launched = True
                            method = f"local_process ({found})"
                            break
                        except Exception as e:
                            logger.warning(f"Échec Popen pour {found}: {e}")

            # 6. Fallback Web Browser si disponible
            if not launched and web_url:
                try:
                    webbrowser.open(web_url)
                    launched = True
                    method = f"web_browser ({web_url})"
                except Exception as e:
                    logger.warning(f"Échec ouverture web {web_url}: {e}")

        screen_desc = {
            "haut": "l'écran du haut",
            "droite": "l'écran de droite",
            "gauche": "l'écran de gauche",
            "secondaire": "l'écran secondaire",
            "principal": "l'écran principal"
        }.get(target_screen.lower().strip(), f"l'écran {target_screen}")

        if launched or simulate:
            status = "launched"
            verbal_reply = f"{app_display_name} est lancé sur {screen_desc}, monsieur."
        else:
            status = "not_found"
            verbal_reply = f"Je n'ai pas pu lancer {app_display_name}. Vérifie qu'il est bien installé sur ton PC."

        return {
            "action": "launch",
            "status": status,
            "app": app_name,
            "display_name": app_display_name,
            "screen": target_screen,
            "screen_description": screen_desc,
            "verbal_reply": verbal_reply,
            "url": web_url or "",
            "is_web": bool(web_url and not launched),
            "method": method
        }

    @classmethod
    def close_application(cls, app_name: str, simulate: bool = False) -> Dict[str, Any]:
        """
        Ferme immédiatement N'IMPORTE QUELLE application ou processus en cours d'exécution.
        """
        norm_query = normalize_text(app_name)

        # Cas spécial natif Windows : Explorateur de fichiers
        # Ne JAMAIS tuer explorer.exe par taskkill car cela tuerait le bureau et la barre des tâches de Windows.
        # Fermeture propre des fenêtres de dossiers ouvertes via COM Shell.Application.
        is_explorer = norm_query in [
            "fichiers", "fichier", "mes fichiers", "mon fichier", "les fichiers",
            "explorateur", "explorateur de fichiers", "explorer", "dossier", "dossiers",
            "mes dossiers", "mon dossier", "documents", "mes documents",
            "telechargements", "mes telechargements", "corbeille"
        ] or "fichier" in norm_query or "explorateur" in norm_query

        if is_explorer:
            closed_count = 0
            if not simulate and sys.platform == "win32":
                try:
                    import base64
                    ps_code = """
                    $shell = New-Object -ComObject Shell.Application
                    $before = $shell.Windows().Count
                    foreach ($w in $shell.Windows()) {
                        try { $w.Quit() } catch {}
                    }
                    Start-Sleep -Milliseconds 400
                    $after = $shell.Windows().Count
                    $closed = [Math]::Max(0, $before - $after)
                    Write-Output $closed
                    """
                    encoded = base64.b64encode(ps_code.encode('utf-16le')).decode('ascii')
                    cmd = ["powershell", "-NoProfile", "-EncodedCommand", encoded]
                    res = subprocess.run(cmd, capture_output=True, text=True)
                    out_clean = res.stdout.strip().split()[-1] if res.stdout.strip() else "0"
                    closed_count = int(out_clean)
                except Exception as e:
                    logger.warning(f"Erreur fermeture propre explorateur : {e}")

            if closed_count > 0 or simulate:
                status = "closed"
                killed_list = ["Explorateur de fichiers (fenêtres fermées)"]
                verbal_reply = "L'explorateur de fichiers a été fermé, monsieur."
            else:
                status = "not_running"
                killed_list = []
                verbal_reply = "Aucune fenêtre de l'explorateur de fichiers n'était ouverte, monsieur."

            return {
                "action": "close",
                "status": status,
                "app": app_name,
                "display_name": "Explorateur de fichiers",
                "killed_processes": killed_list,
                "verbal_reply": verbal_reply
            }

        procs_to_kill: List[str] = []

        # 1. Vérifier nos mappings connus
        for alias, procs in cls.KNOWN_PROCESS_MAPPINGS.items():
            if norm_query == normalize_text(alias) or norm_query in normalize_text(alias):
                procs_to_kill.extend(procs)

        # 2. Chercher dans StartApps pour trouver le nom du .exe ou de l'application
        installed = cls.find_installed_app(app_name)
        if installed:
            app_id = installed.get("app_id", "")
            if ".exe" in app_id.lower():
                exe_name = os.path.basename(app_id).replace(".exe", "")
                if exe_name not in procs_to_kill:
                    procs_to_kill.append(exe_name)
            name_base = installed["name"].split()[0]
            if name_base not in procs_to_kill:
                procs_to_kill.append(name_base)

        # 3. Ajouter le nom direct passé par l'utilisateur
        clean_direct = app_name.strip().replace(".exe", "")
        if clean_direct not in procs_to_kill:
            procs_to_kill.append(clean_direct)

        # 4. Scanner dynamiquement les processus actifs sur Windows via tasklist
        q_clean = norm_query.replace(" ", "")
        q_words = [w for w in norm_query.split() if len(w) > 2]
        if not simulate and sys.platform == "win32":
            try:
                res_tl = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True)
                if res_tl.returncode == 0:
                    import csv, io
                    reader = csv.reader(io.StringIO(res_tl.stdout))
                    resolved_q = cls.ALIASES.get(norm_query, norm_query)
                    resolved_clean = resolved_q.replace(" ", "")
                    for row in reader:
                        if row:
                            p_name = row[0].replace(".exe", "").replace(".EXE", "")
                            norm_p = normalize_text(p_name)
                            p_clean = norm_p.replace(" ", "")
                            # Match direct, sans espace ou tous les mots de la requête
                            if (q_clean and (q_clean in p_clean or p_clean in q_clean)) or \
                               (resolved_clean and (resolved_clean in p_clean or p_clean in resolved_clean)) or \
                               (q_words and all(w in p_clean for w in q_words)):
                                if p_name not in procs_to_kill:
                                    procs_to_kill.append(p_name)
            except Exception as e:
                logger.debug(f"Erreur scan dynamique tasklist: {e}")

        matched_info_close = None
        for k, info in cls.APP_REGISTRY.items():
            if k == norm_query or k in norm_query.split() or norm_query in k.split():
                matched_info_close = info
                break

        if matched_info_close:
            app_display_name = matched_info_close["name"]
        elif installed:
            app_display_name = installed["name"]
        else:
            app_display_name = app_name.title()
        killed_list = []

        if not simulate and sys.platform == "win32":
            # Trier pour tuer les exécutables principaux d'abord
            sorted_procs = sorted(
                list(set(procs_to_kill)),
                key=lambda x: (1 if "-" in x or "(" in x else 0, len(x))
            )
            for p in sorted_procs:
                if p.lower() in ["explorer", "explorer.exe"]:
                    continue
                try:
                    # Tenter taskkill avec arborescence (/T)
                    res = subprocess.run(
                        ["taskkill", "/IM", f"{p}.exe", "/F", "/T"],
                        capture_output=True,
                        text=True
                    )
                    if res.returncode == 0:
                        killed_list.append(p)
                        continue

                    # Tenter Stop-Process PowerShell avec wildcard
                    ps_cmd = f"Stop-Process -Name '{p}' -Force -ErrorAction SilentlyContinue"
                    ps_res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
                    if ps_res.returncode == 0:
                        killed_list.append(p)
                except Exception as e:
                    logger.warning(f"Erreur lors de la fermeture du processus {p} : {e}")

            # Si aucun processus spécifique n'a répondu mais qu'on a un nom propre, tenter wildcard PowerShell
            if not killed_list and q_clean:
                try:
                    ps_wildcard = f"Get-Process | Where-Object {{ $_.ProcessName -like '*{q_clean}*' }} | Stop-Process -Force -ErrorAction SilentlyContinue"
                    ps_res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_wildcard], capture_output=True, text=True)
                    if ps_res.returncode == 0:
                        killed_list.append(app_name)
                except Exception as e:
                    logger.debug(f"Wildcard kill error: {e}")

        status = "closed" if (killed_list or simulate) else "not_running"
        verbal_reply = f"{app_display_name} a été fermé, monsieur." if (killed_list or simulate) else f"{app_display_name} n'était pas en cours d'exécution."

        return {
            "action": "close",
            "status": status,
            "app": app_name,
            "display_name": app_display_name,
            "killed_processes": killed_list,
            "verbal_reply": verbal_reply
        }
