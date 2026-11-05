import urllib.request
import urllib.parse
import json
import re

def search_real_products(query_term, site=None):
    query = f"site:{site} {query_term}" if site else query_term
    encoded = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode("utf-8")
            
            # Extract links and titles
            matches = re.findall(r'<a class="result__snippet[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
            results = []
            for link, snippet in matches:
                # DuckDuckGo wraps links in /l/?kh=-1&uddg=...
                actual_link = link
                if "uddg=" in link:
                    m = re.search(r"uddg=([^&]+)", link)
                    if m:
                        actual_link = urllib.parse.unquote(m.group(1))
                
                snippet_clean = re.sub(r"<[^>]+>", "", snippet).strip()
                results.append((actual_link, snippet_clean))
            return results
    except Exception as e:
        print("Error fetching DuckDuckGo:", e)
        return []

if __name__ == "__main__":
    print("=== Testing Cdiscount ===")
    res_cdiscount = search_real_products("pc portable rtx 4060", site="cdiscount.com/dp/ OR site:cdiscount.com/f-")
    for link, snip in res_cdiscount[:4]:
        print("URL:", link)
        print("Snippet:", snip[:100])
        print("---")
