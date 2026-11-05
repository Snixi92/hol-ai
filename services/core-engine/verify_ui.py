import asyncio
from playwright.async_api import async_playwright

async def verify_new_ui():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        # 1. Desktop Landing
        page_d = await browser.new_page(viewport={"width": 1280, "height": 850})
        await page_d.goto("http://127.0.0.1:8000")
        await page_d.wait_for_timeout(1000)
        await page_d.screenshot(path=r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494\desktop_apple_liquid_glass_landing.png")

        # 2. Open Phone Connect Modal
        await page_d.click("button[title*='Téléphone']")
        await page_d.wait_for_timeout(600)
        await page_d.screenshot(path=r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494\desktop_phone_modal_glass.png")
        # Close modal
        await page_d.click("#phone-connect-modal button[onclick*='togglePhoneConnectModal']")
        await page_d.wait_for_timeout(300)

        # 3. Open Thinking Menu Dropdown
        await page_d.click("#thinking-mode-btn")
        await page_d.wait_for_timeout(400)
        await page_d.screenshot(path=r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494\desktop_thinking_dropdown_glass.png")
        await page_d.click("#thinking-mode-btn")
        await page_d.wait_for_timeout(300)

        # 4. Mobile Landing (iPhone 14/15/16 Pro)
        page_m = await browser.new_page(viewport={"width": 390, "height": 844})
        await page_m.goto("http://127.0.0.1:8000")
        await page_m.wait_for_timeout(1000)
        await page_m.screenshot(path=r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494\mobile_apple_liquid_glass_landing.png")

        # 5. Mobile Phone Modal
        await page_m.evaluate("togglePhoneConnectModal()")
        await page_m.wait_for_timeout(500)
        await page_m.screenshot(path=r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494\mobile_phone_modal_glass.png")

        await browser.close()
        print("All UI verification screenshots captured successfully!")

asyncio.run(verify_new_ui())
