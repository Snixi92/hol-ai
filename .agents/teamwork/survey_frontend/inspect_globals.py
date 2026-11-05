import sys
import re
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

html_path = Path(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html")
content = html_path.read_text(encoding="utf-8")

scripts = re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', content, re.DOTALL)
script2 = scripts[1]

# Find top-level variables (declared outside function blocks)
lines = script2.split('\n')
in_func = 0
globals_declared = []

for line in lines:
    stripped = line.strip()
    # Check braces count
    in_func += stripped.count('{') - stripped.count('}')
    if in_func <= 0:
        in_func = 0
        if re.match(r'^(var|let|const)\s+([a-zA-Z0-9_$]+)', stripped):
            m = re.match(r'^(var|let|const)\s+([a-zA-Z0-9_$]+)\s*=?\s*(.*)', stripped)
            if m:
                globals_declared.append((m.group(1), m.group(2), m.group(3)[:60]))

print(f"Total top-level globals found: {len(globals_declared)}")
for kind, name, val in globals_declared:
    print(f"  {kind} {name} = {val}")
