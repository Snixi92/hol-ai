import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

index_path = r'C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html'
with open(index_path, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.splitlines()

# Find dock container line
for i, line in enumerate(lines, 1):
    if 'ios-dock-container' in line:
        print(f"Found ios-dock-container at line {i}:")
        for j in range(max(1, i - 5), min(len(lines), i + 120)):
            print(f"{j}: {lines[j-1]}")
        break
