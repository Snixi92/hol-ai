path = r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Remove liquid-glass-subtle from bubble-assistant
content = content.replace("bubble-assistant liquid-glass-subtle", "bubble-assistant")

# 2. Update the welcome suggestion buttons to suggestion-chip
old_suggestions = """                    <!-- Suggestions de lancement rapide en 1 clic -->
                    <div class="flex flex-wrap gap-2 pt-1">
                        <button onclick="sendInteractiveAnswer('Fais-moi le briefing complet de ma journée')" class="tactile-btn px-3.5 py-2 rounded-2xl liquid-glass-subtle hover:bg-white/15 text-neutral-800 dark:text-neutral-200 text-xs font-medium transition cursor-pointer flex items-center space-x-2 shadow-sm">
                            <i data-lucide="zap" class="w-3.5 h-3.5 text-amber-400"></i>
                            <span>Briefing du jour</span>
                        </button>
                        <button onclick="sendInteractiveAnswer('trouve moi un iphone xr le moins cher sur tout internet')" class="tactile-btn px-3.5 py-2 rounded-2xl liquid-glass-subtle hover:bg-white/15 text-neutral-800 dark:text-neutral-200 text-xs font-medium transition cursor-pointer flex items-center space-x-2 shadow-sm">
                            <i data-lucide="smartphone" class="w-3.5 h-3.5 text-neutral-300"></i>
                            <span>iPhone XR le moins cher</span>
                        </button>
                        <button onclick="sendInteractiveAnswer('trouve moi une crème visage hydratante')" class="tactile-btn px-3.5 py-2 rounded-2xl liquid-glass-subtle hover:bg-white/15 text-neutral-800 dark:text-neutral-200 text-xs font-medium transition cursor-pointer flex items-center space-x-2 shadow-sm">
                            <i data-lucide="sparkles" class="w-3.5 h-3.5 text-neutral-300"></i>
                            <span>Cosmétiques & Soins</span>
                        </button>
                        <button onclick="sendInteractiveAnswer('où en sont mes colis et livraisons ?')" class="tactile-btn px-3.5 py-2 rounded-2xl liquid-glass-subtle hover:bg-white/15 text-neutral-800 dark:text-neutral-200 text-xs font-medium transition cursor-pointer flex items-center space-x-2 shadow-sm">
                            <i data-lucide="package" class="w-3.5 h-3.5 text-neutral-300"></i>
                            <span>Suivi de mes colis</span>
                        </button>
                    </div>"""

new_suggestions = """                    <!-- Suggestions de lancement rapide en 1 clic -->
                    <div class="flex flex-wrap gap-2 pt-1">
                        <button onclick="sendInteractiveAnswer('Fais-moi le briefing complet de ma journée')" class="tactile-btn px-3.5 py-2 rounded-2xl suggestion-chip text-xs font-medium transition cursor-pointer flex items-center space-x-2">
                            <i data-lucide="zap" class="w-3.5 h-3.5 text-amber-400"></i>
                            <span>Briefing du jour</span>
                        </button>
                        <button onclick="sendInteractiveAnswer('trouve moi un iphone xr le moins cher sur tout internet')" class="tactile-btn px-3.5 py-2 rounded-2xl suggestion-chip text-xs font-medium transition cursor-pointer flex items-center space-x-2">
                            <i data-lucide="smartphone" class="w-3.5 h-3.5 text-neutral-300"></i>
                            <span>iPhone XR le moins cher</span>
                        </button>
                        <button onclick="sendInteractiveAnswer('trouve moi une crème visage hydratante')" class="tactile-btn px-3.5 py-2 rounded-2xl suggestion-chip text-xs font-medium transition cursor-pointer flex items-center space-x-2">
                            <i data-lucide="sparkles" class="w-3.5 h-3.5 text-neutral-300"></i>
                            <span>Cosmétiques & Soins</span>
                        </button>
                        <button onclick="sendInteractiveAnswer('où en sont mes colis et livraisons ?')" class="tactile-btn px-3.5 py-2 rounded-2xl suggestion-chip text-xs font-medium transition cursor-pointer flex items-center space-x-2">
                            <i data-lucide="package" class="w-3.5 h-3.5 text-neutral-300"></i>
                            <span>Suivi de mes colis</span>
                        </button>
                    </div>"""

if old_suggestions in content:
    content = content.replace(old_suggestions, new_suggestions)
    print("Welcome suggestion buttons updated to suggestion-chip!")
else:
    print("Old suggestions block not found directly, checking variations...")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied!")
