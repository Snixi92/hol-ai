import re
import sys
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

index_path = r'C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html'
with open(index_path, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.splitlines()
print(f"Total lines: {len(lines)}, Total chars: {len(content)}")

style_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
if style_match:
    style_content = style_match.group(1)
    print(f"Style tag length: {len(style_content)}")
    for cls in ['.liquid-glass', '.liquid-glass-regular', '.liquid-glass-dock', '.liquid-glass-subtle']:
        matches = [m.start() for m in re.finditer(re.escape(cls), style_content)]
        print(f"{cls}: {len(matches)} occurrences in <style>")

# Emoji check
emoji_pattern = re.compile(r'[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U00002600-\U000026FF]')
emojis = emoji_pattern.findall(content)
print(f"Total emojis found: {len(emojis)}")
print("Emoji counts:", Counter(emojis).most_common(20))

# Find lines where emojis appear
print("\nSample lines with emojis:")
for i, line in enumerate(lines, 1):
    found = emoji_pattern.findall(line)
    if found:
        print(f"Line {i}: {found} -> {line.strip()[:100]}")
        if i > 500: # just sample some early ones
            break

# formatMarkdown check
fm = re.search(r'function formatMarkdown\([^)]*\)\s*\{[\s\S]*?^\}', content, re.MULTILINE)
if fm:
    print("\nformatMarkdown found:")
    print(fm.group(0))

# dock html
dock = re.search(r'<div[^>]*class="[^"]*ios-dock-container[^"]*"[\s\S]*?</div>\s*</div>', content)
if dock:
    print("\nFound dock snippet:")
    print(dock.group(0)[:500])
