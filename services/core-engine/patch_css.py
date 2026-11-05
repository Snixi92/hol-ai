import re

path = r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Target block starts at "/* Thème Sombre : Obsidian OLED profond */" and ends before "/* Animations à Ressort (Apple Spring Physics) */"
start_str = "/* Thème Sombre : Obsidian OLED profond */"
end_str = "/* Animations à Ressort (Apple Spring Physics) */"

if start_str not in content or end_str not in content:
    print(f"Error: Markers not found! start in content: {start_str in content}, end in content: {end_str in content}")
    exit(1)

start_idx = content.find(start_str)
end_idx = content.find(end_str)

new_block = """/* Thème Sombre : Obsidian OLED profond avec lumière ambiante Apple */
        html.dark body {
            background-color: #08080a;
            color: #f4f4f6;
            background-image: 
                radial-gradient(at 15% 20%, rgba(255, 255, 255, 0.08) 0px, transparent 45%),
                radial-gradient(at 85% 75%, rgba(160, 180, 210, 0.05) 0px, transparent 50%),
                radial-gradient(at 50% 50%, rgba(255, 255, 255, 0.02) 0px, transparent 65%);
        }

        /* Thème Clair : Frosted Pure Slate avec brillance ambiante */
        html:not(.dark) body {
            background-color: #f5f5f7;
            color: #09090b;
            background-image: 
                radial-gradient(at 20% 20%, rgba(0, 0, 0, 0.035) 0px, transparent 60%),
                radial-gradient(at 80% 80%, rgba(0, 0, 0, 0.025) 0px, transparent 60%);
        }

        /* --- MOTEUR LIQUID GLASS APPLE iOS 27 (MASTER SPEC "REGULAR GLASS") --- */

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
        }

        /* Apple HIG Calque de Contenu Standard : lisibilité absolue sans verre parasite */
        .bubble-assistant {
            background: #111115 !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35) !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
        }

        html:not(.dark) .bubble-assistant {
            background: #ffffff !important;
            border: 1px solid rgba(0, 0, 0, 0.08) !important;
            box-shadow: 0 4px 18px rgba(15, 23, 42, 0.06) !important;
        }

        /* Boutons de suggestions rapides dans le calque de contenu */
        .suggestion-chip {
            background: #18181f;
            border: 1px solid rgba(255, 255, 255, 0.10);
            color: #e4e4e7;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
            transition: all 0.2s cubic-bezier(0.22, 1, 0.36, 1);
        }

        .suggestion-chip:hover {
            background: #24242e;
            border-color: rgba(255, 255, 255, 0.22);
            color: #ffffff;
            transform: translateY(-1px) scale(1.02);
        }

        html:not(.dark) .suggestion-chip {
            background: #f0f0f4;
            border: 1px solid rgba(0, 0, 0, 0.08);
            color: #18181b;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
        }

        html:not(.dark) .suggestion-chip:hover {
            background: #e4e4e9;
            border-color: rgba(0, 0, 0, 0.16);
        }

        /* Bulle Utilisateur : High-End Obsidian / Titanium */
        .bubble-user-glass {
            background: #1c1c22;
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.18);
            box-shadow: 
                inset 0 1px 1px 0 rgba(255, 255, 255, 0.32),
                0 8px 22px -4px rgba(0, 0, 0, 0.45);
        }

        html:not(.dark) .bubble-user-glass {
            background: #18181b;
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.25);
            box-shadow: 
                inset 0 1px 1.5px 0 rgba(255, 255, 255, 0.45),
                0 8px 20px -4px rgba(0, 0, 0, 0.18);
        }

        /* Avatar Apple Frosted Sphere */
        .apple-avatar {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.24), rgba(255, 255, 255, 0.08));
            border: 1px solid rgba(255, 255, 255, 0.30);
            box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.6), 0 4px 12px rgba(0, 0, 0, 0.30);
            color: #ffffff;
            font-weight: 700;
        }

        /* Apple HIG Scroll Edge Effect (Rule #6) */
        .ios-chat-scroll {
            mask-image: linear-gradient(to bottom, transparent 0%, black 20px, black calc(100% - 36px), transparent 100%);
            -webkit-mask-image: linear-gradient(to bottom, transparent 0%, black 20px, black calc(100% - 36px), transparent 100%);
        }

        /* Apple HIG Accessibilité (Rule #5) */
        @media (prefers-reduced-transparency: reduce) {
            .liquid-glass, .liquid-glass-regular, .liquid-glass-dock, .liquid-glass-subtle {
                backdrop-filter: none !important;
                -webkit-backdrop-filter: none !important;
                background: #121216 !important;
                border: 1px solid rgba(255, 255, 255, 0.25) !important;
            }
            html:not(.dark) .liquid-glass,
            html:not(.dark) .liquid-glass-regular,
            html:not(.dark) .liquid-glass-dock,
            html:not(.dark) .liquid-glass-subtle {
                background: #ffffff !important;
                border: 1px solid rgba(0, 0, 0, 0.15) !important;
            }
        }

        @media (prefers-contrast: more) {
            .liquid-glass, .liquid-glass-regular, .liquid-glass-dock {
                border: 2px solid rgba(255, 255, 255, 0.45) !important;
            }
            html:not(.dark) .liquid-glass,
            html:not(.dark) .liquid-glass-regular,
            html:not(.dark) .liquid-glass-dock {
                border: 2px solid rgba(0, 0, 0, 0.40) !important;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            .msg-animate, .tactile-btn, .liquid-glass, .liquid-glass-regular, .liquid-glass-dock {
                animation: none !important;
                transition: none !important;
            }
            .liquid-glass::before, .liquid-glass-regular::before, .liquid-glass-dock::before {
                display: none !important;
            }
        }

        """

content = content[:start_idx] + new_block + content[end_idx:]

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("CSS master patch applied successfully!")
