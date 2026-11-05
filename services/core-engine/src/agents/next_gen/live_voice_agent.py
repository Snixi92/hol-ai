"""
LiveVoiceAgent : Agent Vocal Temps Réel Mains-Libres pour HoL AI.
Gère la synthèse vocale (TTS) avec voix française native (Hortense Desktop),
la transcription audio (STT) multimodale, et la gestion du mode mains-libres.
"""
import os
import base64
import tempfile
import subprocess
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("hol_ai.live_voice")


class LiveVoiceAgent:
    """Agent expert de la voix, de l'audio et des interactions vocales mains-libres."""

    DEFAULT_VOICE = "Microsoft Hortense Desktop"
    FALLBACK_VOICE = "Microsoft David Desktop"
    _hands_free_active: bool = False

    @classmethod
    def synthesize_speech(
        cls,
        text: str,
        voice_name: Optional[str] = None,
        direct_speak: bool = False,
        output_format: str = "wav"
    ) -> Dict[str, Any]:
        """
        Synthétise du texte en parole audio (WAV encodé en base64) et/ou prononce directement via haut-parleurs.
        
        Args:
            text: Le texte à prononcer
            voice_name: Nom de la voix SAPI (défaut Hortense française)
            direct_speak: Si True, prononce immédiatement sur la machine hôte
            output_format: "wav"
        """
        chosen_voice = voice_name or cls.DEFAULT_VOICE
        clean_text = text.replace('"', '""').replace("'", "''").strip()
        if not clean_text:
            return {"success": False, "error": "Texte vide"}

        temp_dir = tempfile.gettempdir()
        wav_file = os.path.join(temp_dir, f"hol_voice_{os.getpid()}_{hash(text) & 0xFFFFFFFF}.wav").replace("\\", "/")
        ps_file = os.path.join(temp_dir, f"hol_synth_{os.getpid()}_{hash(text) & 0xFFFFFFFF}.ps1")

        # Construction du script PowerShell propre et auto-contenu
        direct_cmd = f"$synth.Speak('{clean_text}')" if direct_speak else ""
        file_cmd = f"""
$synth.SetOutputToWaveFile('{wav_file}')
$synth.Speak('{clean_text}')
$synth.SetOutputToNull()
"""

        ps_script = f"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {{
    $synth.SelectVoice('{chosen_voice}')
}} catch {{
    try {{
        $synth.SelectVoice('{cls.FALLBACK_VOICE}')
    }} catch {{}}
}}
{file_cmd}
{direct_cmd}
$synth.Dispose()
"""
        try:
            with open(ps_file, "w", encoding="utf-8") as f:
                f.write(ps_script)

            res = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_file],
                capture_output=True,
                text=True,
                timeout=20
            )

            b64_audio = ""
            file_size = 0
            if os.path.exists(wav_file):
                file_size = os.path.getsize(wav_file)
                with open(wav_file, "rb") as wf:
                    b64_audio = base64.b64encode(wf.read()).decode("ascii")

            return {
                "success": bool(b64_audio or direct_speak),
                "audio_base64": b64_audio,
                "mime_type": "audio/wav",
                "voice_used": chosen_voice,
                "size_bytes": file_size,
                "direct_spoken": direct_speak,
                "text_spoken": text,
                "stderr": res.stderr if res.returncode != 0 else ""
            }
        except Exception as e:
            logger.error(f"Erreur synthèse vocale: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if os.path.exists(ps_file):
                try:
                    os.remove(ps_file)
                except Exception:
                    pass
            if os.path.exists(wav_file):
                try:
                    os.remove(wav_file)
                except Exception:
                    pass

    @classmethod
    def transcribe_audio(
        cls,
        audio_data: bytes,
        mime_type: str = "audio/wav",
        language_hint: str = "fr"
    ) -> Dict[str, Any]:
        """
        Transcrit un flux audio (parole de l'utilisateur) en texte via Google GenAI multimodal.
        """
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return {"success": False, "error": "GEMINI_API_KEY non configurée pour STT"}

            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            prompt = (
                f"Transcris exactement et fidèlement les paroles entendues dans cet enregistrement audio. "
                f"Si l'audio est en français ou en darija/arabe/anglais, respecte la langue parlée. "
                f"Ne rajoute aucun commentaire méta, seulement le texte prononcé mot pour mot."
            )

            audio_part = types.Part.from_bytes(data=audio_data, mime_type=mime_type)
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=[prompt, audio_part]
            )

            transcript = response.text.strip() if response.text else ""
            return {
                "success": True,
                "text": transcript,
                "language_hint": language_hint,
                "model_used": "gemini-3.5-flash"
            }
        except Exception as e:
            logger.error(f"Erreur transcription audio: {e}")
            return {"success": False, "error": str(e), "text": ""}

    @classmethod
    def get_voice_capabilities(cls) -> Dict[str, Any]:
        """Retourne les capacités vocales et l'état du mode mains-libres."""
        return {
            "tts_available": True,
            "stt_available": True,
            "default_voice": cls.DEFAULT_VOICE,
            "installed_voices": ["Microsoft Hortense Desktop (Français)", "Microsoft Zira Desktop (English)", "Microsoft David Desktop (English)"],
            "hands_free_hotkey": "Alt+Space",
            "hands_free_active": cls._hands_free_active,
            "supported_audio_formats": ["audio/wav", "audio/webm", "audio/mp3", "audio/ogg"]
        }

    @classmethod
    def set_hands_free_state(cls, active: bool) -> Dict[str, Any]:
        """Active ou désactive le mode mains-libres."""
        cls._hands_free_active = active
        return {
            "success": True,
            "hands_free_active": cls._hands_free_active,
            "hotkey": "Alt+Space",
            "message": f"Mode mains-libres {'activé' if active else 'désactivé'}."
        }
