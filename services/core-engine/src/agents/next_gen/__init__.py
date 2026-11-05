"""
Module des 5 Agents Next-Gen de HoL AI :
1. BiographicalMemoryAgent : Mémoire Biographique Persistante Long-Terme
2. LiveVoiceAgent : Mode Vocal Mains-Libres & Synthèse/Transcription
3. ProactiveNotifierAgent : Notifications Proactives Windows & Mobiles
4. DesktopAutomationAgent : Contrôle Graphique et Automatisation du Bureau Windows
5. MobilePWAVisionAgent : PWA Mobile Dédiée & Vision Caméra Multimodale
"""

from .biographical_memory_agent import BiographicalMemoryAgent
from .live_voice_agent import LiveVoiceAgent
from .proactive_notifier_agent import ProactiveNotifierAgent
from .desktop_automation_agent import DesktopAutomationAgent
from .mobile_pwa_vision_agent import MobilePWAVisionAgent

__all__ = [
    "BiographicalMemoryAgent",
    "LiveVoiceAgent",
    "ProactiveNotifierAgent",
    "DesktopAutomationAgent",
    "MobilePWAVisionAgent"
]
