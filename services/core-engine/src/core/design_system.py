"""
Système de Design & Règles d'Expérience Utilisateur pour HoL AI.
Synthèse active des 5 skills :
- pbakaus/impeccable (Craft floor, hiérarchie, suppression des clichés IA)
- Leonxlnx/taste-skill (Direction artistique anti-slop, palettes soignées, typographie)
- better-auth/better-icons (Iconographie vectorielle haute fidélité)
- superdesigndev/superdesign (Architecture de composants spatiaux & thèmes)
- jakubkrehel/make-interfaces-feel-better (Physique des ressorts, haptique sonore, nesting des rayons)
"""

DESIGN_SYSTEM = {
    "name": "HoL Design Engineering Tokens",
    "typography": {
        "primary_font": "Plus Jakarta Sans, sans-serif",
        "code_font": "JetBrains Mono, monospace",
        "hierarchy": {
            "display": {"size": "28px", "weight": 800, "letter_spacing": "-0.03em"},
            "title": {"size": "14px", "weight": 700, "letter_spacing": "-0.01em"},
            "body": {"size": "13px", "weight": 400, "line_height": "1.5"},
            "mono_stat": {"size": "18px", "weight": 700, "font": "mono"}
        }
    },
    "surface_depth": {
        "elevation_1": "0 0 0 1px rgba(255, 255, 255, 0.07), 0 8px 24px -4px rgba(0, 0, 0, 0.6)",
        "elevation_2": "0 0 0 1px rgba(255, 255, 255, 0.12), 0 20px 48px -12px rgba(0, 0, 0, 0.8)",
        "elevation_hover": "0 0 0 1px rgba(99, 102, 241, 0.4), 0 25px 60px -10px rgba(0, 0, 0, 0.9)"
    },
    "geometry": {
        "rule_radius_nesting": "R_inner = max(0, R_outer - padding)",
        "outer_card_radius": "16px",
        "inner_container_radius": "12px",
        "tag_badge_radius": "6px"
    },
    "motion": {
        "spring_physics": "cubic-bezier(0.16, 1, 0.3, 1)",
        "quick_spring": "cubic-bezier(0.2, 0, 0, 1)",
        "durations": {
            "fast": "150ms",
            "medium": "280ms",
            "slow": "450ms"
        }
    },
    "audio_haptics": {
        "enabled": True,
        "tones": {
            "click": {"freq": 820, "type": "sine", "duration_ms": 25},
            "pop": {"freq": 440, "type": "triangle", "duration_ms": 40},
            "success": {"freq": 980, "type": "sine", "duration_ms": 90}
        }
    }
}
