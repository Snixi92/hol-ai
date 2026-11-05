import asyncio
import os
from playwright.async_api import async_playwright

ARTIFACT_DIR = r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494"

async def test_mobile():
    async with async_playwright() as p:
        # Emulate iPhone 15 Pro
        iphone = p.devices['iPhone 15 Pro']
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            **iphone
        )
        page = await context.new_page()
        
        # Navigate to HoL AI
        print("Navigating to http://127.0.0.1:8000 ...")
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        
        # 1. Capture Mobile Home screen
        path_home = os.path.join(ARTIFACT_DIR, "mobile_optimized_iphone_home.png")
        await page.screenshot(path=path_home)
        print(f"Captured: {path_home}")
        
        # 2. Check font size of #user-input
        user_input = page.locator("#user-input")
        font_size = await user_input.evaluate("el => window.getComputedStyle(el).fontSize")
        print(f"User Input Font Size on mobile: {font_size} (Expected >= 16px to prevent iOS auto-zoom)")
        
        # 3. Open Sidebar and capture
        await page.evaluate("toggleSidebar()")
        await page.wait_for_timeout(600)
        path_sidebar = os.path.join(ARTIFACT_DIR, "mobile_optimized_iphone_sidebar.png")
        await page.screenshot(path=path_sidebar)
        print(f"Captured: {path_sidebar}")
        # Close sidebar
        await page.evaluate("toggleSidebar()")
        await page.wait_for_timeout(400)
        
        # 4. Open Settings Modal (iOS Bottom Sheet)
        await page.evaluate("openSettingsModal()")
        await page.wait_for_timeout(600)
        path_settings = os.path.join(ARTIFACT_DIR, "mobile_optimized_iphone_settings_sheet.png")
        await page.screenshot(path=path_settings)
        print(f"Captured: {path_settings}")
        await page.evaluate("closeSettingsModal()")
        await page.wait_for_timeout(400)
        
        # 5. Open Phone Connect / Take Over Modal
        await page.evaluate("togglePhoneConnectModal()")
        await page.wait_for_timeout(600)
        path_phone = os.path.join(ARTIFACT_DIR, "mobile_optimized_iphone_phone_sheet.png")
        await page.screenshot(path=path_phone)
        print(f"Captured: {path_phone}")
        await page.evaluate("togglePhoneConnectModal()")
        await page.wait_for_timeout(400)

        # 6. Test Spaces Liquid Navbar navigation on mobile
        # Tab 1: Objectifs
        await page.evaluate("window.onSpacesNavAction && window.onSpacesNavAction(1)")
        await page.wait_for_timeout(500)
        path_tab1 = os.path.join(ARTIFACT_DIR, "mobile_optimized_iphone_spaces_tab1.png")
        await page.screenshot(path=path_tab1)
        print(f"Captured: {path_tab1}")

        # Tab 0: Feed
        await page.evaluate("window.onSpacesNavAction && window.onSpacesNavAction(0)")
        await page.wait_for_timeout(400)

        await browser.close()
        print("Mobile verification completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_mobile())
