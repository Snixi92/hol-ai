"""
Automated Verification Script for Requirement R4:
Apple iOS 27 Liquid Glass Design System, Ergonomics, & Luxury Palette.

Asserts:
1. CSS rules conform to:
   - blur(24px) saturate(180%) contrast(105%)
   - -webkit-backdrop-filter: blur(24px) saturate(180%) contrast(105%)
   - 1px specular borders (border: 1px solid rgba(255, 255, 255, 0.12); border-top: 1px solid rgba(255, 255, 255, 0.22);)
   - Inset box-shadow reflections (inset 0 1px 1px 0 rgba(255, 255, 255, 0.18), inset 0 -1px 1px 0 rgba(0, 0, 0, 0.4), 0 20px 40px -15px rgba(0, 0, 0, 0.7))
   - Spring physics transitions (transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275))
   - Classes .liquid-glass, .liquid-glass-regular, .liquid-glass-dock, .liquid-glass-subtle
2. Floating Pill Input Dock classes and positioning:
   - Centered container (.ios-dock-container) with fixed bottom positioning and safe area insets
   - Inner dock pill (.liquid-glass-dock) with spring micro-interactions
   - Essential input controls (#chat-form, #user-input, #send-btn, attachments, mic)
3. Elimination of emoji clutter in interface controls:
   - Controls and badges use clean vector icons (Lucide data-lucide or SVGs)
   - Zero emoji clutter in interface controls, dock, thinking modes, and status indicators
4. Palette neutrality and text readability:
   - Luxury monochrome palette: obsidian, titanium, anthracite, transparent glass, off-white
   - Elimination of loud neon accents (emerald/cyan/rose) from dock controls
   - High contrast text readability on dark and light surfaces
5. Upgraded markdown code rendering:
   - Syntax block container (.code-block-container) with language header and copy button
   - Interactive copyCodeSnippet function with feedback
"""

import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Paths
CORE_ENGINE_DIR = Path(__file__).resolve().parent
STATIC_INDEX_HTML = CORE_ENGINE_DIR / "src" / "api" / "static" / "index.html"


def load_index_html() -> str:
    if not STATIC_INDEX_HTML.exists():
        raise FileNotFoundError(f"index.html not found at {STATIC_INDEX_HTML}")
    return STATIC_INDEX_HTML.read_text(encoding="utf-8")


def test_css_liquid_glass_calibration():
    """Verify Apple Liquid Glass calibration values across all master glass classes."""
    content = load_index_html()
    
    # Extract <style> block
    style_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
    assert style_match, "index.html must contain a <style> block"
    style_css = style_match.group(1)

    # 1. Check Root calibration variables
    assert "--glass-blur: 24px;" in style_css, "Root --glass-blur must be 24px"
    assert "--glass-saturate: 180%;" in style_css, "Root --glass-saturate must be 180%"
    assert "--glass-contrast: 105%;" in style_css, "Root --glass-contrast must be 105%"
    assert "cubic-bezier(0.175, 0.885, 0.32, 1.275)" in style_css, "Root spring physics curve must be cubic-bezier(0.175, 0.885, 0.32, 1.275)"

    # 2. Check backdrop-filter blur(24px) saturate(180%) contrast(105%)
    glass_classes = [".liquid-glass", ".liquid-glass-regular", ".liquid-glass-dock", ".liquid-glass-subtle"]
    for cls in glass_classes:
        assert cls in style_css, f"Master CSS class {cls} must exist in <style>"

    # Assert exact backdrop-filter rule presence
    assert "backdrop-filter: blur(24px) saturate(180%) contrast(105%);" in style_css, \
        "CSS must contain 'backdrop-filter: blur(24px) saturate(180%) contrast(105%);'"
    assert "-webkit-backdrop-filter: blur(24px) saturate(180%) contrast(105%);" in style_css, \
        "CSS must contain '-webkit-backdrop-filter: blur(24px) saturate(180%) contrast(105%);'"

    # 3. Check 1px specular borders
    assert "border: 1px solid rgba(255, 255, 255, 0.12);" in style_css, \
        "CSS must contain 1px specular border: 'border: 1px solid rgba(255, 255, 255, 0.12);'"
    assert "border-top: 1px solid rgba(255, 255, 255, 0.22);" in style_css, \
        "CSS must contain top specular highlight: 'border-top: 1px solid rgba(255, 255, 255, 0.22);'"

    # 4. Check internal light reflections (inset box-shadow)
    assert "inset 0 1px 1px 0 rgba(255, 255, 255, 0.18)" in style_css, \
        "CSS must contain specular top reflection inset 0 1px 1px 0 rgba(255, 255, 255, 0.18)"
    assert "inset 0 -1px 1px 0 rgba(0, 0, 0, 0.4)" in style_css, \
        "CSS must contain bottom shadow reflection inset 0 -1px 1px 0 rgba(0, 0, 0, 0.4)"
    assert "0 20px 40px -15px rgba(0, 0, 0, 0.7)" in style_css, \
        "CSS must contain volumetric drop shadow 0 20px 40px -15px rgba(0, 0, 0, 0.7)"

    # 5. Check spring physics transition
    assert "transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);" in style_css, \
        "CSS must contain spring physics: transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);"


