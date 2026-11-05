import sys
import re
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

html_path = Path(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html")
content = html_path.read_text(encoding="utf-8")

# Check for emojis
emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE)
emojis_found = emoji_pattern.findall(content)
print(f"Total emojis found in index.html: {len(emojis_found)}")
from collections import Counter
print("Emoji distribution:", Counter(emojis_found).most_common(20))

# Check for colors like neon, cyan, purple, amber, green in CSS / HTML classes
neon_keywords = ['neon', 'emerald', 'cyan', 'amber', 'purple', 'violet', 'pink', 'rose', 'indigo', 'blue-500', 'yellow']
for kw in neon_keywords:
    count = len(re.findall(r'\b' + kw + r'[-a-zA-Z0-9]*\b', content, re.IGNORECASE))
    print(f" Keyword '{kw}': {count} occurrences")
