import os, sys, re

index_path = r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html"
with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

# Patch 1: Modal backdrop dismissals
p1_pairs = [
    (
        '<div id="settings-modal" class="fixed inset-0 bg-black/75 z-50 hidden flex items-center justify-center p-4 backdrop-blur-sm">',
        '<div id="settings-modal" class="fixed inset-0 bg-black/75 z-50 hidden flex items-center justify-center p-4 backdrop-blur-sm" onclick="if(event.target === this) closeSettingsModal()">'
    ),
    (
        '<div id="hero-carousel-panoramic-modal" class="fixed inset-0 bg-black/95 z-[70] hidden flex flex-col justify-between p-6 sm:p-10 backdrop-blur-2xl select-none text-white overflow-hidden" tabindex="0">',
        '<div id="hero-carousel-panoramic-modal" class="fixed inset-0 bg-black/95 z-[70] hidden flex flex-col justify-between p-6 sm:p-10 backdrop-blur-2xl select-none text-white overflow-hidden" tabindex="0" onclick="if(event.target === this) closeHeroCarouselPanoramic()">'
    ),
    (
        '<div id="background-modal" class="fixed inset-0 bg-black/75 z-50 hidden flex items-center justify-center p-4 backdrop-blur-sm">',
        '<div id="background-modal" class="fixed inset-0 bg-black/75 z-50 hidden flex items-center justify-center p-4 backdrop-blur-sm" onclick="if(event.target === this) closeBackgroundModal()">'
    ),
    (
        '<div id="computer-use-modal" class="fixed inset-0 z-50 hidden bg-black/80 backdrop-blur-md flex items-center justify-center p-2 sm:p-4 animate-in fade-in duration-200">',
        '<div id="computer-use-modal" class="fixed inset-0 z-50 hidden bg-black/80 backdrop-blur-md flex items-center justify-center p-2 sm:p-4 animate-in fade-in duration-200" onclick="if(event.target === this) closeComputerUseModal()">'
    )
]

for orig, repl in p1_pairs:
    if orig in html:
        html = html.replace(orig, repl)
        print(f"Patched backdrop: {orig[:30]}...")
    elif repl in html:
        print(f"Already patched: {orig[:30]}...")
    else:
        print(f"WARNING: Backdrop not found: {orig[:30]}...")

# Patch 2: setChatStyle header visibility toggle
old_style_target = "document.body.classList.remove('style-messaging', 'style-perplexity', 'style-chatgpt');\n\n            document.body.classList.add(`style-${styleName}`);"
new_style_code = """document.body.classList.remove('style-messaging', 'style-perplexity', 'style-chatgpt');
            document.body.classList.add(`style-${styleName}`);

            const headerMessaging = document.getElementById('header-messaging');
            const headerPerplexity = document.getElementById('header-perplexity');
            const headerChatgpt = document.getElementById('header-chatgpt');

            if (headerMessaging) headerMessaging.classList.toggle('hidden', styleName !== 'messaging');
            if (headerPerplexity) headerPerplexity.classList.toggle('hidden', styleName !== 'perplexity');
            if (headerChatgpt) headerChatgpt.classList.toggle('hidden', styleName !== 'chatgpt');"""

if old_style_target in html:
    html = html.replace(old_style_target, new_style_code)
    print("Patched setChatStyle header visibility")
elif "headerMessaging.classList.toggle('hidden'" in html:
    print("setChatStyle already patched")
else:
    # Try normalized whitespace
    import re
    match = re.search(r"document\.body\.classList\.remove\('style-messaging', 'style-perplexity', 'style-chatgpt'\);\s+document\.body\.classList\.add\(`style-\$\{styleName\}`\);", html)
    if match:
        html = html[:match.start()] + new_style_code + html[match.end():]
        print("Patched setChatStyle via regex")
    else:
        print("WARNING: setChatStyle not found")

# Patch 3: Global Escape keydown listener
old_escape_regex = re.compile(
    r"window\.addEventListener\('keydown',\s*function\(e\)\s*\{\s*if\s*\(e\.key === 'Escape' \|\| e\.key === 'Esc'\)\s*\{\s*const lb = document\.getElementById\('liquid-image-lightbox'\);\s*if \(lb && !lb\.classList\.contains\('hidden'\)\) \{\s*closeLiquidImageLightbox\(\);\s*\}\s*\}\s*\}\);",
    re.DOTALL
)