def test_floating_pill_input_dock_ergonomics():
    """Verify centered Floating Pill Input Dock positioning, micro-interactions, and controls."""
    content = load_index_html()
    
    # 1. Dock container positioning
    assert "ios-dock-container" in content, "Must include .ios-dock-container element"
    dock_container_match = re.search(r'<div[^>]*class="[^"]*ios-dock-container[^"]*"[^>]*>', content)
    assert dock_container_match, "ios-dock-container div must exist in HTML"
    dock_class_str = dock_container_match.group(0)
    assert "fixed" in dock_class_str, "Dock container must have fixed positioning"
    assert "inset-x-0" in dock_class_str and "mx-auto" in dock_class_str, "Dock container must be horizontally centered"
    assert "max-w-3xl" in dock_class_str or "max-w-2xl" in dock_class_str, "Dock container must constrain max-width for ergonomics"
    assert "pointer-events-none" in dock_class_str, "Dock container wrapper must let events pass through outside pill"

    # 2. Inner pill dock
    inner_dock_match = re.search(r'<div[^>]*class="[^"]*liquid-glass-dock[^"]*"[^>]*>', content)
    assert inner_dock_match, "Inner dock pill with .liquid-glass-dock must exist"
    inner_class_str = inner_dock_match.group(0)
    assert "pointer-events-auto" in inner_class_str, "Inner dock pill must capture pointer events"

    # 3. Chat form and input elements
    assert '<form id="chat-form"' in content, "Dock must contain #chat-form"
    assert '<input' in content and 'id="user-input"' in content, "Dock must contain #user-input"
    assert 'id="send-btn"' in content, "Dock must contain #send-btn submit button"
    assert 'triggerAttachmentUpload()' in content, "Dock must contain attachment action"
    assert 'triggerVoiceInput()' in content, "Dock must contain voice input action"

    # 4. Dock micro-interactions in CSS
    style_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
    assert style_match
    style_css = style_match.group(1)
    assert ".liquid-glass-dock:hover" in style_css or ".liquid-glass-dock:focus-within" in style_css, \
        "Dock must have hover/focus-within micro-interaction in CSS"


def test_elimination_of_emoji_clutter_in_interface():
    """Verify that interface controls, dock, buttons, and badges have zero emoji clutter."""
    content = load_index_html()

    # Isolate interface controls: header navbar, dock container, and settings modal controls
    dock_match = re.search(r'<div class="[^"]*ios-dock-container[^"]*"[\s\S]*?</main>', content)
    assert dock_match, "Floating input dock section must be present"
    dock_html = dock_match.group(0)

    header_match = re.search(r'<header[\s\S]*?</header>', content)
    assert header_match, "Header section must be present"
    header_html = header_match.group(0)

    # Emoji regex pattern
    emoji_pattern = re.compile(r'[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF]')
    
    # Check dock HTML for raw emojis
    dock_emojis = emoji_pattern.findall(dock_html)
    assert len(dock_emojis) == 0, f"Floating dock controls must have 0 emojis, found: {dock_emojis}"

    # Check header HTML for raw emojis
    header_emojis = emoji_pattern.findall(header_html)
    assert len(header_emojis) == 0, f"Header controls must have 0 emojis, found: {header_emojis}"

    # Check for presence of Lucide vector icons in interface
    assert 'data-lucide=' in content, "Interface must use Lucide vector icons (data-lucide)"
    assert 'data-lucide="paperclip"' in content, "Dock must use Lucide paperclip icon"
    assert 'data-lucide="camera"' in content, "Dock must use Lucide camera icon"
    assert 'data-lucide="mic"' in content, "Dock must use Lucide mic icon"
    assert 'data-lucide="arrow-up"' in content, "Dock must use Lucide arrow-up send icon"


