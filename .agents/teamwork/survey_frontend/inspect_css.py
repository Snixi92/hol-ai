import sys
import re
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

html_path = Path(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html")
content = html_path.read_text(encoding="utf-8")

style_match = re.search(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
if style_match:
    css = style_match.group(1)
    print(f"Total CSS length: {len(css)} chars")
    
    # Find all class selectors
    selectors = re.findall(r'(\.[a-zA-Z0-9_\-]+)\s*\{', css)
    unique_selectors = sorted(list(set(selectors)))
    print(f"Unique class selectors defined in CSS ({len(unique_selectors)}):")
    for s in unique_selectors:
        print(" ", s)
        
    print("\n--- Inspecting .liquid-glass and related classes ---")
    for cls in ['.liquid-glass', '.liquid-glass-regular', '.liquid-glass-dock', '.bubble-user-glass', '.bubble-assistant', '.floating-input-dock']:
        idx = css.find(cls)
        if idx != -1:
            end = css.find('}', idx)
            print(f"\n{cls}:")
            print(css[idx:end+1])
