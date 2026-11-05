import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        device = p.devices['iPhone 15 Pro']
        browser = await p.chromium.launch()
        context = await browser.new_context(**device)
        page = await context.new_page()

        await page.goto("http://localhost:8000", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        # Send a message to see messages and cards rendered on mobile
        await page.fill('#user-input', 'iPhone 15')
        await page.click('#send-btn')

        # Wait for streaming response to finish
        await page.wait_for_timeout(6000)

        shot_chat = r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494\mobile_audit_chat_flow.png"
        await page.screenshot(path=shot_chat)
        print("Saved mobile chat flow screenshot:", shot_chat)

        # Scroll to bottom and capture
        await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(500)
        shot_chat_bottom = r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494\mobile_audit_chat_bottom.png"
        await page.screenshot(path=shot_chat_bottom)
        print("Saved mobile chat bottom screenshot:", shot_chat_bottom)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