def test_luxury_neutral_palette_and_readability():
    """Verify the luxury monochrome neutral palette (obsidian, titanium, anthracite) and crisp text contrast."""
    content = load_index_html()

    # 1. Palette tokens in tailwind.config
    assert "obsidian" in content, "Tailwind config must include luxury obsidian palette"
    assert "titanium" in content, "Tailwind config must include luxury titanium palette"
    assert "#08080a" in content, "Obsidian base color #08080a must be configured"

    # 2. Check that the floating dock does not have loud neon emerald/cyan colors
    dock_match = re.search(r'<div class="[^"]*ios-dock-container[^"]*"[\s\S]*?</main>', content)
    dock_html = dock_match.group(0)
    assert "bg-emerald-400 animate-pulse" not in dock_html, \
        "Dock active indicator must be upgraded to luxury neutral white/neutral glow instead of loud neon emerald"
    assert "rgba(56,189,248" not in dock_html, \
        "Dock controls must avoid saturated cyan glows in favor of neutral monochrome glass"

    # 3. Readability & text contrast
    assert "bubble-assistant" in content, "Content layer must specify .bubble-assistant"
    style_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
    style_css = style_match.group(1)
    assert "#111115" in style_css, "Assistant bubble must have dark solid titanium/obsidian backing for maximum legibility"


def test_markdown_code_rendering_upgrade():
    """Verify that Markdown code rendering includes syntax container, language badge, and copy button."""
    content = load_index_html()

    # 1. formatMarkdown function definition
    assert "function formatMarkdown(" in content, "formatMarkdown function must be defined"
    
    # 2. Code block container with copy button
    assert "code-block-container" in content, "Markdown renderer must produce .code-block-container"
    assert "copy-code-btn" in content, "Markdown renderer must produce .copy-code-btn"
    assert "copyCodeSnippet" in content, "JavaScript must define copyCodeSnippet function"

    # 3. Markdown features
    assert "escapeHtml" in content, "Markdown renderer must sanitize HTML"
    assert "navigator.clipboard" in content, "Copy function must utilize Clipboard API"


def run_all_verifications():
    """Run all verifications and print detailed forensic evidence."""
    tests = [
        ("CSS Liquid Glass Calibration (blur 24px, 1px specular, inset reflections)", test_css_liquid_glass_calibration),
        ("Floating Pill Input Dock Ergonomics & Micro-Interactions", test_floating_pill_input_dock_ergonomics),
        ("Elimination of Emoji Clutter in Interface Controls", test_elimination_of_emoji_clutter_in_interface),
        ("Luxury Monochrome Neutral Palette & Readability", test_luxury_neutral_palette_and_readability),
        ("Upgraded Markdown Code Rendering with Copy Action", test_markdown_code_rendering_upgrade),
    ]

    print("\n" + "=" * 70)
    print("HO L AI — FORENSIC AUDIT: REQUIREMENT R4 (APPLE LIQUID GLASS)")
    print("=" * 70)

    passed_count = 0
    failed_count = 0

    for name, test_fn in tests:
        try:
            test_fn()
            print(f"  [PASS] {name}")
            passed_count += 1
        except AssertionError as e:
            print(f"  [FAIL] {name}: {e}")
            failed_count += 1
        except Exception as e:
            print(f"  [ERROR] {name}: {type(e).__name__}: {e}")
            failed_count += 1

    print("=" * 70)
    print(f"RESULTS: {passed_count} PASSED, {failed_count} FAILED")
    print("=" * 70 + "\n")

    return failed_count == 0


if __name__ == "__main__":
    success = run_all_verifications()
    sys.exit(0 if success else 1)
