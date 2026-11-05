import sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

html_path = Path(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html")
content = html_path.read_text(encoding="utf-8")

idx = content.find('id="chat-form"')
if idx != -1:
    start = content.rfind('<div', 0, idx)
    start_outer = content.rfind('<div', 0, start - 10)
    print("=================== INPUT DOCK HTML ===================")
    print(content[start_outer:start_outer+2500])
