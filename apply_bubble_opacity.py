path = r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

old_css = """.nimbus-water {
  position: absolute;
  left: -14px;
  top: -14px;
  z-index: -1;
  pointer-events: none;
}
.nimbus-nav[data-gl="off"] .nimbus-water { display: none; }
.nimbus-drop {
  display: block !important;
  position: absolute;
  top: 5px;
  bottom: 5px;
  left: 0;
  border-radius: 999px;
  z-index: 1;
  pointer-events: none;
  will-change: transform, width;
  background: radial-gradient(120% 140% at 30% 0%, rgba(255, 255, 255, 0.31), rgba(255, 255, 255, 0.04) 60%), rgba(255, 255, 255, 0.12);
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.48), inset 0 -1px 2px rgba(0, 0, 0, 0.26), 0 3px 10px -2px rgba(0, 0, 0, 0.38);
  backdrop-filter: blur(6px) saturate(145%);
  -webkit-backdrop-filter: blur(6px) saturate(145%);
}"""

new_css = """.nimbus-water {
  position: absolute;
  left: -14px;
  top: -14px;
  z-index: -1;
  pointer-events: none;
  opacity: 0.75;
}
.nimbus-nav[data-gl="off"] .nimbus-water { display: none; }
.nimbus-drop {
  display: block !important;
  position: absolute;
  top: 5px;
  bottom: 5px;
  left: 0;
  border-radius: 999px;
  z-index: 1;
  pointer-events: none;
  opacity: 0.75;
  will-change: transform, width;
  background: radial-gradient(120% 140% at 30% 0%, rgba(255, 255, 255, 0.23), rgba(255, 255, 255, 0.03) 60%), rgba(255, 255, 255, 0.09);
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.36), inset 0 -1px 2px rgba(0, 0, 0, 0.20), 0 3px 10px -2px rgba(0, 0, 0, 0.28);
  backdrop-filter: blur(6px) saturate(145%);
  -webkit-backdrop-filter: blur(6px) saturate(145%);
}"""

assert old_css in text, "old_css not found in index.html"
text = text.replace(old_css, new_css)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("Updated .nimbus-drop and .nimbus-water opacity successfully")
