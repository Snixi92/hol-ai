import urllib.request, urllib.parse

url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus("cdiscount pc portable gamer")
req = urllib.request.Request(url, headers={"User-Agent": "curl/7.88.1"})
try:
    with urllib.request.urlopen(req, timeout=5) as r:
        print("Status:", r.status)
        content = r.read().decode("utf-8")
        print("Len:", len(content))
        print(content[:500])
except Exception as e:
    print("Err:", e)
