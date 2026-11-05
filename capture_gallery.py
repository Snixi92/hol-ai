import asyncio
import os
from playwright.async_api import async_playwright

ARTIFACT_DIR = r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494"

async def capture_extra():
    async with async_playwright() as p:
        # 1. iPhone 15 Pro with active chat conversation
        iphone = p.devices['iPhone 15 Pro']
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(**iphone)
        page = await ctx.new_page()
        
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        await page.wait_for_timeout(800)
        
        # Click on a quick suggestion (e.g. iPhone XR) to trigger active discussion
        btn = page.locator("button:has-text('iPhone XR le moins cher')").first
        if await btn.is_visible():
            await btn.click()
            # Wait for AI streaming response
            await page.wait_for_timeout(3500)
        
        path_chat = os.path.join(ARTIFACT_DIR, "mobile_optimized_iphone_chat_active.png")
        await page.screenshot(path=path_chat)
        print(f"Captured: {path_chat}")
        await ctx.close()
        
        # 2. Pixel 7 (Android) Viewport
        pixel = p.devices['Pixel 7']
        ctx_android = await browser.new_context(**pixel)
        page_android = await ctx_android.new_page()
        await page_android.goto("http://127.0.0.1:8000", wait_until="networkidle")
        await page_android.wait_for_timeout(800)
        
        path_android = os.path.join(ARTIFACT_DIR, "mobile_optimized_android_home.png")
        await page_android.screenshot(path=path_android)
        print(f"Captured: {path_android}")
        await ctx_android.close()
        
        await browser.close()
        print("Done extra captures!")

if __name__ == "__main__":
    asyncio.run(capture_extra())
