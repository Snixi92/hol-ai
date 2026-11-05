"""
SubscriptionAuditorAgent : Agent d'audit automatisé des abonnements et relevés bancaires pour HoL AI.
Inspiré de la fonctionnalité star de Meta Muse (Muse AI) :
- Détection des prélèvements récurrents (SaaS, streaming, salle de sport, télécoms, assurances).
- Calcul du coût mensuel, annuel et identification des dépenses oubliées / superflues.
- Génération automatique de lettres de résiliation juridiquement conformes (Loi Hamon / Châtel en France).
"""
import re
import time
from typing import Dict, Any, List, Optional


class SubscriptionAuditorAgent:
    """Agent expert dans l'audit financier personnel et la chasse aux abonnements dormants."""

    KNOWN_SUBSCRIPTION_PATTERNS = [
        (r"(?i)(?:netflix|nflx)", "Netflix", 13.49, "Divertissement"),
        (r"(?i)(?:spotify|spotif)", "Spotify Premium", 10.99, "Musique"),
        (r"(?i)(?:apple\s*music|itunes|apple\.com\/bill)", "Apple Services", 10.99, "Cloud & Musique"),
        (r"(?i)(?:disney\s*(\+|plus))", "Disney+", 8.99, "Divertissement"),
        (r"(?i)(?:amazon\s*prime|amzn\s*prime)", "Amazon Prime", 6.99, "E-commerce & Vidéo"),
        (r"(?i)(?:youtube\s*premium|google\s*youtube)", "YouTube Premium", 12.99, "Divertissement"),
        (r"(?i)(?:chatgpt|openai)", "ChatGPT Plus", 20.00, "IA & Productivité"),
        (r"(?i)(?:canva)", "Canva Pro", 11.99, "Design"),
        (r"(?i)(?:basic[- ]?fit|fitness\s*park)", "Abonnement Salle de Sport", 29.99, "Santé & Fitness"),
        (r"(?i)(?:sfr|orange|bouygues|free\s*mobile|freebox)", "Forfait Télécom / Box", 29.99, "Télécoms"),
        (r"(?i)(?:adobe|creative\s*cloud)", "Adobe Creative Cloud", 26.29, "Création"),
        (r"(?i)(?:nordvpn|cyberghost|surfshark)", "VPN Service", 3.99, "Sécurité"),
        (r"(?i)(?:icloud)", "iCloud+ Storage", 2.99, "Stockage"),
        (r"(?i)(?:deezer)", "Deezer Premium", 10.99, "Musique"),
    ]

    @classmethod
    def audit_statement(cls, text_content: str) -> Dict[str, Any]:
        """
        Analyse le texte brut d'un relevé bancaire, d'un email ou d'une liste de transactions.
        Identifie les abonnements, calcule l'impact budgétaire et propose des résiliations.
        """
        t0 = time.time()
        detected_subscriptions: List[Dict[str, Any]] = []
        found_names = set()

        lines = [line.strip() for line in text_content.splitlines() if line.strip()]

        for pattern, name, default_price, category in cls.KNOWN_SUBSCRIPTION_PATTERNS:
            match = re.search(pattern, text_content)
            if match and name not in found_names:
                price = default_price
                price_match = re.search(rf"{pattern}.*?(\d+[.,]\d{{2}})\s*€?", text_content)
                if price_match:
                    try:
                        price = float(price_match.group(1).replace(",", "."))
                    except ValueError:
                        price = default_price

                detected_subscriptions.append({
                    "name": name,
                    "monthly_price_eur": round(price, 2),
                    "annual_cost_eur": round(price * 12, 2),
                    "category": category,
                    "detected_mention": match.group(0),
                    "is_often_dormant": name in ["Basic-Fit", "Abonnement Salle de Sport", "NordVPN", "Canva Pro", "Disney+"],
                    "cancellation_available": True
                })
                found_names.add(name)

        if not detected_subscriptions and ("prélèvement" in text_content.lower() or "facture" in text_content.lower()):
            generic_matches = re.findall(r"pr[eé]l[eè]vement\s+([A-Za-z0-9\s\-]+?)\s+(\d+[.,]\d{2})\s*€", text_content, re.IGNORECASE)
            for raw_name, raw_amt in generic_matches[:5]:
                try:
                    p = float(raw_amt.replace(",", "."))
                    name = raw_name.strip()
                    if name not in found_names:
                        detected_subscriptions.append({
                            "name": name,
                            "monthly_price_eur": round(p, 2),
                            "annual_cost_eur": round(p * 12, 2),
                            "category": "Autre Prélèvement",
                            "detected_mention": name,
                            "is_often_dormant": False,
                            "cancellation_available": True
                        })
                        found_names.add(name)
                except ValueError:
                    pass

        total_monthly = sum(s["monthly_price_eur"] for s in detected_subscriptions)
        total_annual = round(total_monthly * 12, 2)
        potential_savings_annual = sum(s["annual_cost_eur"] for s in detected_subscriptions if s["is_often_dormant"])

        duration_ms = round((time.time() - t0) * 1000, 1)

        return {
            "status": "success",
            "subscriptions_count": len(detected_subscriptions),
            "subscriptions": detected_subscriptions,
            "total_monthly_eur": round(total_monthly, 2),
            "total_annual_eur": total_annual,
            "potential_annual_savings_eur": round(potential_savings_annual, 2),
            "duration_ms": duration_ms,
            "verbal_summary": (
                f"J'ai scanné tes dépenses : {len(detected_subscriptions)} abonnements récurrents détectés, "
                f"pour un coût de {total_monthly:.2f} €/mois ({total_annual:.2f} €/an). "
                f"Tu pourrais économiser jusqu'à {potential_savings_annual:.2f} €/an sur des services potentiellement dormants !"
            )
        }

    @classmethod
    def generate_cancellation_letter(cls, service_name: str, user_name: str = "Client", contract_ref: str = "NON_SPECIFIE") -> str:
        """
        Génère une lettre de résiliation juridique en bonne et due forme (Loi Hamon / Châtel en France).
        """
        date_today = time.strftime("%d/%m/%Y")
        return f"""Objet : Résiliation de mon abonnement {service_name} (Réf: {contract_ref})

Madame, Monsieur,

Par la présente, je vous notifie formellement ma décision de résilier mon contrat d'abonnement souscrit auprès de votre service {service_name}, référencé sous le numéro {contract_ref}.

Conformément aux conditions générales de vente ainsi qu'aux dispositions légales en vigueur (notamment la Loi Hamon et l'article L. 215-1 du Code de la consommation), je vous demande de bien vouloir mettre fin à ce contrat à compter de la réception de cette demande, ou à l'échéance de la période d'engagement minimale.

Je vous remercie de bien vouloir me confirmer par retour écrit la bonne prise en compte de ma résiliation ainsi que la date effective de clôture de mon compte. Veuillez également cesser tout prélèvement automatique sur mon compte bancaire à compter de cette date.

Fait le {date_today},
{user_name}
"""
