"""
MobilePWAVisionAgent : Agent PWA Mobile & Vision Caméra Dédiée pour HoL AI.
Fournit le manifest PWA, le Service Worker offline, et l'analyse multimodale en direct
des flux caméra pour la nutrition/repas, tickets de caisse, produits et documents.
"""
import os
import json
import base64
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("hol_ai.mobile_pwa_vision")


class MobilePWAVisionAgent:
    """Agent expert de l'expérience mobile progressive (PWA) et de la vision par caméra."""

    @classmethod
    def get_pwa_manifest(cls) -> Dict[str, Any]:
        """Génère le manifest standard de la PWA mobile HoL AI."""
        return {
            "name": "HoL AI - Assistant Autonome Ultime",
            "short_name": "HoL AI",
            "description": "Assistant IA multimodal tout-en-un avec mémoire persistante, vision caméra et vocal.",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#090d16",
            "theme_color": "#4f46e5",
            "orientation": "portrait-primary",
            "categories": ["productivity", "utilities"],
            "icons": [
                {
                    "src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' stop-color='%236366f1'/%3E%3Cstop offset='100%25' stop-color='%23a855f7'/%3E%3C/linearGradient%3E%3C/defs%3E%3Ccircle cx='256' cy='256' r='240' fill='url(%23g)'/%3E%3Cpath d='M160 160h60v192h-60zm132 0h60v192h-60zm-132 80h192v36H160z' fill='%23ffffff'/%3E%3C/svg%3E",
                    "sizes": "192x192 512x512",
                    "type": "image/svg+xml",
                    "purpose": "any maskable"
                }
            ],
            "shortcuts": [
                {
                    "name": "Scanner Repas / Facture",
                    "url": "/?action=camera",
                    "description": "Ouvre la caméra directe pour scanner un repas ou un reçu"
                },
                {
                    "name": "Mode Vocal Mains-Libres",
                    "url": "/?action=voice",
                    "description": "Démarrer l'échange vocal en temps réel"
                }
            ]
        }

    @classmethod
    def get_service_worker_code(cls) -> str:
        """Fournit le code source JavaScript du Service Worker pour le caching hors-ligne PWA."""
        return """// HoL AI Service Worker v1.2
const CACHE_NAME = 'hol-ai-pwa-cache-v1';
const STATIC_ASSETS = [
  '/',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  // Pour les appels API, toujours réseau en priorité
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(JSON.stringify({ error: "Hors ligne", offline: true }), {
          headers: { 'Content-Type': 'application/json' }
        });
      })
    );
    return;
  }

  // Pour les assets statiques, cache puis réseau
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      return cachedResponse || fetch(event.request).then((networkResponse) => {
        return caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, networkResponse.clone());
          return networkResponse;
        });
      });
    }).catch(() => caches.match('/'))
  );
});
"""

    @classmethod
    def analyze_camera_capture(
        cls,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        scan_mode: str = "general",
        custom_question: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyse une photo prise par l'appareil photo mobile (smartphone) ou la webcam.
        
        Args:
            image_bytes: Données brutes de l'image
            mime_type: Type MIME (image/jpeg, image/png, image/webp)
            scan_mode: "nutrition" | "receipt" | "product" | "document" | "general"
            custom_question: Question personnalisée posée par l'utilisateur
        """
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return {"success": False, "error": "GEMINI_API_KEY manquante pour l'analyse visuelle"}

            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            mode_prompts = {
                "nutrition": (
                    "Tu es un nutritionniste d'élite et chef expert. Analyse ce repas ou aliment photographié avec précision :\n"
                    "1. Identification de chaque aliment présent sur la photo.\n"
                    "2. Estimation calorique globale (kcal) et répartition des macronutriments (Protéines en g, Glucides en g, Lipides en g).\n"
                    "3. Indice de santé et Nutri-Score estimé.\n"
                    "4. Conseils concrets et bienveillants (Big Sis Energy).\n"
                    "Réponds en français avec une mise en page claire et structurée."
                ),
                "receipt": (
                    "Tu es un expert comptable et gestionnaire de budget. Analyse ce ticket de caisse ou facture :\n"
                    "1. Enseigne ou magasin marchand.\n"
                    "2. Date et heure d'achat.\n"
                    "3. Montant total TTC (€).\n"
                    "4. Liste exhaustive des articles et prix individuels.\n"
                    "5. Taux de TVA et observations (promotions appliquées, etc.).\n"
                    "Réponds en français sous forme de tableau ou récapitulatif clair."
                ),
                "product": (
                    "Tu es un dénicheur de bons plans et expert hardware/tech/commerce. Analyse ce produit photographié :\n"
                    "1. Nom exact, marque et modèle.\n"
                    "2. Caractéristiques techniques visibles ou identifiées.\n"
                    "3. Fourchette de prix moyen estimé sur le marché.\n"
                    "4. Avis objectif : points forts, points faibles et alternatives intéressantes.\n"
                    "Réponds en français de façon chaleureuse et ultra-pertinente."
                ),
                "document": (
                    "Tu es un assistant de lecture OCR haute fidélité. Analyse ce document administratif, courrier ou papier :\n"
                    "1. Type de document et émetteur.\n"
                    "2. Date et références clés (numéro client, identifiant).\n"
                    "3. Résumé fidèle et clair des informations principales ou actions requises.\n"
                    "Réponds en français de manière concise et structurée."
                ),
                "general": (
                    "Analyse cette photo prise par l'utilisateur. Décris avec clarté et précision ce qui y figure, "
                    "et réponds de façon chaleureuse et proactive (Big Sis Energy) en apportant un maximum de valeur ajoutée."
                )
            }

            base_prompt = mode_prompts.get(scan_mode, mode_prompts["general"])
            if custom_question:
                prompt = f"{base_prompt}\n\nQuestion spécifique de l'utilisateur : {custom_question}"
            else:
                prompt = base_prompt

            image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=[prompt, image_part]
            )

            result_text = response.text.strip() if response.text else "Aucun texte généré pour cette image."

            return {
                "success": True,
                "scan_mode": scan_mode,
                "analysis": result_text,
                "model_used": "gemini-3.5-flash",
                "image_size_bytes": len(image_bytes)
            }
        except Exception as e:
            logger.error(f"Erreur analyse caméra: {e}")
            return {
                "success": False,
                "error": str(e),
                "scan_mode": scan_mode
            }
