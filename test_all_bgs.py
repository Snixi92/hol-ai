import asyncio
import os
from playwright.async_api import async_playwright

ARTIFACT_DIR = r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494"

async def test_all_backgrounds():
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
        
        # Inject stub if missing to test what else breaks
        await page.evaluate("""() => {
            if (typeof updateChatBgSettingsUI === 'undefined') {
                window.updateChatBgSettingsUI = function() {
                    if (typeof updateHeroCarouselUI === 'function') updateHeroCarouselUI();
                };
            }
        }""")
        
        # 1. Test preset CSS backgrounds
        presets = ['aurora', 'cyber-grid', 'nebula', 'frosted', 'sunset', 'default']
        for preset in presets:
            print(f"Testing preset: {preset}")
            await page.evaluate(f"setChatBackground('{preset}')")
            await page.wait_for_timeout(300)
            res = await page.evaluate("""() => {
                const layer = document.getElementById('conversation-bg-layer');
                const computed = window.getComputedStyle(layer);
                return {
                    className: layer.className,
                    bgImage: computed.backgroundImage,
                    bgColor: computed.backgroundColor,
                    opacity: computed.opacity,
                    zIndex: computed.zIndex,
                    width: layer.offsetWidth,
                    height: layer.offsetHeight
                };
            }""")
            print(f"  Result for {preset}: bgImage={res['bgImage'][:50]}... zIndex={res['zIndex']} size={res['width']}x{res['height']}")
            await page.screenshot(path=os.path.join(ARTIFACT_DIR, f"debug_bg_preset_{preset}.png"))
            
        # 2. Test 21st.dev Shaders
        shaders = [
            '21st-globe',
            '21st-fluid-field',
            '21st-particle-wave',
            '21st-shader-metal',
            '21st-glyph-swell',
            '21st-wave-mesh',
            '21st-fluid-canvas',
            '21st-wave-background'
        ]
        for shader in shaders:
            print(f"\nTesting shader: {shader}")
            await page.evaluate(f"setChatBackground('{shader}')")
            await page.wait_for_timeout(1000)
            frame_info = await page.evaluate("""() => {
                const frame = document.getElementById('chat-bg-canvas-frame');
                const layer = document.getElementById('conversation-bg-layer');
                return {
                    hasFrame: !!frame,
                    src: frame ? frame.src : null,
                    offsetWidth: frame ? frame.offsetWidth : 0,
                    offsetHeight: frame ? frame.offsetHeight : 0,
                    layerClasses: layer.className
                };
            }""")
            print(f"  Result for {shader}: hasFrame={frame_info['hasFrame']} src={frame_info['src']} size={frame_info['offsetWidth']}x{frame_info['offsetHeight']}")
            await page.screenshot(path=os.path.join(ARTIFACT_DIR, f"debug_bg_shader_{shader}.png"))

        # 3. Test Custom Image URL
        print("\nTesting custom background URL...")
        test_url = "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=1600&auto=format&fit=crop"
        await page.evaluate(f"setChatBackground('custom', '{test_url}')")
        await page.wait_for_timeout(500)
        custom_res = await page.evaluate("""() => {
            const layer = document.getElementById('conversation-bg-layer');
            const computed = window.getComputedStyle(layer);
            return {
                styleBg: layer.style.backgroundImage,
                computedBg: computed.backgroundImage
            };
        }""")
        print("  Custom bg result:", custom_res)
        await page.screenshot(path=os.path.join(ARTIFACT_DIR, "debug_bg_custom.png"))

        print("\nAll errors encountered:", errors)
        print("All failed requests:", failed_requests)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_all_backgrounds())
