import asyncio
import os
from playwright.async_api import async_playwright

ARTIFACT_DIR = r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494"

async def test_backgrounds():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        failed_requests = []
        page.on("requestfailed", lambda req: failed_requests.append(f"{req.url} failed: {req.failure}"))
        
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        await page.wait_for_timeout(500)
        
        # Check initial state
        initial_bg = await page.evaluate("""() => {
            const layer = document.getElementById('conversation-bg-layer');
            return {
                currentChatBackground: window.currentChatBackground,
                localStorage: localStorage.getItem('hol_chat_background'),
                layerClasses: layer ? layer.className : null,
                layerStyle: layer ? layer.style.cssText : null,
                children: layer ? layer.children.length : 0
            };
        }""")
        print("Initial state:", initial_bg)
        
        # Test 1: Select a CSS preset background (e.g. 'aurora')
        print("\n--- Testing setChatBackground('aurora') ---")
        await page.evaluate("setChatBackground('aurora')")
        await page.wait_for_timeout(500)
        
        aurora_state = await page.evaluate("""() => {
            const layer = document.getElementById('conversation-bg-layer');
            return {
                currentChatBackground: window.currentChatBackground,
                layerClasses: layer ? layer.className : null,
                computedBg: layer ? window.getComputedStyle(layer).backgroundImage : null,
                computedBgColor: layer ? window.getComputedStyle(layer).backgroundColor : null
            };
        }""")
        print("Aurora state:", aurora_state)
        await page.screenshot(path=os.path.join(ARTIFACT_DIR, "debug_bg_aurora.png"))
        
        # Test 2: Select a shader background (e.g. '21st-globe')
        print("\n--- Testing setChatBackground('21st-globe') ---")
        await page.evaluate("setChatBackground('21st-globe')")
        await page.wait_for_timeout(1000)
        
        globe_state = await page.evaluate("""() => {
            const layer = document.getElementById('conversation-bg-layer');
            const frame = document.getElementById('chat-bg-canvas-frame');
            return {
                currentChatBackground: window.currentChatBackground,
                frameFound: !!frame,
                frameSrc: frame ? frame.src : null,
                layerClasses: layer ? layer.className : null
            };
        }""")
        print("Globe shader state:", globe_state)
        await page.screenshot(path=os.path.join(ARTIFACT_DIR, "debug_bg_globe.png"))
        
        # Test 3: Select another shader (e.g. '21st-fluid-canvas')
        print("\n--- Testing setChatBackground('21st-fluid-canvas') ---")
        await page.evaluate("setChatBackground('21st-fluid-canvas')")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=os.path.join(ARTIFACT_DIR, "debug_bg_fluid.png"))
        
        # Test 4: Open Settings Modal and click Carousel
        print("\n--- Testing Carousel in Settings Modal ---")
        await page.evaluate("openSettingsModal()")
        await page.wait_for_timeout(500)
        
        # Click Next button on carousel
        carousel_info = await page.evaluate("""() => {
            const title = document.getElementById('hero-carousel-title');
            const nextBtn = document.querySelector('[onclick*=\"heroCarouselNext\"]');
            return {
                title: title ? title.innerText : null,
                hasNextBtn: !!nextBtn
            };
        }""")
        print("Carousel initial in modal:", carousel_info)
        
        # Click next in carousel
        await page.evaluate("heroCarouselNext()")
        await page.wait_for_timeout(500)
        
        carousel_after_next = await page.evaluate("""() => {
            const title = document.getElementById('hero-carousel-title');
            return {
                title: title ? title.innerText : null,
                currentIdx: window.heroCarouselCurrentIndex,
                currentBg: window.currentChatBackground
            };
        }""")
        print("Carousel after next:", carousel_after_next)
        
        # Check clicking thumbnail or active slide in carousel
        thumbnails_count = await page.evaluate("""() => {
            return document.querySelectorAll('#hero-carousel-thumbnails > div').length;
        }""")
        print("Thumbnails count in carousel:", thumbnails_count)
        
        print("\nConsole errors:", errors)
        print("Failed network requests:", failed_requests)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_backgrounds())
