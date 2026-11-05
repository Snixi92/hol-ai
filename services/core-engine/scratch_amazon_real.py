import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def test_amazon():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="fr-FR"
        )
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        print("Navigating to Amazon search for PS5...")
        await page.goto("https://www.amazon.fr/s?k=playstation+5+slim", wait_until="domcontentloaded", timeout=20000)
        
        # Click cookie accept
        try:
            accept = page.locator("#sp-cc-accept")
            if await accept.count() > 0:
                await accept.click()
                await page.wait_for_timeout(1000)
        except Exception:
            pass
        
        title = await page.title()
        print("Page title:", title)
        
        # Look for search results
        results = page.locator("div[data-component-type='s-search-result']")
        count = await results.count()
        print("Results count:", count)
        
        for i in range(min(3, count)):
            item = results.nth(i)
            t_elem = item.locator("h2 a span, h2 span")
            t_text = await t_elem.first.inner_text() if await t_elem.count() > 0 else ""
            
            link_elem = item.locator("h2 a")
            href = await link_elem.first.get_attribute("href") if await link_elem.count() > 0 else ""
            
            price_elem = item.locator(".a-price .a-offscreen")
            price_text = await price_elem.first.inner_text() if await price_elem.count() > 0 else "N/A"
            
            # Direct product URL
            import urllib.parse
            full_url = urllib.parse.urljoin("https://www.amazon.fr", href)
            # Clean url to keep only /dp/ASIN
            import re
            m = re.search(r"(/dp/[A-Z0-9]+)", full_url)
            clean_url = f"https://www.amazon.fr{m.group(1)}" if m else full_url
            
            print(f"Product {i+1}:")
            print("  Title:", t_text)
            print("  Price:", price_text)
            print("  URL:", clean_url)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_amazon())
