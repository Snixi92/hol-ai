"""
Service de résolution d'icônes haute définition pour HoL AI (Inspiré de better-icons).
Permet aux agents d'interroger et d'extraire plus de 200 000 icônes vectorielles SVG (Lucide, Radix, Tabler, Carbon).
"""
import urllib.request
import urllib.parse
from typing import Optional, Dict
from functools import lru_cache


ICON_COLLECTION_ALIASES = {
    "package": "lucide:package-check",
    "delivery": "lucide:truck",
    "finance": "lucide:circle-dollar-sign",
    "profit": "lucide:trending-up",
    "script": "lucide:clapperboard",
    "telegram": "logos:telegram",
    "execution": "lucide:zap",
    "memory": "lucide:brain",
    "canvas": "lucide:layout-grid",
    "mic": "lucide:mic",
    "search": "lucide:search",
    "settings": "lucide:sliders-horizontal",
    "audio": "lucide:volume-2"
}


class IconService:
    BASE_URL = "https://api.iconify.design"

    @classmethod
    @lru_cache(maxsize=256)
    def get_svg_icon(cls, icon_identifier: str, size: int = 20, color: str = "currentColor") -> str:
        """
        Récupère le code SVG d'une icône via son identifiant Iconify (ex: 'lucide:package-check').
        Retourne un SVG propre prêt à être injecté dans le DOM du Canvas.
        """
        if icon_identifier in ICON_COLLECTION_ALIASES:
            icon_identifier = ICON_COLLECTION_ALIASES[icon_identifier]

        if ":" not in icon_identifier:
            icon_identifier = f"lucide:{icon_identifier}"

        prefix, name = icon_identifier.split(":", 1)
        url = f"{cls.BASE_URL}/{prefix}/{name}.svg?color={urllib.parse.quote(color)}&width={size}&height={size}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HoL-AI-BetterIcons/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    return resp.read().decode("utf-8")
        except Exception:
            pass

        # Fallback SVG minimaliste si hors ligne
        return (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            f'<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line>'
            f'<line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'
        )
