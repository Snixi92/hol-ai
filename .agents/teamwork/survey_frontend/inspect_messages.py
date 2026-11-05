from pathlib import Path

html_path = Path(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html")
content = html_path.read_text(encoding="utf-8")

funcs = ['function appendAssistantMessage', 'function appendUserMessage', 'function showTypingIndicator']
for fn in funcs:
    idx = content.find(fn)
    if idx != -1:
        print(f"\n=================== {fn} ===================")
        print(content[idx:idx+2500])
