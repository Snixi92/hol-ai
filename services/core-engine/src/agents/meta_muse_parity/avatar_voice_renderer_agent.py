"""
AvatarVoiceRendererAgent : Agent de rendu et synchronisation labiale de l'Avatar 3D pour HoL AI.
Inspiré du Realtime Avatar de Meta Muse :
- Modélisation des états faciaux et micro-expressions (idle, speaking, thinking, happy, alert).
- Génération des cibles morphologiques (morph targets / visèmes) pour synchronisation labiale temps réel.
- Pilotage du composant visuel WebGL / Canvas dans le dashboard HUD.
"""
import time
from typing import Dict, Any, List, Optional


class AvatarVoiceRendererAgent:
    """Agent responsable de l'incarnation visuelle et de l'animation de l'Avatar 3D."""

    MOOD_CONFIGS = {
        "idle": {"head_tilt": 0.02, "eye_blink_interval_sec": 3.5, "glow_color": "#00f0ff", "expression": "calm"},
        "speaking": {"head_tilt": 0.05, "eye_blink_interval_sec": 2.8, "glow_color": "#10b981", "expression": "expressive"},
        "thinking": {"head_tilt": -0.08, "eye_blink_interval_sec": 4.0, "glow_color": "#a855f7", "expression": "pensive"},
        "happy": {"head_tilt": 0.06, "eye_blink_interval_sec": 2.5, "glow_color": "#f59e0b", "expression": "smiling"},
        "alert": {"head_tilt": 0.0, "eye_blink_interval_sec": 5.0, "glow_color": "#ef4444", "expression": "vigilant"},
        "cyberpunk_focus": {"head_tilt": 0.03, "eye_blink_interval_sec": 3.0, "glow_color": "#06b6d4", "expression": "focused"}
    }

    @classmethod
    def generate_avatar_state(cls, mood: str = "idle", speech_text: str = "") -> Dict[str, Any]:
        """
        Calcule l'état de l'avatar et les séries de visèmes pour l'animation WebGL.
        """
        t0 = time.time()
        active_mood = mood.lower() if mood.lower() in cls.MOOD_CONFIGS else "speaking" if speech_text else "idle"
        cfg = cls.MOOD_CONFIGS[active_mood]

        visemes = []
        if speech_text:
            text_cleaned = speech_text.lower()
            words = text_cleaned.split()
            current_time_ms = 0

            for word in words[:25]:
                for char in word:
                    viseme_type = "rest"
                    duration = 80
                    if char in "aeio":
                        viseme_type = "jaw_open"
                        duration = 110
                    elif char in "uou":
                        viseme_type = "mouth_round"
                        duration = 100
                    elif char in "mbp":
                        viseme_type = "lips_closed"
                        duration = 70
                    elif char in "fv":
                        viseme_type = "lip_tuck"
                        duration = 80
                    elif char in "stdn":
                        viseme_type = "tongue_up"
                        duration = 75

                    visemes.append({
                        "viseme": viseme_type,
                        "intensity": 0.85 if viseme_type != "rest" else 0.1,
                        "time_offset_ms": current_time_ms,
                        "duration_ms": duration
                    })
                    current_time_ms += duration
                current_time_ms += 120

        duration_ms = round((time.time() - t0) * 1000, 1)

        return {
            "status": "ready",
            "mood": active_mood,
            "expression": cfg["expression"],
            "glow_color": cfg["glow_color"],
            "visemes_count": len(visemes),
            "visemes": visemes[:60],
            "estimated_speech_duration_ms": len(visemes) * 90 if visemes else 0,
            "duration_ms": duration_ms,
            "verbal_reply": f"Avatar 3D configuré en mode '{active_mood}' avec {len(visemes)} visèmes d'animation générés."
        }
