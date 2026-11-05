import re

index_path = r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html"
with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. PWA Meta Tags in <head>
pwa_meta = """    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="HoL AI">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="format-detection" content="telephone=no">
    <meta name="theme-color" content="#08080a">"""

old_pwa_regex = re.compile(
    r'<meta name="apple-mobile-web-app-capable" content="yes">\s*<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">\s*<meta name="theme-color" content="#08080a">',
    re.DOTALL
)
if old_pwa_regex.search(html):
    html = old_pwa_regex.sub(pwa_meta, html, count=1)
    print("1. Upgraded PWA meta tags")

# 2. Safe-area insets & mobile CSS
old_safe_area = """        /* Mobile Safe-Area Insets for iOS 27 */
        header, #header-messaging, #header-perplexity, #header-chatgpt {
            padding-top: max(0.5rem, env(safe-area-inset-top, 0px)) !important;
        }
        .ios-dock-container {
            bottom: calc(0.75rem + env(safe-area-inset-bottom, 0px)) !important;
            padding-bottom: env(safe-area-inset-bottom, 0px);
        }
        .ios-chat-scroll {
            padding-bottom: calc(11.5rem + env(safe-area-inset-bottom, 0px)) !important;
        }"""

new_safe_area = """        /* Mobile Safe-Area Insets & Native Mobile Feel (iOS 27 / Android) */
        header, #header-messaging, #header-perplexity, #header-chatgpt {
            min-height: calc(3.85rem + env(safe-area-inset-top, 0px)) !important;
            height: auto !important;
            padding-top: max(0.65rem, env(safe-area-inset-top, 0px)) !important;
            padding-bottom: 0.5rem !important;
        }
        .ios-dock-container {
            bottom: calc(0.6rem + env(safe-area-inset-bottom, 0px)) !important;
            padding-bottom: max(0.2rem, env(safe-area-inset-bottom, 0px)) !important;
        }
        .ios-chat-scroll {
            padding-bottom: calc(12.5rem + env(safe-area-inset-bottom, 0px)) !important;
            mask-image: linear-gradient(to bottom, transparent 0%, black 20px, black calc(100% - 36px), transparent 100%);
            -webkit-mask-image: linear-gradient(to bottom, transparent 0%, black 20px, black calc(100% - 36px), transparent 100%);
            -webkit-overflow-scrolling: touch;
            overscroll-behavior-y: contain;
        }

        /* Prevent 300ms tap delay & remove grey tap flash */
        *, *::before, *::after {
            -webkit-tap-highlight-color: transparent !important;
        }
        button, a, input, select, textarea, .tactile-btn, .nimbus-item {
            touch-action: manipulation;
        }

        /* Prevent iOS Safari 15%-20% auto-zoom upon focusing inputs */
        @media (max-width: 640px) {
            #user-input, input[type="text"], input[type="password"], textarea {
                font-size: 16px !important;
            }
        }"""

if old_safe_area in html:
    html = html.replace(old_safe_area, new_safe_area)
    print("2. Upgraded Safe-Area & Mobile CSS")
else:
    print("WARNING: old_safe_area not found")

# 3. Mode Sheet Mobile iOS 27
old_sheet_css = """        /* Mode Sheet Mobile iOS 27 */
        @media (max-width: 640px) {
            .ios-sheet-modal {
                border-bottom-left-radius: 0 !important;
                border-bottom-right-radius: 0 !important;
                border-top-left-radius: 32px !important;
                border-top-right-radius: 32px !important;
                max-height: 90vh;
                margin-top: auto;
            }
        }"""

new_sheet_css = """        /* Mode Sheet Mobile iOS 27 */
        @media (max-width: 640px) {
            .ios-sheet-modal {
                border-bottom-left-radius: 0 !important;
                border-bottom-right-radius: 0 !important;
                border-top-left-radius: 32px !important;
                border-top-right-radius: 32px !important;
                max-height: 88vh;
                margin-top: auto;
                width: 100% !important;
                max-width: 100% !important;
                padding-bottom: max(2rem, env(safe-area-inset-bottom, 0px)) !important;
                overscroll-behavior: contain;
            }
        }"""

if old_sheet_css in html:
    html = html.replace(old_sheet_css, new_sheet_css)
    print("3. Upgraded .ios-sheet-modal CSS")
else:
    print("WARNING: old_sheet_css not found")

