with open(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static\index.html", "r", encoding="utf-8") as f:
    text = f.read()

checks = [
    ("Settings backdrop dismiss", 'id="settings-modal" class="fixed inset-0 bg-black/75 z-50 hidden flex items-center justify-center p-4 backdrop-blur-sm" onclick="if(event.target === this) closeSettingsModal()"'),
    ("Background backdrop dismiss", 'id="background-modal" class="fixed inset-0 bg-black/75 z-50 hidden flex items-center justify-center p-4 backdrop-blur-sm" onclick="if(event.target === this) closeBackgroundModal()"'),
    ("Computer use backdrop dismiss", 'id="computer-use-modal" class="fixed inset-0 z-50 hidden bg-black/80 backdrop-blur-md flex items-center justify-center p-2 sm:p-4 animate-in fade-in duration-200" onclick="if(event.target === this) closeComputerUseModal()"'),
    ("Escape listener has closeSettingsModal", "if (typeof closeSettingsModal === 'function') closeSettingsModal();"),
    ("Escape listener has closeJarvisHud", "if (typeof closeJarvisHud === 'function') closeJarvisHud();"),
    ("Bottom onLiquidNavAction dispatches actions", "openSettingsModal();"),
    ("Bottom onSpacesNavAction calls switchMetaMuseSpace", "switchMetaMuseSpace(space);"),
    ("Global alias sendMessage", "window.sendMessage ="),
    ("Global alias closeJarvisMode", "window.closeJarvisMode ="),
    ("Global alias startNewConversation", "window.startNewConversation ="),
    ("Global alias exportConversationMarkdown", "window.exportConversationMarkdown ="),
]

all_pass = True
for name, sub in checks:
    passed = sub in text
    if not passed:
        all_pass = False
    print(f"[{'PASS' if passed else 'FAIL'}] {name}")

if all_pass:
    print("\nALL 11 CHECKS PASSED PERFECTLY!")
else:
    print("\nSOME CHECKS FAILED!")
