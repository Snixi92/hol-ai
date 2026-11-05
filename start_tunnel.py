import subprocess
import re
import os
import sys
import time
import qrcode

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ARTIFACT_DIR = r"C:\Users\Yassir\.gemini\antigravity\brain\e150d96d-341f-4124-86c7-4e4f474c8494"
STATIC_DIR = r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine\src\api\static"
CLOUDFLARED_BIN = r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\cloudflared.exe"

def run_tunnel():
    print("Starting Cloudflare HTTPS Quick Tunnel (HTTP/2) for HoL AI...", flush=True)
    cmd = [CLOUDFLARED_BIN, "tunnel", "--protocol", "http2", "--url", "http://127.0.0.1:8000", "--no-autoupdate"]
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1
    )
    
    tunnel_url = None
    url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')
    
    for line in iter(proc.stdout.readline, ''):
        print(line, end='', flush=True)
        if not tunnel_url:
            match = url_pattern.search(line)
            if match:
                tunnel_url = match.group(0)
                print("\n" + "=" * 70, flush=True)
                print(f"[PUBLIC HTTPS URL DETECTED] {tunnel_url}", flush=True)
                print("=" * 70 + "\n", flush=True)
                
                # Save to text files
                with open("tunnel_url.txt", "w", encoding="utf-8") as f:
                    f.write(tunnel_url)
                
                art_txt = os.path.join(ARTIFACT_DIR, "tunnel_url.txt")
                with open(art_txt, "w", encoding="utf-8") as f:
                    f.write(tunnel_url)
                    
                # Generate QR Code for Phone Camera Scan
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_M,
                    box_size=10,
                    border=4
                )
                qr.add_data(tunnel_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                qr_artifact = os.path.join(ARTIFACT_DIR, "qr_online_phone.png")
                img.save(qr_artifact)
                print(f"QR Code saved to artifact: {qr_artifact}", flush=True)
                
                # Also update static qr_phone.png so the in-app modal shows the online URL
                static_qr = os.path.join(STATIC_DIR, "qr_phone.png")
                img.save(static_qr)
                print(f"QR Code updated in static directory: {static_qr}", flush=True)

    proc.wait()

if __name__ == "__main__":
    run_tunnel()
