import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Log all console messages
        page.on("console", lambda m: print("PAGE CONSOLE:", m.text))
        page.on("pageerror", lambda e: print("PAGE ERROR:", e))
        
        await page.goto('http://localhost:8000')
        await page.wait_for_timeout(1000)
        
        # Check what window.onLiquidNavAction is
        fn_str = await page.evaluate("() => window.onLiquidNavAction ? window.onLiquidNavAction.toString() : 'undefined'")
        print("window.onLiquidNavAction definition:")
        print(fn_str)
        
        # Check what toggleTheme is
        tt_str = await page.evaluate("() => typeof toggleTheme")
        print("typeof toggleTheme:", tt_str)
        
        # Call onLiquidNavAction directly
        print("\nCalling window.onLiquidNavAction(3, 'theme') via evaluate...")
        await page.evaluate("() => window.onLiquidNavAction(3, 'theme')")
        theme_after_eval = await page.evaluate("() => currentTheme")
        print("Theme after evaluate:", theme_after_eval)
        
        # Now click via Playwright
        print("\nClicking button via Playwright...")
        btn = page.locator('#site-liquid-navbar button[data-action="theme"]')
        await btn.click(force=True)
        await page.wait_for_timeout(300)
        theme_after_click = await page.evaluate("() => currentTheme")
        print("Theme after click:", theme_after_click)
        
        await browser.close()

asyncio.run(run())
