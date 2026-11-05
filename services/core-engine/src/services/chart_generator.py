"""
Générateur de graphiques dynamiques et infographies néon HUD pour Jarvis.
Permet d'afficher immédiatement à l'écran des graphiques interactifs (barres, courbes, tendances)
sur l'adoption de l'IA, les métriques financières ou les statistiques de marché.
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("hol_ai.chart_generator")


class ChartGeneratorService:
    """Service de génération de visualisations de données pour le Cockpit Jarvis."""

    @classmethod
    def create_chart(
        cls,
        title: str,
        chart_type: str = "bar",
        labels: Optional[List[str]] = None,
        values: Optional[List[float]] = None,
        unit: str = "%"
    ) -> Dict[str, Any]:
        """
        Génère les données structurées et le SVG optimisé pour affichage direct dans l'interface HUD.
        """
        labels = labels or []
        values = values or []

        # Si les listes sont vides, fournir un point par défaut
        if not labels or not values:
            return {
                "status": "fallback",
                "title": title or "Graphique sans données",
                "chart_type": chart_type or "bar",
                "unit": unit,
                "data_points": [{"label": "N/A", "value": 0.0, "percentage": 0.0}],
                "max_value": 0.0,
                "min_value": 0.0,
                "verbal_reply": f"Aucune donnée chiffrée disponible pour {title}."
            }

        # Nettoyage et alignement de taille
        count = min(len(labels), len(values))
        clean_labels = [str(labels[i]) for i in range(count)]
        clean_values = [float(values[i]) for i in range(count)]

        max_val = max(clean_values) if clean_values else 1.0
        if max_val == 0:
            max_val = 1.0

        min_val = min(clean_values) if clean_values else 0.0

        data_points = []
        for l, v in zip(clean_labels, clean_values):
            pct = round((v / max_val) * 100, 1) if max_val > 0 else 0.0
            data_points.append({
                "label": l,
                "value": v,
                "percentage": pct
            })

        # Génération d'un SVG léger cyberpunk autonome
        svg_bars = []
        bar_width = 40
        gap = 25
        chart_height = 140
        total_width = max(len(data_points) * (bar_width + gap) + 40, 320)

        for idx, pt in enumerate(data_points):
            x = 30 + idx * (bar_width + gap)
            h = max(int((pt["value"] / max_val) * (chart_height - 30)), 4) if max_val > 0 else 4
            y = chart_height - h
            val_str = f"{pt['value']}{unit}"
            svg_bars.append(
                f'<g class="bar-group">'
                f'<rect x="{x}" y="{y}" width="{bar_width}" height="{h}" rx="4" fill="url(#neonCyanGrad)" filter="url(#glow)"/>'
                f'<text x="{x + bar_width//2}" y="{y - 6}" fill="#00f3ff" font-size="11" font-weight="bold" text-anchor="middle">{val_str}</text>'
                f'<text x="{x + bar_width//2}" y="{chart_height + 18}" fill="#94a3b8" font-size="11" text-anchor="middle">{pt["label"]}</text>'
                f'</g>'
            )

        svg_markup = (
            f'<svg viewBox="0 0 {total_width} {chart_height + 35}" xmlns="http://www.w3.org/2000/svg" class="hud-svg-chart">'
            f'<defs>'
            f'<linearGradient id="neonCyanGrad" x1="0%" y1="0%" x2="0%" y2="100%">'
            f'<stop offset="0%" stop-color="#00f3ff" stop-opacity="0.95"/>'
            f'<stop offset="100%" stop-color="#0284c7" stop-opacity="0.5"/>'
            f'</linearGradient>'
            f'<filter id="glow" x="-20%" y="-20%" width="140%" height="140%">'
            f'<feGaussianBlur stdDeviation="3" result="blur" />'
            f'<feMerge>'
            f'<feMergeNode in="blur" />'
            f'<feMergeNode in="SourceGraphic" />'
            f'</feMerge>'
            f'</filter>'
            f'</defs>'
            f'{"".join(svg_bars)}'
            f'</svg>'
        )

        verbal_reply = f"Voici les graphiques d'évolution pour {title}, monsieur."

        return {
            "status": "ok",
            "title": title,
            "chart_type": chart_type,
            "unit": unit,
            "data_points": data_points,
            "max_value": max_val,
            "min_value": min_val,
            "visual_svg": svg_markup,
            "verbal_reply": verbal_reply
        }
