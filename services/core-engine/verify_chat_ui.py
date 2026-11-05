import asyncio
from playwright.async_api import async_playwright

async def verify_real_chat():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 850})
        await page.goto("http://127.0.0.1:8000")
        await page.wait_for_timeout(1000)

        # Send a query
        await page.fill("#user-input", "trouve moi un iphone xr le moins cher sur tout internet")
        await page.click("#send-btn")
        
        # Wait for the response to stream and render
        print("Waiting for response to stream...")
        # Poll for completion or text
        for i in range(15):
            await page.wait_for_timeout(1000)
            text = await page.inner_text("#chat-messages")
            if "€" in text or "BackMarket" in text or "Rakuten" in text or "Amazon" in text:
                print(f"Response detected at {i}s")
                break
        
        # Wait a bit more for final formatting
        await page.wait_for_timeout(2000)
        
        # Capture conversation showing scroll & overlap
        await page.screenshot(path=r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494\desktop_real_conversation_liquid_glass.png")
        
        # Scroll up slightly to see content directly passing under the dock
        await page.evaluate("document.getElementById('chat-messages').scrollTop -= 180")
        await page.wait_for_timeout(500)
        await page.screenshot(path=r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494\desktop_dock_overlap_refraction.png")

        # Mobile view of the same conversation
        page_m = await browser.new_page(viewport={"width": 390, "height": 844})
        await page_m.goto("http://127.0.0.1:8000")
        await page_m.wait_for_timeout(1000)
        await page_m.screenshot(path=r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494\mobile_real_conversation_liquid_glass.png")

        await browser.close()
        print("Real chat verification completed!")

asyncio.run(verify_real_chat())
