import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="fr-FR"
        )
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        await page.goto("https://www.amazon.fr/s?k=playstation+5+slim", wait_until="networkidle", timeout=25000)
        print("URL:", page.url)
        print("Title:", await page.title())
        content = await page.content()
        print("Content length:", len(content))
        if "captcha" in content.lower():
            print("Detected CAPTCHA!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect())
