import re
from pathlib import Path

html_path = Path(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html")
content = html_path.read_text(encoding="utf-8")

idx = content.find("function renderChatCard")
if idx != -1:
    end_idx = content.find("function executeApprovedAction", idx)
    print("Length of renderChatCard:", end_idx - idx)
    slice_card = content[idx:end_idx]
    types = re.findall(r"type\s*===\s*['\"]([^'\"]+)['\"]", slice_card)
    print("Card types handled in renderChatCard:", types)
