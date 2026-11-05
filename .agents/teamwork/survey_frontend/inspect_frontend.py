import re
from pathlib import Path

html_path = Path(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html")
content = html_path.read_text(encoding="utf-8")

print(f"Total length: {len(content):,} chars")
print(f"Total lines: {content.count(chr(10)):,}")

script_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', content)
print("\n--- External Scripts ---")
for s in script_srcs:
    print(" ", s)

link_css = re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', content)
print("\n--- External Links/CSS ---")
for l in link_css:
    print(" ", l)

styles = re.findall(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
print(f"\n--- Style Tags ({len(styles)}) ---")
for i, s in enumerate(styles):
    print(f" Style #{i+1}: {len(s):,} chars, {s.count(chr(10))} lines")

inline_scripts = re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', content, re.DOTALL)
print(f"\n--- Inline Scripts ({len(inline_scripts)}) ---")
for i, s in enumerate(inline_scripts):
    print(f" Script #{i+1}: {len(s):,} chars, {s.count(chr(10))} lines")
