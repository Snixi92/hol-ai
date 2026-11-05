import asyncio
import os
from playwright.async_api import async_playwright

ARTIFACT_DIR = r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494"

async def verify_all():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        failed_requests = []
        page.on("requestfailed", lambda req: failed_requests.append(f"{req.url}: {req.failure}"))
        
        print("1. Loading page...")
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        await page.wait_for_timeout(800)
        
        # 2. Open Settings modal
        print("2. Opening Settings modal...")
        await page.evaluate("openSettingsModal()")
        await page.wait_for_timeout(600)
        
        # 3. Click next on carousel multiple times
        print("3. Clicking carousel Next buttons...")
        await page.evaluate("heroCarouselNext()")
        await page.wait_for_timeout(400)
        await page.evaluate("heroCarouselNext()")
        await page.wait_for_timeout(400)
        
        # 4. Click slide index 1 (Fluid Field shader)
        print("4. Clicking slide 1 (Fluid Field)...")
        await page.evaluate("selectHeroCarouselSlide(1)")
        await page.wait_for_timeout(800)
        
        state_shader = await page.evaluate("""() => {
            const frame = document.getElementById('chat-bg-canvas-frame');
            return {
                bg: window.currentChatBackground,
                hasFrame: !!frame,
                src: frame ? frame.src : null,
                localStorage: localStorage.getItem('hol_chat_background')
            };
        }""")
        print("  Shader state:", state_shader)
        assert state_shader['hasFrame'] == True
        assert state_shader['bg'] == '21st-fluid-field'
        assert state_shader['localStorage'] == '21st-fluid-field'
        
        # 5. Click preset slide (e.g. index 9: aurora)
        print("5. Clicking slide 9 (Aurora preset)...")
        await page.evaluate("selectHeroCarouselSlide(9)")
        await page.wait_for_timeout(600)
        
        state_aurora = await page.evaluate("""() => {
            const layer = document.getElementById('conversation-bg-layer');
            const frame = document.getElementById('chat-bg-canvas-frame');
            return {
                bg: window.currentChatBackground,
                className: layer.className,
                hasFrame: !!frame,
                localStorage: localStorage.getItem('hol_chat_background')
            };
        }""")
        print("  Aurora state:", state_aurora)
        assert state_aurora['bg'] == 'aurora'
        assert state_aurora['hasFrame'] == False
        assert 'bg-preset-aurora' in state_aurora['className']
        
        # 6. Test sample preset wallpaper click (Yosemite)
        print("6. Testing sample preset wallpaper...")
        await page.evaluate("applyPresetSampleBg('https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=1600&auto=format&fit=crop')")
        await page.wait_for_timeout(600)
        
        state_custom = await page.evaluate("""() => {
            const layer = document.getElementById('conversation-bg-layer');
            return {
                bg: window.currentChatBackground,
                styleBg: layer.style.backgroundImage,
                localStorage: localStorage.getItem('hol_chat_background'),
                localCustom: localStorage.getItem('hol_chat_background_custom')
            };
        }""")
        print("  Custom wallpaper state:", state_custom)
        assert state_custom['bg'] == 'custom'
        assert 'unsplash' in state_custom['styleBg']
        assert 'unsplash' in state_custom['localCustom']
        
        # 7. Test page RELOAD persistence!
        print("7. Testing page reload persistence...")
        await page.reload(wait_until="networkidle")
        await page.wait_for_timeout(800)
        
        state_reloaded = await page.evaluate("""() => {
            const layer = document.getElementById('conversation-bg-layer');
            return {
                bg: window.currentChatBackground,
                styleBg: layer.style.backgroundImage,
                localStorage: localStorage.getItem('hol_chat_background')
            };
        }""")
        print("  State after reload:", state_reloaded)
        assert state_reloaded['bg'] == 'custom'
        assert 'unsplash' in state_reloaded['styleBg']
        
        # 8. Switch to Globe shader and verify persistence across reload
        print("8. Switching to 21st-globe and checking reload persistence...")
        await page.evaluate("setChatBackground('21st-globe')")
        await page.wait_for_timeout(600)
        await page.reload(wait_until="networkidle")
        await page.wait_for_timeout(800)
        
        state_globe_reload = await page.evaluate("""() => {
            const frame = document.getElementById('chat-bg-canvas-frame');
            return {
                bg: window.currentChatBackground,
                hasFrame: !!frame,
                src: frame ? frame.src : null,
                localStorage: localStorage.getItem('hol_chat_background')
            };
        }""")
        print("  Globe state after reload:", state_globe_reload)
        assert state_globe_reload['hasFrame'] == True
        assert 'globe.html' in state_globe_reload['src']
        
        # 9. Test theme toggle synchronization
        print("9. Testing theme toggle...")
        await page.evaluate("toggleTheme()")
        await page.wait_for_timeout(500)
        theme_state = await page.evaluate("""() => {
            const html = document.documentElement;
            const frame = document.getElementById('chat-bg-canvas-frame');
            return {
                isDark: html.classList.contains('dark'),
                frameSrc: frame ? frame.src : null
            };
        }""")
        print("  Theme toggle state:", theme_state)
        # Revert theme back to dark
        await page.evaluate("toggleTheme()")
        await page.wait_for_timeout(400)
        
        # 10. Capture screenshot of Settings carousel with active slide
        await page.evaluate("openSettingsModal()")
        await page.wait_for_timeout(600)
        path_settings_bg = os.path.join(ARTIFACT_DIR, "background_fix_settings_carousel.png")
        await page.screenshot(path=path_settings_bg)
        print(f"Captured: {path_settings_bg}")
        
        await page.evaluate("closeSettingsModal()")
        await page.wait_for_timeout(400)
        path_chat_globe = os.path.join(ARTIFACT_DIR, "background_fix_chat_globe.png")
        await page.screenshot(path=path_chat_globe)
        print(f"Captured: {path_chat_globe}")

        # Check console errors
        print("\nPage errors encountered during full flow:", errors)
        assert len(errors) == 0, f"Errors occurred: {errors}"
        
        print("\n=== ALL BACKGROUND TESTS PASSED WITH 0 ERRORS ===")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_all())
