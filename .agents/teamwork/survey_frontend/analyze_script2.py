import re
from pathlib import Path

html_path = Path(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html")
content = html_path.read_text(encoding="utf-8")

scripts = re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', content, re.DOTALL)
script2 = scripts[1]

# Find function definitions
funcs = re.findall(r'(?:function\s+([a-zA-Z0-9_$]+)|const\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|var\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)', script2)
flattened_funcs = [f[0] or f[1] or f[2] for f in funcs if f[0] or f[1] or f[2]]
print(f"Total functions found in Script #2: {len(flattened_funcs)}")
print("Key function names (first 80):")
print(flattened_funcs[:80])

# Search for history or chat or sidebar related terms
print("\n--- Chat/History/Sidebar keywords in Script #2 ---")
for kw in ['history', 'sidebar', 'storage', 'conversation', 'indexedDB', 'sessionId', 'render', 'markdown', 'card', 'image', 'stream', 'fetch']:
    matches = len(re.findall(re.escape(kw), script2, re.IGNORECASE))
    print(f" '{kw}': {matches} occurrences")
