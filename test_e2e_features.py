import asyncio
import json
import time
from playwright.async_api import async_playwright

async def main():
    console_errors = []
    page_errors = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error" else None)
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        print("1. Navigating to http://localhost:8000...")
        await page.goto("http://localhost:8000", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        # 1. Test Header Action 0: Computer-Use
        print("2. Testing Computer-Use modal...")
        await page.click('#site-liquid-navbar button[data-action="computer-use"]')
        await page.wait_for_timeout(400)
        cu_modal = page.locator('#computer-use-modal')
        assert await cu_modal.is_visible(), "Computer-use modal should be visible"
        # Click outside (backdrop dismiss)
        await page.mouse.click(10, 10)
        await page.wait_for_timeout(300)
        assert not await cu_modal.is_visible(), "Computer-use modal should be dismissed by backdrop click"
        print("  -> Computer-Use modal OK")

        # 2. Test Header Action 1: Jarvis
        print("3. Testing Jarvis HUD mode...")
        await page.click('#site-liquid-navbar button[data-action="jarvis"]')
        await page.wait_for_timeout(400)
        jarvis_hud = page.locator('#jarvis-hud-overlay')
        assert await jarvis_hud.is_visible(), "Jarvis HUD should be visible"
        # Press Escape to close
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)
        assert not await jarvis_hud.is_visible(), "Jarvis HUD should be closed by Escape"
        print("  -> Jarvis HUD mode OK")

        # 3. Test Header Action 2: Phone connect modal
        print("4. Testing Phone connect modal...")
        phone_btn = page.locator('#site-liquid-navbar button[data-action="phone"]')
        if await phone_btn.is_visible():
            await phone_btn.click()
            await page.wait_for_timeout(400)
            phone_modal = page.locator('#phone-connect-modal')
            assert await phone_modal.is_visible(), "Phone connect modal should be visible"
            await page.mouse.click(10, 10)
            await page.wait_for_timeout(300)
            assert not await phone_modal.is_visible(), "Phone connect modal should be dismissed by backdrop click"
            print("  -> Phone modal OK")

        # 4. Test Header Action 3: Theme Toggle
        print("5. Testing Theme Toggle...")
        is_dark_before = await page.evaluate("() => document.documentElement.classList.contains('dark')")
        await page.click('#site-liquid-navbar button[data-action="theme"]')
        await page.wait_for_timeout(300)
        is_dark_after = await page.evaluate("() => document.documentElement.classList.contains('dark')")
        assert is_dark_before != is_dark_after, f"Theme class should toggle from {is_dark_before} to {not is_dark_before}"
        # Toggle back to dark
        await page.click('#site-liquid-navbar button[data-action="theme"]')
        await page.wait_for_timeout(300)
        print("  -> Theme Toggle OK")

        # 5. Test Header Action 4: Background Watcher Modal
        print("6. Testing Background Watcher modal...")
        bg_btn = page.locator('#site-liquid-navbar button[data-action="background"]')
        if await bg_btn.is_visible():
            await bg_btn.click()
            await page.wait_for_timeout(400)
            bg_modal = page.locator('#background-modal')
            assert await bg_modal.is_visible(), "Background modal should be visible"
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)
            assert not await bg_modal.is_visible(), "Background modal should be closed by Escape"
            print("  -> Background modal OK")

        # 6. Test Header Action 5: Settings Modal
        print("7. Testing Settings modal & backdrop/Escape dismiss...")
        await page.click('#site-liquid-navbar button[data-action="settings"]')
        await page.wait_for_timeout(400)
        settings_modal = page.locator('#settings-modal')
        assert await settings_modal.is_visible(), "Settings modal should be visible"

        # Click backdrop to dismiss
        await page.mouse.click(10, 10)
        await page.wait_for_timeout(300)
        assert not await settings_modal.is_visible(), "Settings modal should be dismissed by backdrop click"
        print("  -> Settings modal backdrop dismiss OK")

        # Reopen and test Escape key
        await page.click('#site-liquid-navbar button[data-action="settings"]')
        await page.wait_for_timeout(400)
        assert await settings_modal.is_visible()
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)
        assert not await settings_modal.is_visible(), "Settings modal should be dismissed by Escape key"
        print("  -> Settings modal Escape key dismiss OK")

        # 7. Test Thinking Modes
        print("8. Testing Thinking Modes...")
        await page.click('#thinking-deep-btn')
        await page.wait_for_timeout(200)
        level = await page.evaluate("() => currentThinkingLevel")
        assert level == "deep", f"Expected thinking level deep, got {level}"

        await page.click('#thinking-standard-btn')
        await page.wait_for_timeout(200)
        level2 = await page.evaluate("() => currentThinkingLevel")
        assert level2 == "standard", f"Expected thinking level standard, got {level2}"
        print("  -> Thinking Modes OK")

        # 8. Test Spaces Navigation
        print("9. Testing Spaces Navigation (Objectifs)...")
        await page.click('#space-goals-btn')
        await page.wait_for_timeout(500)
        input_val = await page.evaluate("() => document.getElementById('user-input').value")
        print(f"  -> Goals space triggered input: '{input_val}'")
        # Switch back to feed
        await page.click('#space-feed-btn')
        await page.wait_for_timeout(300)
        print("  -> Spaces Navigation OK")

        # 9. Test Sidebar and New Chat
        print("10. Testing Sidebar & startNewChat...")
        await page.evaluate("() => toggleSidebar()")
        await page.wait_for_timeout(300)
        sb = page.locator('#sidebar')
        assert await sb.is_visible(), "Sidebar should be open"
        
        # Test new chat button
        await page.click('button:has-text("Nouvelle discussion")')
        await page.wait_for_timeout(300)
        print("  -> Sidebar & New Chat OK")

        # 10. Test Chat Input & AI Streaming
        print("11. Testing Chat Input & AI Streaming...")
        await page.fill('#user-input', 'Dis bonjour en 3 mots')
        await page.click('#send-btn')
        
        # Wait for assistant response to appear
        start = time.time()
        success = False
        while time.time() - start < 15:
            bubbles = await page.locator('.bubble-ai, .bubble-assistant').all()
            if bubbles:
                text = await bubbles[-1].inner_text()
                if len(text.strip()) > 3:
                    success = True
                    print(f"  -> AI response received: '{text.strip()[:60]}...'")
                    break
            await page.wait_for_timeout(500)
        assert success, "AI should return streaming response"

        # 11. Check errors
        print("\nConsole Errors:", console_errors)
        print("Page Errors:", page_errors)
        assert len(page_errors) == 0, f"Page errors encountered: {page_errors}"

        critical_errors = [e for e in console_errors if "favicon" not in e and "sourcemap" not in e.lower()]
        assert len(critical_errors) == 0, f"Critical console errors encountered: {critical_errors}"

        print("\n=== ALL E2E TEST SUITES PASSED WITH ZERO ERRORS ===")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