new_escape_code = """window.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' || e.key === 'Esc') {
                const settings = document.getElementById('settings-modal');
                if (settings && !settings.classList.contains('hidden')) {
                    if (typeof closeSettingsModal === 'function') closeSettingsModal();
                    else settings.classList.add('hidden');
                }
                const bgModal = document.getElementById('background-modal');
                if (bgModal && !bgModal.classList.contains('hidden')) {
                    if (typeof closeBackgroundModal === 'function') closeBackgroundModal();
                    else bgModal.classList.add('hidden');
                }
                const cuModal = document.getElementById('computer-use-modal');
                if (cuModal && !cuModal.classList.contains('hidden')) {
                    if (typeof closeComputerUseModal === 'function') closeComputerUseModal();
                    else cuModal.classList.add('hidden');
                }
                const phoneModal = document.getElementById('phone-connect-modal');
                if (phoneModal && !phoneModal.classList.contains('hidden')) {
                    if (typeof togglePhoneConnectModal === 'function') togglePhoneConnectModal();
                    else phoneModal.classList.add('hidden');
                }
                const panoModal = document.getElementById('hero-carousel-panoramic-modal');
                if (panoModal && !panoModal.classList.contains('hidden')) {
                    if (typeof closeHeroCarouselPanoramic === 'function') closeHeroCarouselPanoramic();
                    else panoModal.classList.add('hidden');
                }
                const jarvisHud = document.getElementById('jarvis-hud-overlay');
                if (jarvisHud && !jarvisHud.classList.contains('hidden')) {
                    if (typeof closeJarvisHud === 'function') closeJarvisHud();
                    else jarvisHud.classList.add('hidden');
                }
                const lb = document.getElementById('liquid-image-lightbox');
                if (lb && !lb.classList.contains('hidden')) {
                    if (typeof closeLiquidImageLightbox === 'function') closeLiquidImageLightbox();
                    else lb.classList.add('hidden');
                }
            }
        });"""

if old_escape_regex.search(html):
    html = old_escape_regex.sub(new_escape_code, html, count=1)
    print("Patched global Escape keydown listener")
elif "closeSettingsModal();" in html and "window.addEventListener('keydown'" in html:
    print("Escape keydown listener already patched")
else:
    print("WARNING: Escape keydown listener not found")

# Patch 4: switchMetaMuseSpace input element
old_spaces_code = re.compile(
    r"if \(spaceName === 'goals'\) \{\s*const msgInput = document\.getElementById\('chat-input'\) \|\| document\.querySelector\('input\[type=\"text\"\]'\);\s*if \(msgInput\) \{\s*msgInput\.value = \"Affiche mes objectifs en cours et mon avancement\";\s*if \(typeof sendMessage === 'function'\) sendMessage\(\);\s*\}\s*\} else if \(spaceName === 'ideas'\) \{\s*const msgInput = document\.getElementById\('chat-input'\) \|\| document\.querySelector\('input\[type=\"text\"\]'\);\s*if \(msgInput\) \{\s*msgInput\.value = \"Donne-moi 3 idées proactives pour optimiser mes dépenses et ma journée\";\s*if \(typeof sendMessage === 'function'\) sendMessage\(\);\s*\}\s*\} else if \(spaceName === 'artifacts'\) \{\s*const msgInput = document\.getElementById\('chat-input'\) \|\| document\.querySelector\('input\[type=\"text\"\]'\);\s*if \(msgInput\) \{\s*msgInput\.value = \"Montre-moi la liste des artefacts générés\";\s*if \(typeof sendMessage === 'function'\) sendMessage\(\);\s*\}\s*\}",
    re.DOTALL
)

