import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # iPhone 15 Pro emulation
        device = p.devices['iPhone 15 Pro']
        browser = await p.chromium.launch()
        context = await browser.new_context(**device)
        page = await context.new_page()

        await page.goto("http://localhost:8000", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        # 1. Full page initial view on mobile
        shot_home = r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494\mobile_audit_home.png"
        await page.screenshot(path=shot_home)
        print("1. Saved mobile home screenshot:", shot_home)

        # Check horizontal overflow
        body_scroll_w = await page.evaluate("() => document.body.scrollWidth")
        body_client_w = await page.evaluate("() => document.body.clientWidth")
        html_scroll_w = await page.evaluate("() => document.documentElement.scrollWidth")
        html_client_w = await page.evaluate("() => document.documentElement.clientWidth")
        print(f"Horizontal scroll check: body scroll={body_scroll_w}, client={body_client_w}; html scroll={html_scroll_w}, client={html_client_w}")
        has_h_overflow = html_scroll_w > html_client_w or body_scroll_w > body_client_w
        print(f"Has horizontal overflow: {has_h_overflow}")

        # Check header visibility & elements
        header_bounds = await page.evaluate("""() => {
            const h = document.getElementById('header-messaging');
            if (!h) return null;
            const r = h.getBoundingClientRect();
            return { width: r.width, height: r.height, top: r.top, left: r.left };
        }""")
        print("Header bounds:", header_bounds)

        # Check liquid navbar items on mobile
        nav_info = await page.evaluate("""() => {
            const nav = document.getElementById('site-liquid-navbar');
            if (!nav) return null;
            const items = Array.from(nav.querySelectorAll('.nimbus-item')).map(el => ({
                action: el.getAttribute('data-action'),
                visible: window.getComputedStyle(el).display !== 'none',
                width: el.getBoundingClientRect().width,
                height: el.getBoundingClientRect().height
            }));
            return { navWidth: nav.getBoundingClientRect().width, items };
        }""")
        print("Liquid navbar info on mobile:", nav_info)

        # Check Spaces navbar
        spaces_info = await page.evaluate("""() => {
            const nav = document.getElementById('spaces-liquid-navbar');
            if (!nav) return null;
            const r = nav.getBoundingClientRect();
            return { visible: window.getComputedStyle(nav).display !== 'none', width: r.width, height: r.height };
        }""")
        print("Spaces navbar info:", spaces_info)

        # Check Thinking navbar
        thinking_info = await page.evaluate("""() => {
            const nav = document.getElementById('thinking-liquid-navbar');
            if (!nav) return null;
            const r = nav.getBoundingClientRect();
            return { visible: window.getComputedStyle(nav).display !== 'none', width: r.width, height: r.height };
        }""")
        print("Thinking navbar info:", thinking_info)

        # Check input dock
        dock_info = await page.evaluate("""() => {
            const dock = document.querySelector('.liquid-glass-dock') || document.querySelector('form');
            if (!dock) return null;
            const r = dock.getBoundingClientRect();
            const input = document.getElementById('user-input');
            const fs = input ? window.getComputedStyle(input).fontSize : null;
            return { width: r.width, height: r.height, bottom: window.innerHeight - r.bottom, inputFontSize: fs };
        }""")
        print("Input dock info:", dock_info)

        # 2. Open Sidebar and take screenshot
        await page.evaluate("() => toggleSidebar()")
        await page.wait_for_timeout(400)
        shot_sb = r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494\mobile_audit_sidebar.png"
        await page.screenshot(path=shot_sb)
        print("2. Saved mobile sidebar screenshot:", shot_sb)
        await page.evaluate("() => toggleSidebar()")
        await page.wait_for_timeout(300)

        # 3. Open Settings Modal and take screenshot
        await page.evaluate("() => openSettingsModal()")
        await page.wait_for_timeout(400)
        shot_settings = r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494\mobile_audit_settings.png"
        await page.screenshot(path=shot_settings)
        print("3. Saved mobile settings screenshot:", shot_settings)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