# 4. Modal container classes to items-end on mobile
pairs_modal = [
    (
        '<div id="settings-modal" class="fixed inset-0 bg-black/75 z-50 hidden flex items-center justify-center p-4 backdrop-blur-sm" onclick="if(event.target === this) closeSettingsModal()">',
        '<div id="settings-modal" class="fixed inset-0 bg-black/75 z-50 hidden flex items-end sm:items-center justify-center p-0 sm:p-4 backdrop-blur-sm" onclick="if(event.target === this) closeSettingsModal()">'
    ),
    (
        '<div id="background-modal" class="fixed inset-0 bg-black/75 z-50 hidden flex items-center justify-center p-4 backdrop-blur-sm" onclick="if(event.target === this) closeBackgroundModal()">',
        '<div id="background-modal" class="fixed inset-0 bg-black/75 z-50 hidden flex items-end sm:items-center justify-center p-0 sm:p-4 backdrop-blur-sm" onclick="if(event.target === this) closeBackgroundModal()">'
    ),
    (
        '<div id="phone-connect-modal" class="fixed inset-0 z-50 bg-black/75 backdrop-blur-xl hidden items-center justify-center p-4 transition-all duration-300" onclick="if(event.target === this) togglePhoneConnectModal()">',
        '<div id="phone-connect-modal" class="fixed inset-0 z-50 bg-black/75 backdrop-blur-xl hidden flex items-end sm:items-center justify-center p-0 sm:p-4 transition-all duration-300" onclick="if(event.target === this) togglePhoneConnectModal()">'
    ),
    (
        '<div id="computer-use-modal" class="fixed inset-0 z-50 hidden bg-black/80 backdrop-blur-md flex items-center justify-center p-2 sm:p-4 animate-in fade-in duration-200" onclick="if(event.target === this) closeComputerUseModal()">',
        '<div id="computer-use-modal" class="fixed inset-0 z-50 hidden bg-black/80 backdrop-blur-md flex items-end sm:items-center justify-center p-0 sm:p-4 animate-in fade-in duration-200" onclick="if(event.target === this) closeComputerUseModal()">'
    )
]

for orig, repl in pairs_modal:
    if orig in html:
        html = html.replace(orig, repl)
        print(f"4. Patched modal container: {orig[:30]}...")
    else:
        print(f"WARNING: modal container not found: {orig[:30]}...")

# 5. Sidebar width & safe-area padding
old_sidebar = '<aside id="sidebar" class="hidden fixed lg:static inset-y-0 left-0 w-64 liquid-glass border-r border-white/10 flex flex-col z-40 transform -translate-x-full lg:translate-x-0 transition-transform duration-200 ease-out">'
new_sidebar = '<aside id="sidebar" class="hidden fixed lg:static inset-y-0 left-0 w-[84vw] max-w-xs sm:w-72 lg:w-72 liquid-glass border-r border-white/10 flex flex-col z-40 transform -translate-x-full lg:translate-x-0 transition-transform duration-200 ease-out pt-[max(0.75rem,env(safe-area-inset-top,0px))] pb-[max(1rem,env(safe-area-inset-bottom,0px))]">'

if old_sidebar in html:
    html = html.replace(old_sidebar, new_sidebar)
    print("5. Upgraded sidebar width & safe-area")
else:
    print("WARNING: old_sidebar not found")

# 6. Spaces navbar mobile centering
old_spaces = """        <div class="h-12 px-3 sm:px-4 liquid-glass border-b border-white/10 flex items-center justify-between text-xs overflow-visible z-10 flex-shrink-0">
            <div class="flex items-center min-w-0">"""

new_spaces = """        <div class="h-12 px-3 sm:px-4 liquid-glass border-b border-white/10 flex items-center justify-center sm:justify-start text-xs overflow-visible z-10 flex-shrink-0">
            <div class="flex items-center justify-center w-full sm:w-auto min-w-0">"""

if old_spaces in html:
    html = html.replace(old_spaces, new_spaces)
    print("6. Centered spaces navbar on mobile")
else:
    print("WARNING: old_spaces not found")

# 7. Add touchstart and touchmove for Fresnel glint
old_mouse = """        document.addEventListener('mousemove', (e) => {
            updateGlassCoords(e.clientX, e.clientY);
        }, { passive: true });"""

new_touch = """        document.addEventListener('mousemove', (e) => {
            updateGlassCoords(e.clientX, e.clientY);
        }, { passive: true });
        document.addEventListener('touchmove', (e) => {
            if (e.touches && e.touches[0]) {
                updateGlassCoords(e.touches[0].clientX, e.touches[0].clientY);
            }
        }, { passive: true });
        document.addEventListener('touchstart', (e) => {
            if (e.touches && e.touches[0]) {
                updateGlassCoords(e.touches[0].clientX, e.touches[0].clientY);
            }
        }, { passive: true });"""

if old_mouse in html:
    html = html.replace(old_mouse, new_touch)
    print("7. Injected touch Fresnel listeners")
else:
    print("WARNING: old_mouse not found")

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html)
print("Saved optimized index.html")
