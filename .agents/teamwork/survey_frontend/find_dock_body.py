import sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

html_path = Path(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html")
content = html_path.read_text(encoding="utf-8")

# Find occurrences of ios-dock-container in body
body_idx = content.find('<body')
idx = content.find('ios-dock-container', body_idx)
if idx != -1:
    print("Found ios-dock-container in body at char", idx)
    print(content[idx-100:idx+800])
else:
    print("Not found in body! Let's search for dock elements in body:")
    for kw in ['id="chat-form"', 'floating-input-dock', 'bottom-0', 'fixed bottom']:
        p = content.find(kw, body_idx)
        print(f" {kw}: {p}")
        if p != -1:
            print(content[p-100:p+400])
