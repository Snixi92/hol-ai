import asyncio
from playwright.async_api import async_playwright

async def test_all_shaders():
    shaders = [
        'globe.html',
        'fluid-canvas.html',
        'fluid-field.html',
        'glyph-swell.html',
        'particle-wave.html',
        'shader-metal.html',
        'wave-background.html',
        'wave-mesh.html'
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for shader in shaders:
            url = f"http://127.0.0.1:8000/backgrounds/{shader}?theme=dark"
            errors = []
            page.on("pageerror", lambda err: errors.append(str(err)))
            try:
                resp = await page.goto(url, wait_until="networkidle", timeout=5000)
                await page.wait_for_timeout(400)
                status = resp.status if resp else "no resp"
                print(f"Shader {shader}: HTTP {status}, Errors={len(errors)}: {errors}")
            except Exception as e:
                print(f"Shader {shader}: Exception: {e}")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_all_shaders())
