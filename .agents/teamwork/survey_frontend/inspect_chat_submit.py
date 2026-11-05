from pathlib import Path

html_path = Path(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html")
content = html_path.read_text(encoding="utf-8")

idx = content.find("async function handleChatSubmit")
if idx == -1:
    idx = content.find("function handleChatSubmit")

if idx != -1:
    print("=================== handleChatSubmit ===================")
    print(content[idx:idx+4500])
