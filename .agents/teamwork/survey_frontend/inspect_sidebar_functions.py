import re
from pathlib import Path

html_path = Path(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html")
content = html_path.read_text(encoding="utf-8")

# 1. Extract the sidebar DOM element from HTML
sidebar_match = re.search(r'(<aside[^>]*id=["\']sidebar["\'][^>]*>.*?</aside>)', content, re.DOTALL)
if sidebar_match:
    print("=================== SIDEBAR HTML ===================")
    print(sidebar_match.group(1)[:2000]) # first 2000 chars
    print("...")
else:
    # try searching for id="sidebar"
    m2 = re.search(r'(<[^>]+id=["\']sidebar["\'][^>]*>.*?</(?:aside|div)>)', content, re.DOTALL)
    if m2:
        print("Found sidebar element:", m2.group(0)[:1500])

# 2. Extract toggleSidebar and startNewChat functions
for fn in ['toggleSidebar', 'startNewChat', 'handleChatSubmit', 'formatMarkdown', 'renderChatCard', 'updateGlassCoords']:
    m = re.search(r'(function\s+' + fn + r'\s*\([^)]*\)\s*\{(?:[^{}]*|\{(?:[^{}]*|\{[^{}]*\})*\})*\})', content)
    if m:
        print(f"\n=================== FUNCTION {fn} ===================")
        print(m.group(1)[:1500])
        print("...")
    else:
        print(f"\nCould not find function {fn} with standard regex, searching by declaration...")
        idx = content.find(f"function {fn}")
        if idx != -1:
            print(f"\n=================== FUNCTION {fn} (raw slice) ===================")
            print(content[idx:idx+1200])

