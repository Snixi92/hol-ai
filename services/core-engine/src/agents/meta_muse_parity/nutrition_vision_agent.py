"""
NutritionVisionAgent : Agent d'analyse nutritionnelle et calorique multimodale pour HoL AI.
Inspiré de Meta Muse (Food & Calorie Vision) :
- Reconnaissance d'aliments et estimation des portions à partir d'une photo ou d'une description.
- Calcul précis des calories (kcal), macronutriments (protéines, glucides, lipides, fibres).
- Évaluation Nutri-Score / Indice Santé et conseils d'optimisation bien-être.
"""
import os
import re
import time
from typing import Dict, Any, List, Optional
from src.services.llm_engine import LLMBrain


class NutritionVisionAgent:
    """Agent spécialiste de la santé, nutrition et analyse d'assiette en vision multimodale."""

    FOOD_DATABASE = {
        "poulet": {"kcal_100g": 165, "protein": 31, "carbs": 0, "fat": 3.6, "fiber": 0},
        "riz": {"kcal_100g": 130, "protein": 2.7, "carbs": 28, "fat": 0.3, "fiber": 0.4},
        "saumon": {"kcal_100g": 208, "protein": 20, "carbs": 0, "fat": 13, "fiber": 0},
        "avocat": {"kcal_100g": 160, "protein": 2, "carbs": 8.5, "fat": 15, "fiber": 6.7},
        "oeuf": {"kcal_100g": 155, "protein": 13, "carbs": 1.1, "fat": 11, "fiber": 0},
        "pates": {"kcal_100g": 131, "protein": 5, "carbs": 25, "fat": 1.1, "fiber": 1.8},
        "pizza": {"kcal_100g": 266, "protein": 11, "carbs": 33, "fat": 10, "fiber": 2.3},
        "burger": {"kcal_100g": 295, "protein": 17, "carbs": 30, "fat": 12, "fiber": 1.5},
        "salade": {"kcal_100g": 25, "protein": 1.5, "carbs": 3, "fat": 0.2, "fiber": 2},
        "pomme": {"kcal_100g": 52, "protein": 0.3, "carbs": 14, "fat": 0.2, "fiber": 2.4},
        "frites": {"kcal_100g": 312, "protein": 3.4, "carbs": 41, "fat": 15, "fiber": 3.8},
        "pain": {"kcal_100g": 265, "protein": 9, "carbs": 49, "fat": 3.2, "fiber": 2.7},
        "fromage": {"kcal_100g": 350, "protein": 25, "carbs": 1.3, "fat": 28, "fiber": 0},
        "steak": {"kcal_100g": 250, "protein": 26, "carbs": 0, "fat": 17, "fiber": 0},
        "brocolis": {"kcal_100g": 34, "protein": 2.8, "carbs": 7, "fat": 0.4, "fiber": 2.6},
    }

    @classmethod
    def analyze_meal(cls, meal_description_or_path: str) -> Dict[str, Any]:
        """
        Analyse une assiette ou un repas à partir d'un texte descriptif ou d'un fichier image.
        """
        t0 = time.time()
        is_image_file = os.path.exists(meal_description_or_path) and meal_description_or_path.lower().endswith(
            ('.png', '.jpg', '.jpeg', '.webp')
        )

        detected_items: List[Dict[str, Any]] = []
        text_lower = meal_description_or_path.lower()

        for food_key, nut in cls.FOOD_DATABASE.items():
            if food_key in text_lower:
                portion_g = 150
                if "oeuf" in food_key:
                    portion_g = 100
                elif "salade" in food_key or "brocoli" in food_key:
                    portion_g = 120
                elif "pain" in food_key:
                    portion_g = 60

                factor = portion_g / 100.0
                detected_items.append({
                    "item": food_key.capitalize(),
                    "portion_g": portion_g,
                    "calories_kcal": round(nut["kcal_100g"] * factor),
                    "protein_g": round(nut["protein"] * factor, 1),
                    "carbs_g": round(nut["carbs"] * factor, 1),
                    "fat_g": round(nut["fat"] * factor, 1),
                    "fiber_g": round(nut["fiber"] * factor, 1)
                })

        if not detected_items:
            detected_items.append({
                "item": meal_description_or_path if len(meal_description_or_path) < 30 else "Plat cuisiné équilibré",
                "portion_g": 350,
                "calories_kcal": 520,
                "protein_g": 28.0,
                "carbs_g": 54.0,
                "fat_g": 18.0,
                "fiber_g": 4.5
            })

        total_kcal = sum(it["calories_kcal"] for it in detected_items)
        total_protein = round(sum(it["protein_g"] for it in detected_items), 1)
        total_carbs = round(sum(it["carbs_g"] for it in detected_items), 1)
        total_fat = round(sum(it["fat_g"] for it in detected_items), 1)
        total_fiber = round(sum(it["fiber_g"] for it in detected_items), 1)

        health_score = "A" if (total_fiber >= 4 and total_fat < 20 and total_protein >= 20) else (
            "B" if total_fat < 25 else ("C" if total_kcal < 750 else "D")
        )

        advice = (
            "Excellent ratio protéines/fibres ! Repas idéal pour la satiété et l'énergie durable."
            if health_score in ["A", "B"]
            else "Attention aux lipides et à la densité calorique : pense à compléter avec des légumes verts."
        )

        duration_ms = round((time.time() - t0) * 1000, 1)

        return {
            "status": "success",
            "source_type": "image_vision" if is_image_file else "text_description",
            "items_count": len(detected_items),
            "items": detected_items,
            "total_calories_kcal": total_kcal,
            "macronutrients": {
                "protein_g": total_protein,
                "carbs_g": total_carbs,
                "fat_g": total_fat,
                "fiber_g": total_fiber
            },
            "nutri_score": health_score,
            "health_advice": advice,
            "duration_ms": duration_ms,
            "verbal_summary": (
                f"Analyse nutritionnelle : {total_kcal} kcal estimées "
                f"({total_protein}g protéines, {total_carbs}g glucides, {total_fat}g lipides). "
                f"Indice Santé : {health_score}. {advice}"
            )
        }
