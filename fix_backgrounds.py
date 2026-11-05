import re

FILE_PATH = r"services\core-engine\src\api\static\index.html"

with open(FILE_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Fix setChatBackground and define updateChatBgSettingsUI
old_set_bg = """        function setChatBackground(bgId, customUrl = '') {
            currentChatBackground = bgId;
            if (bgId === 'custom' && customUrl) {
                currentCustomBgUrl = customUrl;
                localStorage.setItem('hol_chat_background_custom', customUrl);
            }
            localStorage.setItem('hol_chat_background', bgId);
            applySavedChatBackground();
            updateChatBgSettingsUI();
        }"""

new_set_bg = """        function updateChatBgSettingsUI() {
            if (typeof updateHeroCarouselUI === 'function') {
                try { updateHeroCarouselUI(); } catch (e) { console.warn('updateHeroCarouselUI error:', e); }
            }
            const activeBg = window.currentChatBackground || localStorage.getItem('hol_chat_background') || 'default';
            const badge = document.getElementById('active-bg-badge');
            if (badge && typeof HERO_CAROUSEL_ITEMS !== 'undefined') {
                const item = HERO_CAROUSEL_ITEMS.find(it => it.id === activeBg);
                badge.innerText = item ? item.title.split(' ')[0] : (activeBg === 'custom' ? 'Image' : 'Défaut');
            }
        }

        function setChatBackground(bgId, customUrl = '') {
            currentChatBackground = bgId;
            window.currentChatBackground = bgId;
            if (bgId === 'custom') {
                if (customUrl) {
                    currentCustomBgUrl = customUrl;
                    window.currentCustomBgUrl = customUrl;
                    localStorage.setItem('hol_chat_background_custom', customUrl);
                } else if (!currentCustomBgUrl) {
                    currentCustomBgUrl = localStorage.getItem('hol_chat_background_custom') || '';
                    window.currentCustomBgUrl = currentCustomBgUrl;
                }
            }
            localStorage.setItem('hol_chat_background', bgId);
            applySavedChatBackground();
            updateChatBgSettingsUI();
        }

        window.setChatBackground = setChatBackground;
        window.updateChatBgSettingsUI = updateChatBgSettingsUI;
        window.applySavedChatBackground = applySavedChatBackground;"""

assert old_set_bg in content, "old_set_bg not found!"
content = content.replace(old_set_bg, new_set_bg)
print("1. Patched setChatBackground & defined updateChatBgSettingsUI")

# 2. Fix applyAndClosePanoramic
old_apply_pano = """        function applyAndClosePanoramic() {
            closeHeroCarouselPanoramic();
            // Show toast or confirmation
            const status = document.getElementById('hero-carousel-status');
            if (status) {
                status.innerText = 'Appliqué';
                status.className = 'text-[9px] font-mono px-1.5 py-0.5 rounded-md bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
                setTimeout(() => {
                    status.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span><span>Actif ✓</span>';
                }, 2000);
            }
        }"""

new_apply_pano = """        function applyAndClosePanoramic() {
            if (typeof HERO_CAROUSEL_ITEMS !== 'undefined' && HERO_CAROUSEL_ITEMS[heroCarouselCurrentIndex]) {
                setChatBackground(HERO_CAROUSEL_ITEMS[heroCarouselCurrentIndex].id);
            }
            closeHeroCarouselPanoramic();
            const status = document.getElementById('hero-carousel-status');
            if (status) {
                status.innerText = 'Appliqué ✓';
                status.className = 'text-[9px] font-mono px-1.5 py-0.5 rounded-md bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
                setTimeout(() => {
                    status.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span><span>Actif ✓</span>';
                }, 2000);
            }
        }"""

if old_apply_pano in content:
    content = content.replace(old_apply_pano, new_apply_pano)
    print("2. Patched applyAndClosePanoramic")
else:
    # Handle possible encoding in 'Appliqué'
    m = re.search(r'function applyAndClosePanoramic\(\) \{[\s\S]*?status\.innerHTML[\s\S]*?\}', content)
    if m:
        content = content[:m.start()] + new_apply_pano + content[m.end():]
        print("2. Patched applyAndClosePanoramic via regex")

# 3. Fix applyCurrentTheme to re-apply background for light/dark
old_apply_theme = """            } else {
                html.classList.add('dark');
                if (iconTop) iconTop.innerHTML = '<i data-lucide="moon" class="w-4 h-4 text-neutral-200"></i>';
                if (btnDark) { btnDark.classList.add('bg-white', 'text-black', 'border-white'); }
                if (btnLight) { btnLight.classList.remove('bg-white', 'text-black', 'border-white'); }
            }
            lucideSafeRender();"""

new_apply_theme = """            } else {
                html.classList.add('dark');
                if (iconTop) iconTop.innerHTML = '<i data-lucide="moon" class="w-4 h-4 text-neutral-200"></i>';
                if (btnDark) { btnDark.classList.add('bg-white', 'text-black', 'border-white'); }
                if (btnLight) { btnLight.classList.remove('bg-white', 'text-black', 'border-white'); }
            }
            if (typeof applySavedChatBackground === 'function') {
                applySavedChatBackground();
            }
            lucideSafeRender();"""

assert old_apply_theme in content, "old_apply_theme not found!"
content = content.replace(old_apply_theme, new_apply_theme)
print("3. Patched applyCurrentTheme with applySavedChatBackground")

# 4. Fix DOMContentLoaded to applySavedChatBackground on load
old_dom_loaded = """        window.addEventListener('DOMContentLoaded', () => {
            lucideSafeRender();
            if (typeof updateThinkingModeUI === 'function') {
                updateThinkingModeUI(currentThinkingLevel);
            }
        });"""

new_dom_loaded = """        window.addEventListener('DOMContentLoaded', () => {
            lucideSafeRender();
            if (typeof applySavedChatBackground === 'function') {
                applySavedChatBackground();
            }
            if (typeof updateThinkingModeUI === 'function') {
                updateThinkingModeUI(currentThinkingLevel);
            }
            if (typeof updateHeroCarouselUI === 'function') {
                updateHeroCarouselUI();
            }
        });"""

assert old_dom_loaded in content, "old_dom_loaded not found!"
content = content.replace(old_dom_loaded, new_dom_loaded)
print("4. Patched DOMContentLoaded with applySavedChatBackground")

# 5. Fix "Cliquer pour activer" button in carousel
old_click_to_activate = '<span class="text-sky-400 font-semibold">Cliquer pour activer</span>'
new_click_to_activate = '<button type="button" onclick="selectHeroCarouselSlide(heroCarouselCurrentIndex)" class="text-sky-400 hover:text-sky-300 font-semibold cursor-pointer underline transition">Cliquer pour activer</button>'
if old_click_to_activate in content:
    content = content.replace(old_click_to_activate, new_click_to_activate)
    print("5. Patched 'Cliquer pour activer' into interactive button")

# 6. Populate custom-bg-input in openSettingsModal
old_open_settings = """        function openSettingsModal() {

            document.getElementById('settings-modal').classList.remove('hidden');
            if (typeof initHeroCarousel === "function") initHeroCarousel();
            if (typeof fetchConnectorsStatus === "function") fetchConnectorsStatus();

            setChatStyle(currentStyle);

            applyCurrentTheme();
        updateThinkingModeUI(currentThinkingLevel);

        }"""

new_open_settings = """        function openSettingsModal() {

            document.getElementById('settings-modal').classList.remove('hidden');
            if (typeof initHeroCarousel === "function") initHeroCarousel();
            if (typeof fetchConnectorsStatus === "function") fetchConnectorsStatus();

            setChatStyle(currentStyle);

            applyCurrentTheme();
            updateThinkingModeUI(currentThinkingLevel);

            const customInput = document.getElementById('custom-bg-input');
            if (customInput && currentCustomBgUrl) {
                customInput.value = currentCustomBgUrl;
            }
        }"""

assert old_open_settings in content, "old_open_settings not found!"
content = content.replace(old_open_settings, new_open_settings)
print("6. Patched openSettingsModal to prefill custom background URL")

with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("ALL BACKGROUND PATCHES APPLIED TO index.html!")
