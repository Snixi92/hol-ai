import sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

html_path = Path(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html")
content = html_path.read_text(encoding="utf-8")

idx = content.find('ios-dock-container')
if idx != -1:
    print("=================== ios-dock-container HTML ===================")
    print(content[idx-300:idx+2500])
