path = r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old_header = '<header id="header-messaging" class="h-14 sm:h-16 px-3 sm:px-4 flex items-center justify-between liquid-glass border-b border-white/10 z-20 flex-shrink-0 w-full min-w-0">'
new_header = '<header id="header-messaging" class="h-14 sm:h-16 px-3 sm:px-4 flex items-center justify-between liquid-glass z-20 flex-shrink-0 w-full min-w-0">'

if old_header in content:
    content = content.replace(old_header, new_header)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Header border-b unified successfully!")
else:
    print("Old header string not found!")
