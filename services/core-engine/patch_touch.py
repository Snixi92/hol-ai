path = r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

target_str = """        // --- DYNAMIQUE OPTIQUE DE FRESNEL (Interactive Cursor/Touch Tracking) ---
        document.addEventListener('mousemove', (e) => {
            const glassElements = document.querySelectorAll('.liquid-glass, .liquid-glass-regular, .liquid-glass-dock, .liquid-glass-subtle');
            glassElements.forEach(el => {
                const rect = el.getBoundingClientRect();
                if (e.clientX >= rect.left - 40 && e.clientX <= rect.right + 40 &&
                    e.clientY >= rect.top - 40 && e.clientY <= rect.bottom + 40) {
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    el.style.setProperty('--mouse-x', `${x}px`);
                    el.style.setProperty('--mouse-y', `${y}px`);
                }
            });
        }, { passive: true });"""

replacement_str = """        // --- DYNAMIQUE OPTIQUE DE FRESNEL (Interactive Cursor/Touch Tracking) ---
        function updateGlassCoords(clientX, clientY) {
            const glassElements = document.querySelectorAll('.liquid-glass, .liquid-glass-regular, .liquid-glass-dock, .liquid-glass-subtle');
            glassElements.forEach(el => {
                const rect = el.getBoundingClientRect();
                if (clientX >= rect.left - 50 && clientX <= rect.right + 50 &&
                    clientY >= rect.top - 50 && clientY <= rect.bottom + 50) {
                    const x = clientX - rect.left;
                    const y = clientY - rect.top;
                    el.style.setProperty('--mouse-x', `${x}px`);
                    el.style.setProperty('--mouse-y', `${y}px`);
                }
            });
        }

        document.addEventListener('mousemove', (e) => {
            updateGlassCoords(e.clientX, e.clientY);
        }, { passive: true });

        document.addEventListener('touchstart', (e) => {
            if (e.touches && e.touches[0]) {
                updateGlassCoords(e.touches[0].clientX, e.touches[0].clientY);
            }
        }, { passive: true });

        document.addEventListener('touchmove', (e) => {
            if (e.touches && e.touches[0]) {
                updateGlassCoords(e.touches[0].clientX, e.touches[0].clientY);
            }
        }, { passive: true });"""

if target_str in content:
    content = content.replace(target_str, replacement_str)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Fresnel touch+mouse support installed successfully!")
else:
    print("Target string for Fresnel not found, trying fuzzy match...")
    start_marker = "// --- DYNAMIQUE OPTIQUE DE FRESNEL (Interactive Cursor/Touch Tracking) ---"
    end_marker = "// État de session"
    if start_marker in content and end_marker in content:
        s_idx = content.find(start_marker)
        e_idx = content.find(end_marker)
        content = content[:s_idx] + replacement_str + "\n\n        " + content[e_idx:]
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Fresnel touch+mouse support installed via fuzzy match!")
    else:
        print("Markers not found!")
