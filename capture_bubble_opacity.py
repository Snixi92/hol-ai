import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        await page.goto("http://localhost:8000", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        # Check opacity in computed styles
        drop_opacity = await page.evaluate("() => window.getComputedStyle(document.querySelector('.nimbus-drop')).opacity")
        water_opacity = await page.evaluate("() => window.getComputedStyle(document.querySelector('.nimbus-water')).opacity")
        print(f"Computed opacity - drop: {drop_opacity}, water: {water_opacity}")

        # Capture initial screenshot
        shot_path = r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494\bubble_opacity_reduced_025.png"
        await page.screenshot(path=shot_path)
        print("Captured full page screenshot to:", shot_path)

        # Capture zoomed in on header and spaces navbar
        header_el = page.locator("#site-liquid-navbar")
        if await header_el.is_visible():
            header_shot = r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494\bubble_header_navbar_025.png"
            await header_el.screenshot(path=header_shot)
            print("Captured header navbar screenshot to:", header_shot)

        # Click Thinking Deep to see the drop move
        await page.click("#thinking-deep-btn")
        await page.wait_for_timeout(400)
        thinking_el = page.locator("#thinking-liquid-navbar")
        if await thinking_el.is_visible():
            thinking_shot = r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494\bubble_thinking_navbar_025.png"
            await thinking_el.screenshot(path=thinking_shot)
            print("Captured thinking navbar screenshot to:", thinking_shot)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
