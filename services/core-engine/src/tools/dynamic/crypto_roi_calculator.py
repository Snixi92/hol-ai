"""
Outil dynamique : crypto_roi_calculator
Description: Calcule le retour sur investissement d'un portefeuille crypto
Généré par HoL AI DynamicToolSynthesizerAgent
"""

def calculate_crypto_roi(invested_eur: float, current_eur: float) -> float:
    return round(((current_eur - invested_eur) / invested_eur) * 100, 2)
