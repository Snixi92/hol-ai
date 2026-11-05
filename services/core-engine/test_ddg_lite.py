import urllib.request
import urllib.parse
import json
import re

def search_ddg_lite(query):
    url = "https://lite.duckduckgo.com/lite/"
    data = urllib.parse.urlencode({"q": query}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/html"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8")
            # In lite.duckduckgo.com, results are in table
            # Links: <a rel="nofollow" href="...">Title</a>
            links = re.findall(r'<a[^>]+class=[\'"]result-link[\'"][^>]+href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', html, re.DOTALL)
            results = []
            for href, title in links:
                t = re.sub(r'<[^>]+>', '', title).strip()
                # Unquote duckduckgo redirect
                actual = href
                if "uddg=" in href:
                    m = re.search(r"uddg=([^&]+)", href)
                    if m:
                        actual = urllib.parse.unquote(m.group(1))
                results.append((actual, t))
            return results
    except Exception as e:
        print("Lite DDG error:", e)
        return []

if __name__ == "__main__":
    print("Testing DuckDuckGo Lite search for real Cdiscount product...")
    res = search_ddg_lite("site:cdiscount.com pc portable rtx 4060")
    print("Found count:", len(res))
    for link, title in res[:6]:
        print("LINK:", link)
        print("TITLE:", title)
        print("---")
