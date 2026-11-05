with open("services/core-engine/src/api/static/index.html", "r", encoding="utf-8") as f:
    text = f.read()

import re

# Find function definitions for hero carousel
funcs = re.findall(r'function\s+(heroCarousel[a-zA-Z0-9_]*|initHeroCarousel|selectHeroCarouselSlide|openHeroCarouselPanoramic|closeHeroCarouselPanoramic)[^\{]*\{', text)
print("Carousel function declarations found:", funcs)

for fn in ['initHeroCarousel', 'selectHeroCarouselSlide', 'openHeroCarouselPanoramic', 'closeHeroCarouselPanoramic', 'updateHeroCarouselUI']:
    m = re.search(r'function\s+' + fn + r'\s*\([^)]*\)\s*\{', text)
    if m:
        start = m.start()
        print(f"\n--- {fn} (at {start}) ---")
        print(text[start:start+1200])
