import sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

html_path = Path(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html")
content = html_path.read_text(encoding="utf-8")

idx = content.find("type === 'media_asset'")
if idx != -1:
    print("=================== media_asset card rendering ===================")
    print(content[idx:idx+1500])
