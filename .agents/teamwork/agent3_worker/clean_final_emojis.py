from pathlib import Path

index_path = Path(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html")
content = index_path.read_text(encoding="utf-8")

content = content.replace("status.innerText = 'Appliqué ✓';", "status.innerText = 'Appliqué';")
content = content.replace("status.innerHTML = '<span class=\"w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse\"></span><span>Actif ✓</span>';", "status.innerHTML = '<span class=\"w-1.5 h-1.5 rounded-full bg-white/80 animate-pulse\"></span><span>Actif</span>';")
content = content.replace("badge.innerText = c.is_native ? '✓ Actif Natif' : 'Connecté ✓';", "badge.innerText = c.is_native ? 'Actif Natif' : 'Connecté';")
content = content.replace("drawerFb.innerText = `✓ ${data.message || \"Enregistré avec succès dans .env\"}`;", "drawerFb.innerText = data.message || \"Enregistré avec succès dans .env\";")

content = content.replace("⚡ Annonces spécifiques", '<i data-lucide="sparkles" class="w-3 h-3 inline mr-1 text-neutral-400"></i>Annonces spécifiques')
content = content.replace("text-amber-500 font-mono\">⚡ ${escapeHtml", 'text-neutral-300 font-mono\">${escapeHtml')
content = content.replace("<span>🌐</span>", '<span><i data-lucide="globe" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace("<span>⚡</span>", '<span><i data-lucide="zap" class="w-3.5 h-3.5 inline text-neutral-400"></i></span>')
content = content.replace('<span class="absolute text-xl">🌐</span>', '<i data-lucide="globe" class="w-6 h-6 text-neutral-400 absolute"></i>')
content = content.replace("console.log(\"👏 DOUBLE-CLAP DÉTECTÉ AVEC SUCCÈS !\");", "console.log(\"DOUBLE-CLAP DÉTECTÉ AVEC SUCCÈS !\");")
content = content.replace("🛑 Stop", '<i data-lucide="square" class="w-3.5 h-3.5 inline mr-1"></i>Stop')
content = content.replace("cuStatusDot.innerText = \"✕ Erreur flux\";", "cuStatusDot.innerText = \"Erreur flux\";")
content = content.replace("cuModeBadge.innerText = \"🎮 CONTRÔLE HUMAIN (TAKE OVER)\";", "cuModeBadge.innerText = \"CONTRÔLE HUMAIN (TAKE OVER)\";")

index_path.write_text(content, encoding="utf-8")
print("[OK] Finished cleaning remaining emojis!")
