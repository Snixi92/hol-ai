from pathlib import Path

html_path = Path(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html")
content = html_path.read_text(encoding="utf-8")

# Let's find sidebar HTML
pos = content.find('id="sidebar"')
if pos != -1:
    start = content.rfind('<', 0, pos)
    print("=================== SIDEBAR HTML START ===================")
    print(content[start:start+3500])

# Inspect specific functions
funcs = ['function toggleSidebar', 'function startNewChat', 'function handleChatSubmit', 'function formatMarkdown', 'function renderChatCard', 'function updateGlassCoords']
for fn in funcs:
    idx = content.find(fn)
    if idx != -1:
        print(f"\n=================== {fn} ===================")
        print(content[idx:idx+1500])
