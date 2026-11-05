"""
Transformation script to update services/core-engine/src/api/static/index.html
for Requirement R4 (Apple Liquid Glass UI/UX & Luxury Palette).
"""
import re
import sys
from pathlib import Path

index_path = Path(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html")
content = index_path.read_text(encoding="utf-8")
print(f"Original index.html length: {len(content)} chars, {len(content.splitlines())} lines")

# 1. Update CSS variables in :root
root_old = """:root {
            --glass-blur: 28px;
            --glass-saturate: 190%;
            --glass-contrast: 105%;
            --spring-standard: cubic-bezier(0.22, 1, 0.36, 1);
            --spring-bounce: cubic-bezier(0.16, 1, 0.3, 1);
            --spring-snappy: cubic-bezier(0.2, 0, 0, 1);"""

root_new = """:root {
            --glass-blur: 24px;
            --glass-saturate: 180%;
            --glass-contrast: 105%;
            --spring-standard: cubic-bezier(0.175, 0.885, 0.32, 1.275);
            --spring-bounce: cubic-bezier(0.175, 0.885, 0.32, 1.275);
            --spring-physics: cubic-bezier(0.175, 0.885, 0.32, 1.275);
            --spring-snappy: cubic-bezier(0.2, 0, 0, 1);"""

if root_old in content:
    content = content.replace(root_old, root_new, 1)
    print("[OK] Replaced :root variables")
else:
    print("[SKIP] :root variables already updated or not found")

# 2. Update .liquid-glass, .liquid-glass-regular, .liquid-glass-dock, .liquid-glass-subtle
glass_old_block = """        /* --- MOTEUR LIQUID GLASS APPLE iOS 27 (MASTER SPEC "REGULAR GLASS") --- */

        .liquid-glass, .liquid-glass-regular {
            position: relative;
            background: 
                linear-gradient(135deg, rgba(255, 255, 255, 0.14) 0%, rgba(255, 255, 255, 0.025) 35%, rgba(0, 0, 0, 0.06) 65%, rgba(255, 255, 255, 0.09) 100%),
                rgba(14, 14, 18, 0.52);
            backdrop-filter: blur(28px) saturate(220%) contrast(108%);
            -webkit-backdrop-filter: blur(28px) saturate(220%) contrast(108%);
            border: 1px solid rgba(255, 255, 255, 0.20);
            box-shadow: 
                /* Arête spéculaire supérieure ultra-fine rasoir */
                inset 0 1.6px 2px 0 rgba(255, 255, 255, 0.85),
                /* Réfraction d'ombre inférieure (effet d'épaisseur de lentille) */
                inset 0 -2px 3px 0 rgba(0, 0, 0, 0.50),
                /* Biseau latéral gauche */
                inset 2px 0 3px 0 rgba(255, 255, 255, 0.30),
                /* Biseau latéral droit */
                inset -2px 0 3px 0 rgba(255, 255, 255, 0.18),
                /* Micro-aberration chromatique périphérique */
                0 0 1px 0 rgba(255, 80, 80, 0.15),
                0 0 2px 0 rgba(80, 160, 255, 0.15),
                /* Ombre volumétrique douce et diffuse */
                0 28px 64px -10px rgba(0, 0, 0, 0.82);
            transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1),
                        box-shadow 0.35s cubic-bezier(0.22, 1, 0.36, 1);
        }

        /* Réfraction interactive au survol & toucher (Dynamisme optique de Fresnel) */
        .liquid-glass::before, .liquid-glass-regular::before {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: inherit;
            background: radial-gradient(
                circle 280px at var(--mouse-x, 50%) var(--mouse-y, 50%),
                rgba(255, 255, 255, 0.28) 0%,
                rgba(255, 255, 255, 0.05) 40%,
                transparent 70%
            );
            opacity: 0.92;
            pointer-events: none;
            transition: opacity 0.25s ease;
        }

        /* Dock flottant : Master Capsule Fluide Apple Liquid Glass */
        .liquid-glass-dock {
            position: relative;
            background: 
                linear-gradient(135deg, rgba(255, 255, 255, 0.16) 0%, rgba(255, 255, 255, 0.02) 35%, rgba(0, 0, 0, 0.05) 65%, rgba(255, 255, 255, 0.10) 100%),
                rgba(14, 14, 18, 0.52);
            backdrop-filter: blur(32px) saturate(220%) contrast(108%);
            -webkit-backdrop-filter: blur(32px) saturate(220%) contrast(108%);
            border: 1px solid rgba(255, 255, 255, 0.22);
            box-shadow: 
                inset 0 1.8px 2.5px 0 rgba(255, 255, 255, 0.88),
                inset 0 -2.2px 3.5px 0 rgba(0, 0, 0, 0.55),
                inset 2.2px 0 3.5px 0 rgba(255, 255, 255, 0.35),
                inset -2.2px 0 3.5px 0 rgba(255, 255, 255, 0.20),
                0 0 1px 0 rgba(255, 80, 80, 0.16),
                0 0 2px 0 rgba(80, 160, 255, 0.16),
                0 32px 72px -12px rgba(0, 0, 0, 0.85);
        }

        .liquid-glass-dock::before {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: inherit;
            background: radial-gradient(
                circle 320px at var(--mouse-x, 50%) var(--mouse-y, 50%),
                rgba(255, 255, 255, 0.30) 0%,
                rgba(255, 255, 255, 0.06) 40%,
                transparent 70%
            );
            opacity: 0.95;
            pointer-events: none;
            transition: opacity 0.25s ease;
        }

        /* Thème clair : Liquid Glass cristal pur poli */
        html:not(.dark) .liquid-glass, 
        html:not(.dark) .liquid-glass-regular,
        html:not(.dark) .liquid-glass-dock {
            background: 
                linear-gradient(135deg, rgba(255, 255, 255, 0.82) 0%, rgba(255, 255, 255, 0.36) 35%, rgba(240, 240, 248, 0.25) 65%, rgba(255, 255, 255, 0.55) 100%),
                rgba(255, 255, 255, 0.68);
            border: 1px solid rgba(255, 255, 255, 0.95);
            box-shadow: 
                inset 0 1.6px 2px 0 rgba(255, 255, 255, 0.98),
                inset 0 -1.6px 2px 0 rgba(0, 0, 0, 0.06),
                inset 1.6px 0 2px 0 rgba(255, 255, 255, 0.60),
                inset -1.6px 0 2px 0 rgba(255, 255, 255, 0.40),
                0 20px 48px -10px rgba(15, 23, 42, 0.14);
        }

        /* Contrôles et pills subtils en Liquid Glass */
        .liquid-glass-subtle {
            position: relative;
            background: 
                linear-gradient(135deg, rgba(255, 255, 255, 0.10) 0%, rgba(255, 255, 255, 0.02) 50%, rgba(255, 255, 255, 0.06) 100%),
                rgba(255, 255, 255, 0.06);
            backdrop-filter: blur(20px) saturate(190%);
            -webkit-backdrop-filter: blur(20px) saturate(190%);
            border: 1px solid rgba(255, 255, 255, 0.14);
            box-shadow: 
                inset 0 1px 1.5px 0 rgba(255, 255, 255, 0.45),
                inset 0 -1px 1px 0 rgba(0, 0, 0, 0.25),
                0 10px 28px -6px rgba(0, 0, 0, 0.40);
        }

        html:not(.dark) .liquid-glass-subtle {
            background: rgba(255, 255, 255, 0.88);
            backdrop-filter: blur(20px) saturate(190%);
            -webkit-backdrop-filter: blur(20px) saturate(190%);
            border: 1px solid rgba(255, 255, 255, 0.92);
            box-shadow: 
                inset 0 1px 1.5px 0 rgba(255, 255, 255, 0.95),
                0 8px 24px -6px rgba(15, 23, 42, 0.06);
        }"""

glass_new_block = """        /* --- MOTEUR LIQUID GLASS APPLE iOS 27 (MASTER SPEC "REGULAR GLASS") --- */

        .liquid-glass, .liquid-glass-regular {
            position: relative;
            background: 
                linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 35%, rgba(0, 0, 0, 0.15) 65%, rgba(255, 255, 255, 0.05) 100%),
                rgba(12, 12, 16, 0.68);
            backdrop-filter: blur(24px) saturate(180%) contrast(105%);
            -webkit-backdrop-filter: blur(24px) saturate(180%) contrast(105%);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-top: 1px solid rgba(255, 255, 255, 0.22);
            box-shadow: 
                inset 0 1px 1px 0 rgba(255, 255, 255, 0.18),
                inset 0 -1px 1px 0 rgba(0, 0, 0, 0.4),
                0 20px 40px -15px rgba(0, 0, 0, 0.7);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        /* Réfraction interactive au survol & toucher (Dynamisme optique de Fresnel) */
        .liquid-glass::before, .liquid-glass-regular::before {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: inherit;
            background: radial-gradient(
                circle 280px at var(--mouse-x, 50%) var(--mouse-y, 50%),
                rgba(255, 255, 255, 0.18) 0%,
                rgba(255, 255, 255, 0.03) 40%,
                transparent 70%
            );
            opacity: 0.85;
            pointer-events: none;
            transition: opacity 0.25s ease;
        }

        /* Dock flottant : Master Capsule Fluide Apple Liquid Glass */
        .liquid-glass-dock {
            position: relative;
            background: 
                linear-gradient(135deg, rgba(255, 255, 255, 0.10) 0%, rgba(255, 255, 255, 0.02) 35%, rgba(0, 0, 0, 0.20) 65%, rgba(255, 255, 255, 0.06) 100%),
                rgba(12, 12, 16, 0.72);
            backdrop-filter: blur(24px) saturate(180%) contrast(105%);
            -webkit-backdrop-filter: blur(24px) saturate(180%) contrast(105%);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-top: 1px solid rgba(255, 255, 255, 0.22);
            box-shadow: 
                inset 0 1px 1px 0 rgba(255, 255, 255, 0.18),
                inset 0 -1px 1px 0 rgba(0, 0, 0, 0.4),
                0 20px 40px -15px rgba(0, 0, 0, 0.7);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        .liquid-glass-dock:hover, .liquid-glass-dock:focus-within {
            box-shadow: 
                inset 0 1px 1.5px 0 rgba(255, 255, 255, 0.25),
                inset 0 -1px 1px 0 rgba(0, 0, 0, 0.45),
                0 24px 48px -12px rgba(0, 0, 0, 0.8);
            transform: translateY(-2px);
        }

        .liquid-glass-dock::before {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: inherit;
            background: radial-gradient(
                circle 320px at var(--mouse-x, 50%) var(--mouse-y, 50%),
                rgba(255, 255, 255, 0.22) 0%,
                rgba(255, 255, 255, 0.04) 40%,
                transparent 70%
            );
            opacity: 0.90;
            pointer-events: none;
            transition: opacity 0.25s ease;
        }

        /* Thème clair : Liquid Glass cristal pur poli */
        html:not(.dark) .liquid-glass, 
        html:not(.dark) .liquid-glass-regular,
        html:not(.dark) .liquid-glass-dock {
            background: 
                linear-gradient(135deg, rgba(255, 255, 255, 0.85) 0%, rgba(255, 255, 255, 0.40) 35%, rgba(240, 240, 248, 0.30) 65%, rgba(255, 255, 255, 0.60) 100%),
                rgba(255, 255, 255, 0.75);
            backdrop-filter: blur(24px) saturate(180%) contrast(105%);
            -webkit-backdrop-filter: blur(24px) saturate(180%) contrast(105%);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-top: 1px solid rgba(255, 255, 255, 0.90);
            box-shadow: 
                inset 0 1px 1px 0 rgba(255, 255, 255, 0.95),
                inset 0 -1px 1px 0 rgba(0, 0, 0, 0.05),
                0 16px 36px -8px rgba(15, 23, 42, 0.12);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        /* Contrôles et pills subtils en Liquid Glass */
        .liquid-glass-subtle {
            position: relative;
            background: 
                linear-gradient(135deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.01) 50%, rgba(255, 255, 255, 0.04) 100%),
                rgba(20, 20, 26, 0.55);
            backdrop-filter: blur(24px) saturate(180%) contrast(105%);
            -webkit-backdrop-filter: blur(24px) saturate(180%) contrast(105%);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-top: 1px solid rgba(255, 255, 255, 0.22);
            box-shadow: 
                inset 0 1px 1px 0 rgba(255, 255, 255, 0.18),
                inset 0 -1px 1px 0 rgba(0, 0, 0, 0.4),
                0 20px 40px -15px rgba(0, 0, 0, 0.7);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        html:not(.dark) .liquid-glass-subtle {
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(24px) saturate(180%) contrast(105%);
            -webkit-backdrop-filter: blur(24px) saturate(180%) contrast(105%);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-top: 1px solid rgba(255, 255, 255, 0.85);
            box-shadow: 
                inset 0 1px 1px 0 rgba(255, 255, 255, 0.90),
                0 8px 24px -6px rgba(15, 23, 42, 0.06);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }"""

if glass_old_block in content:
    content = content.replace(glass_old_block, glass_new_block, 1)
    print("[OK] Replaced liquid-glass classes calibration")
else:
    print("[SKIP] glass_old_block already updated or not found")

# 3. Update .chat-form-liquid in style
form_old = """/* Master Liquid Glass Chat Form */
.chat-form-liquid {
  background: rgba(14, 18, 28, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.14);
  box-shadow: inset 0 1px 1.5px rgba(255, 255, 255, 0.15), inset 0 0 0 1px rgba(255, 255, 255, 0.05), 0 8px 24px -6px rgba(0, 0, 0, 0.5);
}"""

form_new = """/* Master Liquid Glass Chat Form */
.chat-form-liquid {
  background: rgba(14, 14, 20, 0.60);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-top: 1px solid rgba(255, 255, 255, 0.22);
  box-shadow: inset 0 1px 1px 0 rgba(255, 255, 255, 0.18), inset 0 -1px 1px 0 rgba(0, 0, 0, 0.4), 0 8px 24px -6px rgba(0, 0, 0, 0.5);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.chat-form-liquid:focus-within {
  border-color: rgba(255, 255, 255, 0.28);
  border-top-color: rgba(255, 255, 255, 0.40);
  box-shadow: inset 0 1px 1.5px 0 rgba(255, 255, 255, 0.25), inset 0 -1px 1px 0 rgba(0, 0, 0, 0.4), 0 12px 32px -6px rgba(0, 0, 0, 0.65);
}

/* Markdown Code Block Container */
.code-block-container {
  background: #09090d;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-top: 1px solid rgba(255, 255, 255, 0.22);
  box-shadow: inset 0 1px 1px 0 rgba(255, 255, 255, 0.12), 0 12px 28px -8px rgba(0, 0, 0, 0.6);
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.copy-code-btn {
  cursor: pointer;
  user-select: none;
}
.copy-code-btn:active {
  transform: scale(0.95);
}"""

if form_old in content:
    content = content.replace(form_old, form_new, 1)
    print("[OK] Replaced chat-form-liquid & added code-block-container CSS")
else:
    print("[SKIP] form_old already updated")

# 4. Dock HTML neutral palette & cyan elimination
dock_dot_old = '<span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse flex-shrink-0 mr-1.5"></span>'
dock_dot_new = '<span class="w-2 h-2 rounded-full bg-white/80 animate-pulse flex-shrink-0 mr-1.5"></span>'
if dock_dot_old in content:
    content = content.replace(dock_dot_old, dock_dot_new, 1)

dock_orb_old = '<canvas id="header-thinking-orb" class="w-4 h-4 shrink-0 inline-block drop-shadow-[0_0_8px_rgba(56,189,248,0.5)] mr-1"></canvas>'
dock_orb_new = '<canvas id="header-thinking-orb" class="w-4 h-4 shrink-0 inline-block drop-shadow-[0_0_8px_rgba(255,255,255,0.25)] mr-1"></canvas>'
if dock_orb_old in content:
    content = content.replace(dock_orb_old, dock_orb_new, 1)

dock_form_old = 'class="relative flex items-center chat-form-liquid rounded-[22px] sm:rounded-[26px] focus-within:border-white/30 focus-within:shadow-[0_0_20px_rgba(56,189,248,0.12)] transition p-1"'
dock_form_new = 'class="relative flex items-center chat-form-liquid rounded-[22px] sm:rounded-[26px] focus-within:border-white/30 focus-within:shadow-[0_0_20px_rgba(255,255,255,0.08)] transition p-1"'
if dock_form_old in content:
    content = content.replace(dock_form_old, dock_form_new, 1)
print("[OK] Replaced Dock HTML cyan/emerald tokens with luxury neutral tokens")

# 5. Header comments with emojis
content = content.replace("<!-- 1. [ 🌐 ] Computer-Use -->", "<!-- 1. [ Browser ] Computer-Use -->")
content = content.replace("<!-- 2. [ 🤖 ] Jarvis Cockpit / IA Robot -->", "<!-- 2. [ Cockpit ] Jarvis Cockpit / IA Robot -->")
content = content.replace("<!-- 3. [ 📱 ] Version Mobile -->", "<!-- 3. [ Mobile ] Version Mobile -->")
content = content.replace("<!-- 4. [ 🌙 ] Thème Clair / Sombre -->", "<!-- 4. [ Theme ] Thème Clair / Sombre -->")
content = content.replace("<!-- 5. [ 🟢 Veilles 24/7 ] Missions -->", "<!-- 5. [ Watch ] Missions -->")
content = content.replace("<!-- 6. [ ⚙️ Réglages ] Paramètres -->", "<!-- 6. [ Settings ] Paramètres -->")
content = content.replace('<span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse inline-block mr-1"></span>', '<span class="w-2 h-2 rounded-full bg-white/80 animate-pulse inline-block mr-1"></span>')
print("[OK] Cleaned Header comments and status dot")

# 6. Carousel and HUD emojis
content = content.replace("""<span id="hero-carousel-status" class="text-[9px] font-mono px-1.5 py-0.5 rounded-md bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center space-x-1">
                                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                                <span>Actif ✓</span>
                            </span>""", """<span id="hero-carousel-status" class="text-[9px] font-mono px-1.5 py-0.5 rounded-md bg-white/10 text-neutral-200 border border-white/20 flex items-center space-x-1">
                                <span class="w-1.5 h-1.5 rounded-full bg-white/80 animate-pulse"></span>
                                <span>Actif</span>
                            </span>""")

content = content.replace("""                    <div class="w-full h-full bg-[#090d1a] rounded-[10px] flex items-center justify-center font-mono font-bold text-neutral-200 text-sm">

                        ⚡

                    </div>""", """                    <div class="w-full h-full bg-[#090d1a] rounded-[10px] flex items-center justify-center font-mono font-bold text-neutral-200 text-sm">
                        <i data-lucide="zap" class="w-4 h-4 text-neutral-200"></i>
                    </div>""")

content = content.replace("Ciel printanier agréable 🌤️, vent 12 km/h", "Ciel printanier agréable, vent 12 km/h")
content = content.replace('<span id="speech-state-badge" class="text-emerald-400 font-mono">🔊 Prête</span>', '<span id="speech-state-badge" class="text-neutral-200 font-mono flex items-center space-x-1"><i data-lucide="volume-2" class="w-3.5 h-3.5 inline"></i><span>Prête</span></span>')
content = content.replace("Tapez deux fois des mains 👏 ou appuyez sur [Espace] pour déclencher le Jarvis Morning Briefing...", "Tapez deux fois des mains ou appuyez sur [Espace] pour déclencher le Jarvis Morning Briefing...")
print("[OK] Cleaned Carousel & HUD icons")

# 7. Settings dialog icons
content = content.replace("💡 <strong>Authentification Recommandée :</strong>", '<i data-lucide="info" class="w-3.5 h-3.5 inline mr-1 text-neutral-300"></i><strong>Authentification Recommandée :</strong>')
content = content.replace("📱 Créez un bot sur Telegram", '<i data-lucide="send" class="w-3.5 h-3.5 inline mr-1 text-neutral-300"></i>Créez un bot sur Telegram')
content = content.replace("🧠 Clé d'accès au modèle", '<i data-lucide="key" class="w-3.5 h-3.5 inline mr-1 text-neutral-300"></i>Clé d\'accès au modèle')
print("[OK] Cleaned Settings modal badges")

# 8. Thinking steps emojis line by line
content = content.replace('\U0001f310 Recherche sur le web', 'Recherche sur le web')
content = content.replace('\U0001f9e0 Analyse du produit...', 'Analyse du produit...')
content = content.replace('\U0001f6cd\ufe0f Recherche et comparaison', 'Recherche et comparaison')
content = content.replace('\U0001f3f7\ufe0f V\xe9rification des stocks', 'V\xe9rification des stocks')
content = content.replace('Vérification des stocks et des tarifs...', 'Vérification des stocks et des tarifs...')
content = content.replace('\u270d\ufe0f Pr\xe9paration des meilleures offres...', 'Pr\xe9paration des meilleures offres...')
content = content.replace('\U0001f9e0 Analyse de la commande', 'Analyse de la commande')
content = content.replace('\u26a1 Pr\xe9paration du contr\xf4le PC...', 'Pr\xe9paration du contr\xf4le PC...')
content = content.replace('\U0001f680 Ex\xe9cution de l\'action sur ton \xe9cran...', 'Ex\xe9cution de l\'action sur votre \xe9cran...')
content = content.replace('\U0001f9e0 Conception de l\'architecture...', 'Conception de l\'architecture...')
content = content.replace('\U0001f4bb G\xe9n\xe9ration du code source', 'G\xe9n\xe9ration du code source')
content = content.replace('\u2728 Finalisation de l\'application...', 'Finalisation de l\'application...')
content = content.replace('\u2728 Exploration des connaissances...', 'Exploration des connaissances...')
print("[OK] Cleaned thinking steps emojis")

# 9. Card emojis in renderChatCard
content = content.replace("<span>${d.icon || '🏷️'}</span>", '<span><i data-lucide="tag" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("⚡ Annonces spécifiques recommandées", '<i data-lucide="sparkles" class="w-3 h-3 inline mr-1 text-neutral-400"></i>Annonces spécifiques recommandées')
content = content.replace("<span>🎯</span>", '<span><i data-lucide="crosshair" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("⚡ ${escapeHtml(data.merchant_selected || 'Amazon')}", '${escapeHtml(data.merchant_selected || "Amazon")}')
content = content.replace("<span>🛒</span>", '<span><i data-lucide="shopping-cart" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace('const title = data.title || "🎯 Précisions pour cibler les meilleures offres sur tout le Web";', 'const title = data.title || "Précisions pour cibler les meilleures offres sur tout le Web";')
content = content.replace("<span>✨</span>", '<span><i data-lucide="sparkles" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("💡 Réponse rapide en 1 clic :", '<i data-lucide="lightbulb" class="w-3.5 h-3.5 inline mr-1 text-neutral-400"></i>Réponse rapide en 1 clic :')
content = content.replace("<span>${p.icon || '🏷️'}</span>", '<span><i data-lucide="tag" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("<span>🛍️</span>", '<span><i data-lucide="shopping-bag" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("<span>${p.icon || '📦'}</span>", '<span><i data-lucide="package" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("⚡ Offres extraites en direct sur le Web :", '<i data-lucide="zap" class="w-3 h-3 inline mr-1 text-neutral-400"></i>Offres extraites en direct sur le Web :')
content = content.replace("<span>🔍</span>", '<span><i data-lucide="search" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("📦 Colis ${escapeHtml(data.carrier || 'UPS')}", '<i data-lucide="package" class="w-3.5 h-3.5 inline mr-1 text-neutral-400"></i>Colis ${escapeHtml(data.carrier || "UPS")}')
content = content.replace("📍 ${escapeHtml(data.current_location || 'Centre de tri')}", '<i data-lucide="map-pin" class="w-3.5 h-3.5 inline mr-1 text-neutral-400"></i>${escapeHtml(data.current_location || "Centre de tri")}')
content = content.replace('<span class="text-base">⚡</span>', '<i data-lucide="zap" class="w-4 h-4 text-neutral-300"></i>')
content = content.replace("<span>${escapeHtml(weather.condition || '☀️')}</span>", '<span><i data-lucide="sun" class="w-4 h-4 text-neutral-300"></i></span>')
content = content.replace('<span class="text-emerald-500 font-bold">💳 Stripe / E-com</span>', '<span class="text-neutral-200 font-bold flex items-center space-x-1"><i data-lucide="credit-card" class="w-3.5 h-3.5 inline"></i><span>Stripe / E-com</span></span>')
content = content.replace("<span>📅</span>", '<span><i data-lucide="calendar" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("<span>✉️</span>", '<span><i data-lucide="mail" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("<span>📦</span>", '<span><i data-lucide="package" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("const icon = isClose ? '🛑' : '🚀';", 'const icon = isClose ? \'<i data-lucide="square" class="w-3.5 h-3.5 inline text-neutral-400"></i>\' : \'<i data-lucide="arrow-up-right" class="w-3.5 h-3.5 inline text-neutral-400"></i>\';')
content = content.replace("<div>📁 Dossier : <strong>/static/apps/${escapeHtml(appName)}/</strong></div>", '<div><i data-lucide="folder" class="w-3.5 h-3.5 inline mr-1 text-neutral-400"></i>Dossier : <strong>/static/apps/${escapeHtml(appName)}/</strong></div>')
content = content.replace('<div class="text-emerald-400">✓ index.html • style.css • script.js</div>', '<div class="text-neutral-300 flex items-center"><i data-lucide="check" class="w-3 h-3 inline mr-1 text-neutral-300"></i>index.html • style.css • script.js</div>')
content = content.replace('<span class="text-neutral-200">📊</span>', '<i data-lucide="bar-chart-2" class="w-3.5 h-3.5 inline text-neutral-400"></i>')
content = content.replace("${scheduled ? `📅 Programmé : <strong class=\"text-neutral-200\">${escapeHtml(scheduled)}</strong>` : '⚡ Prêt à publier'}", '${scheduled ? `Programmé : <strong class="text-neutral-200">${escapeHtml(scheduled)}</strong>` : "Prêt à publier"}')
content = content.replace('🖼️ ${escapeHtml(title)}', '<i data-lucide="image" class="w-3.5 h-3.5 inline mr-1 text-neutral-300"></i>${escapeHtml(title)}')
content = content.replace("<span>📄</span>", '<span><i data-lucide="file-text" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("<span>✍️</span>", '<span><i data-lucide="pen-tool" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("<span>✂️</span>", '<span><i data-lucide="scissors" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("<span>📂</span>", '<span><i data-lucide="folder" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("${item.is_dir ? '📁' : '📄'} ${escapeHtml(item.path)}", '${item.is_dir ? \'<i data-lucide="folder" class="w-3 h-3 inline mr-1 text-neutral-400"></i>\' : \'<i data-lucide="file-text" class="w-3 h-3 inline mr-1 text-neutral-400"></i>\'}${escapeHtml(item.path)}')
content = content.replace('<span class="text-neutral-200">💻</span>', '<i data-lucide="terminal" class="w-3.5 h-3.5 inline text-neutral-400"></i>')
content = content.replace("<span>📖</span>", '<span><i data-lucide="book-open" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("<span>🤖</span>", '<span><i data-lucide="bot" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("💾 ${escapeHtml(path)}", '<i data-lucide="save" class="w-3.5 h-3.5 inline mr-1 text-neutral-400"></i>${escapeHtml(path)}')
content = content.replace("🧪 Test :", '<i data-lucide="flask-conical" class="w-3.5 h-3.5 inline mr-1 text-neutral-400"></i>Test :')
content = content.replace("<span>🏛️</span>", '<span><i data-lucide="landmark" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("<span>📊</span>", '<span><i data-lucide="pie-chart" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("<span>🥗</span>", '<span><i data-lucide="activity" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("💡 ${escapeHtml(advice)}", '<i data-lucide="lightbulb" class="w-3.5 h-3.5 inline mr-1 text-neutral-400"></i>${escapeHtml(advice)}')
content = content.replace("<span>💬</span>", '<span><i data-lucide="message-square" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("<span>🍳</span>", '<span><i data-lucide="utensils" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("<span>👤</span>", '<span><i data-lucide="user" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("<span>💳</span>", '<span><i data-lucide="credit-card" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("<span>🛡️</span>", '<span><i data-lucide="shield" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace('btn.innerHTML = `<span>✓ Validé & Signé (${d.tx_hash.slice(0, 8)}...)</span>`;', 'btn.innerHTML = `<span>Validé & Signé (${d.tx_hash.slice(0, 8)}...)</span>`;')
content = content.replace('btn.innerHTML = `<span>✓ Publié sur LinkedIn !</span>`;', 'btn.innerHTML = `<span>Publié sur LinkedIn !</span>`;')
content = content.replace('if (input) input.placeholder = "🎙️ Parle maintenant... j\'écoute...";', 'if (input) input.placeholder = "Parle maintenant... j\'écoute...";')
content = content.replace('<button type="button" onclick="cancelAttachment()" class="text-slate-400 hover:text-rose-500 px-1 font-bold">✕</button>', '<button type="button" onclick="cancelAttachment()" class="text-slate-400 hover:text-white px-1 font-bold"><i data-lucide="x" class="w-3.5 h-3.5 inline"></i></button>')
content = content.replace("if (stateBadge) stateBadge.innerText = '⚡ Analyse';", "if (stateBadge) stateBadge.innerText = 'Analyse';")
content = content.replace("if (stateBadge) stateBadge.innerText = '✅ Prêt';", "if (stateBadge) stateBadge.innerText = 'Prêt';")
content = content.replace("if (stateBadge) stateBadge.innerText = '🔊 Voix Active';", "if (stateBadge) stateBadge.innerText = 'Voix Active';")
content = content.replace("btnBadge.innerText = '👏 Clap ON';", "btnBadge.innerText = 'Clap ON';")
content = content.replace("btnBadge.innerText = '👏 Clap OFF';", "btnBadge.innerText = 'Clap OFF';")
content = content.replace("if (hudToggleLabel) hudToggleLabel.innerText = '👂 Détecteur Clap : ACTIF';", "if (hudToggleLabel) hudToggleLabel.innerText = 'Détecteur Clap : ACTIF';")
content = content.replace("if (hudToggleLabel) hudToggleLabel.innerText = '👂 Détecteur Clap : CLIQUEZ ICI';", "if (hudToggleLabel) hudToggleLabel.innerText = 'Détecteur Clap : CLIQUEZ ICI';")
content = content.replace('🤖 MODE IA SPECTATEUR', 'MODE IA SPECTATEUR')
content = content.replace('cuTakeOverBtn.innerHTML = "<span>🤖</span><span>Rendre la main à l\'IA</span>";', 'cuTakeOverBtn.innerHTML = "<i data-lucide=\'bot\' class=\'w-3.5 h-3.5 inline mr-1\'></i><span>Rendre la main à l\'IA</span>";')
print("[OK] Replaced all card emojis with Lucide vector icons")

# 10. Upgraded formatMarkdown implementation
format_md_regex = re.compile(r'function formatMarkdown\(text\)\s*\{[\s\S]*?^\s*\}', re.MULTILINE)
format_md_match = format_md_regex.search(content)
assert format_md_match, "Could not find formatMarkdown regex match"

new_format_md = """function formatMarkdown(text) {
            if (!text) return '';

            // 1. Isolate and protect fenced code blocks
            const codeBlocks = [];
            let processed = text.replace(/```([a-zA-Z0-9_\\-\\+]*)\\n([\\s\\S]*?)```/g, function(match, lang, code) {
                const blockId = '%%CODE_BLOCK_' + codeBlocks.length + '_' + Math.random().toString(36).substring(2, 7) + '%%';
                const language = (lang || 'code').trim().toLowerCase();
                const displayLang = language ? language.toUpperCase() : 'CODE';
                const escaped = escapeHtml(code.replace(/\\r\\n/g, '\\n').replace(/\\n+$/, ''));
                
                const html = `
                    <div class="code-block-container my-3 rounded-xl overflow-hidden border border-white/10 bg-[#09090d] shadow-xl">
                        <div class="flex items-center justify-between px-3 py-1.5 bg-[#14141a] border-b border-white/5 text-[11px] text-neutral-400 font-mono select-none">
                            <div class="flex items-center space-x-2">
                                <span class="flex space-x-1">
                                    <span class="w-2.5 h-2.5 rounded-full bg-white/20 inline-block"></span>
                                    <span class="w-2.5 h-2.5 rounded-full bg-white/20 inline-block"></span>
                                    <span class="w-2.5 h-2.5 rounded-full bg-white/20 inline-block"></span>
                                </span>
                                <span class="font-semibold text-neutral-300 tracking-wider text-[10px] ml-1">${escapeHtml(displayLang)}</span>
                            </div>
                            <button type="button" onclick="copyCodeSnippet(this)" class="copy-code-btn tactile-btn flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] text-neutral-400 hover:text-white hover:bg-white/10 transition border border-transparent hover:border-white/10" title="Copier le code">
                                <i data-lucide="copy" class="w-3 h-3"></i>
                                <span>Copier</span>
                            </button>
                        </div>
                        <pre class="p-3 text-[12px] font-mono text-neutral-200 overflow-x-auto selection:bg-white/20 leading-relaxed custom-scrollbar"><code>${escaped}</code></pre>
                    </div>
                `;
                codeBlocks.push({ id: blockId, html: html });
                return blockId;
            });

            // 2. Escape HTML for remaining regular text
            processed = escapeHtml(processed);

            // 3. Inline code
            processed = processed.replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 rounded bg-white/10 text-neutral-200 font-mono text-[12px] border border-white/10">$1</code>');

            // 4. Headers
            processed = processed.replace(/^### (.*$)/gim, '<h3 class="text-sm font-bold text-white mt-3 mb-1.5 tracking-tight">$1</h3>');
            processed = processed.replace(/^## (.*$)/gim, '<h2 class="text-base font-bold text-white mt-4 mb-2 tracking-tight">$1</h2>');
            processed = processed.replace(/^# (.*$)/gim, '<h1 class="text-lg font-bold text-white mt-4 mb-2 tracking-tight">$1</h1>');

            // 5. Blockquotes
            processed = processed.replace(/^>\\s?(.*$)/gim, '<blockquote class="border-l-2 border-white/30 pl-3 my-2 text-neutral-300 italic text-[13px]">$1</blockquote>');

            // 6. Bold & Italic
            processed = processed.replace(/\\*\\*\\*(.*?)\\*\\*\\*/g, '<strong class="font-semibold text-white"><em class="italic">$1</em></strong>');
            processed = processed.replace(/\\*\\*(.*?)\\*\\*/g, '<strong class="font-semibold text-white">$1</strong>');
            processed = processed.replace(/\\*([^\\*]+)\\*/g, '<em class="italic text-neutral-200">$1</em>');

            // 7. Ordered and Unordered Lists
            processed = processed.replace(/^(\\d+)\\.\\s+(.*$)/gim, '<li class="ml-4 list-decimal text-neutral-200 my-0.5 text-[13px]" value="$1">$2</li>');
            processed = processed.replace(/^[\\*\\-]\\s+(.*$)/gim, '<li class="ml-4 list-disc text-neutral-200 my-0.5 text-[13px]">$1</li>');

            // 8. Secure hyperlinks
            processed = processed.replace(/\\[([^\\]]+)\\]\\((https?:\\/\\/[^\\)]+)\\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-neutral-300 underline underline-offset-2 hover:text-white transition">$1</a>');

            // 9. Line breaks
            processed = processed.replace(/\\n\\n/g, '<br><br>');
            processed = processed.replace(/\\n/g, '<br>');

            // 10. Restore code blocks
            codeBlocks.forEach(b => {
                processed = processed.replace(b.id, b.html);
            });

            return processed;
        }

        // Copy Code Snippet helper
        function copyCodeSnippet(button) {
            if (!button) return;
            const container = button.closest('.code-block-container');
            if (!container) return;
            const codeEl = container.querySelector('pre code');
            if (!codeEl) return;
            const textToCopy = codeEl.innerText || codeEl.textContent;

            const handleSuccess = () => {
                const orig = button.innerHTML;
                button.innerHTML = '<i data-lucide="check" class="w-3 h-3 text-white"></i><span class="text-white">Copié !</span>';
                if (window.lucide && lucide.createIcons) {
                    lucide.createIcons({ root: button });
                }
                setTimeout(() => {
                    button.innerHTML = orig;
                    if (window.lucide && lucide.createIcons) {
                        lucide.createIcons({ root: button });
                    }
                }, 2000);
            };

            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(textToCopy).then(handleSuccess).catch(() => {
                    fallbackCopy(textToCopy, handleSuccess);
                });
            } else {
                fallbackCopy(textToCopy, handleSuccess);
            }
        }

        function fallbackCopy(text, cb) {
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.select();
            try {
                document.execCommand('copy');
                if (cb) cb();
            } catch (e) {
                console.error('Fallback copy failed', e);
            }
            document.body.removeChild(ta);
        }"""

content = content[:format_md_match.start()] + new_format_md + content[format_md_match.end():]
print("[OK] Replaced formatMarkdown with upgraded code syntax rendering & copyCodeSnippet")

# Also ensure lucide.createIcons is called after assistant message append
if "appendAssistantMessage(reply, cards, thoughts, level) {" in content and "setTimeout(() => { if (window.lucide && lucide.createIcons) lucide.createIcons(); }, 50);" not in content:
    content = content.replace(
        "appendAssistantMessage(reply, cards, thoughts, level) {",
        "appendAssistantMessage(reply, cards, thoughts, level) {\n            setTimeout(() => { if (window.lucide && lucide.createIcons) lucide.createIcons(); }, 50);"
    )
    print("[OK] Hooked lucide.createIcons into appendAssistantMessage")

index_path.write_text(content, encoding="utf-8")
print(f"Successfully updated index.html! New length: {len(content)} chars, {len(content.splitlines())} lines")