new_spaces_code = """const msgInput = document.getElementById('user-input') || document.getElementById('chat-input');
            if (spaceName === 'goals') {
                if (msgInput) {
                    msgInput.value = "Affiche mes objectifs en cours et mon avancement";
                    if (typeof sendMessage === 'function') sendMessage();
                    else if (typeof handleChatSubmit === 'function') handleChatSubmit(null);
                }
            } else if (spaceName === 'ideas') {
                if (msgInput) {
                    msgInput.value = "Donne-moi 3 idées proactives pour optimiser mes dépenses et ma journée";
                    if (typeof sendMessage === 'function') sendMessage();
                    else if (typeof handleChatSubmit === 'function') handleChatSubmit(null);
                }
            } else if (spaceName === 'artifacts') {
                if (msgInput) {
                    msgInput.value = "Montre-moi la liste des artefacts générés";
                    if (typeof sendMessage === 'function') sendMessage();
                    else if (typeof handleChatSubmit === 'function') handleChatSubmit(null);
                }
            }"""

if old_spaces_code.search(html):
    html = old_spaces_code.sub(new_spaces_code, html, count=1)
    print("Patched switchMetaMuseSpace input target & dispatch")
elif "document.getElementById('user-input') || document.getElementById('chat-input')" in html:
    print("switchMetaMuseSpace already patched")
else:
    print("WARNING: switchMetaMuseSpace pattern not found")

# Patch 5: onLiquidNavAction, onSpacesNavAction and window aliases at bottom
old_bottom_handlers = re.compile(
    r"// Global click handlers\s*window\.onLiquidNavAction = function\(index, action\) \{\s*if \(window\.nimbusHeaderActions\) window\.nimbusHeaderActions\.selectIndex\(index, true\);\s*\};\s*window\.onSpacesNavAction = function\(index, space\) \{\s*if \(window\.nimbusSpacesNav\) window\.nimbusSpacesNav\.selectIndex\(index, true\);\s*\};",
    re.DOTALL
)

new_bottom_handlers = """// Global click handlers
            window.onLiquidNavAction = function(index, action) {
                if (window.nimbusHeaderActions) window.nimbusHeaderActions.selectIndex(index, true);
                if (action === 'computer-use' || action === 'computer') {
                    if (typeof openComputerUseModal === 'function') openComputerUseModal('https://www.google.fr');
                } else if (action === 'jarvis') {
                    if (typeof triggerJarvisMode === 'function') triggerJarvisMode();
                } else if (action === 'phone') {
                    if (typeof togglePhoneConnectModal === 'function') togglePhoneConnectModal();
                } else if (action === 'theme') {
                    if (typeof toggleTheme === 'function') toggleTheme();
                } else if (action === 'background') {
                    if (typeof openBackgroundModal === 'function') openBackgroundModal();
                } else if (action === 'settings') {
                    if (typeof openSettingsModal === 'function') openSettingsModal();
                }
            };

            window.onSpacesNavAction = function(index, space) {
                if (window.nimbusSpacesNav) window.nimbusSpacesNav.selectIndex(index, true);
                if (typeof switchMetaMuseSpace === 'function') switchMetaMuseSpace(space);
            };

            // Global aliases
            window.sendMessage = () => { if (typeof handleChatSubmit === 'function') return handleChatSubmit(null); };
            window.closeJarvisMode = () => { if (typeof closeJarvisHud === 'function') return closeJarvisHud(); };
            window.startNewConversation = () => { if (typeof startNewChat === 'function') return startNewChat(); };
            window.exportConversationMarkdown = (id) => { if (typeof exportConversationFile === 'function') return exportConversationFile(id, 'markdown'); };
            window.exportConversationJson = (id) => { if (typeof exportConversationFile === 'function') return exportConversationFile(id, 'json'); };
            window.deleteConversation = (id) => { if (typeof deleteConversationConfirm === 'function') return deleteConversationConfirm(id); };
            window.startRenameConversation = (id, title) => { if (typeof renameConversationPrompt === 'function') return renameConversationPrompt(id, title); };
            window.togglePin = (id, state) => { if (typeof togglePinConversation === 'function') return togglePinConversation(id, state); };"""

if old_bottom_handlers.search(html):
    html = old_bottom_handlers.sub(new_bottom_handlers, html, count=1)
    print("Patched bottom handlers & injected global aliases")
elif "window.closeJarvisMode =" in html:
    print("Bottom handlers already patched")
else:
    print("WARNING: Bottom handlers pattern not found")

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html)
print("Finished patching index.html")
