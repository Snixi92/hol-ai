import asyncio
from playwright.async_api import async_playwright

async def verify_mobile_conversation():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page_m = await browser.new_page(viewport={"width": 390, "height": 844})
        await page_m.goto("http://127.0.0.1:8000")
        await page_m.wait_for_timeout(1000)

        # Click the suggestion button "iPhone XR le moins cher" on mobile
        await page_m.click("button:has-text('iPhone XR le moins cher')")
        
        # Wait for streaming
        for i in range(15):
            await page_m.wait_for_timeout(1000)
            text = await page_m.inner_text("#chat-messages")
            if "€" in text or "Amazon" in text or "reconditionné" in text:
                break
        
        await page_m.wait_for_timeout(2000)
        # Screenshot of mobile conversation
        await page_m.screenshot(path=r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494\mobile_active_conversation_liquid_glass.png")
        
        # Scroll up slightly on mobile to see content right behind the mobile dock
        await page_m.evaluate("document.getElementById('chat-messages').scrollTop -= 140")
        await page_m.wait_for_timeout(500)
        await page_m.screenshot(path=r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494\mobile_dock_overlap_refraction.png")

        await browser.close()
        print("Mobile conversation verification completed!")

asyncio.run(verify_mobile_conversation())
