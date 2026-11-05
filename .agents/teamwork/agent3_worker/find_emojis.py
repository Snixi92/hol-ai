import re
import sys
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

index_path = r'C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html'
with open(index_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

emoji_pattern = re.compile(r'[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U00002600-\U000026FF]')

emoji_lines = []
for i, line in enumerate(lines, 1):
    found = emoji_pattern.findall(line)
    if found:
        emoji_lines.append((i, found, line.strip()))

print(f"Total lines with emojis: {len(emoji_lines)}")
for i, found, text in emoji_lines:
    print(f"L{i}: {' '.join(found)} | {text[:120]}")
