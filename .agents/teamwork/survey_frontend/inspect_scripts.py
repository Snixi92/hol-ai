import re
from pathlib import Path

html_path = Path(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html")
content = html_path.read_text(encoding="utf-8")

# Let's inspect the HTML body layout
# Find body content before scripts
body_match = re.search(r'<body[^>]*>(.*?)<script', content, re.DOTALL)
if body_match:
    body_html = body_match.group(1)
    print(f"Body HTML before scripts: {len(body_html):,} chars, {body_html.count(chr(10))} lines")
    # Extract IDs in the body
    ids = re.findall(r'id=["\']([^"\']+)["\']', body_html)
    print("\nDOM Elements with ID in body (first 50):", ids[:50])

# Inspect Script #1
scripts = re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', content, re.DOTALL)
for i, s in enumerate(scripts):
    lines = [l.strip() for l in s.strip().split('\n') if l.strip()]
    first_few = '\n'.join(lines[:10])
    print(f"\n=================== SCRIPT #{i+1} PREVIEW ({len(s):,} chars) ===================")
    print(first_few)
    print("...")

