import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

index_path = r'C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html'
with open(index_path, 'r', encoding='utf-8') as f:
    content = f.read()

style_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
if style_match:
    style_content = style_match.group(1)
    
    # Let's find blocks for .liquid-glass
    for match in re.finditer(r'([^{}]+)\{([^{}]+)\}', style_content):
        selectors = match.group(1).strip()
        body = match.group(2).strip()
        if any(cls in selectors for cls in ['.liquid-glass', '.liquid-glass-regular', '.liquid-glass-dock', '.liquid-glass-subtle']):
            print(f"=== Selector: {selectors} ===")
            print(body[:200] + ('...' if len(body) > 200 else ''))
            print()
