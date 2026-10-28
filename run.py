"""
Gold Contract Radar — Unified Development Launcher
Runs both the FastAPI backend and Next.js frontend concurrently from the project root.
"""

import sys
import os
import subprocess
import signal
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

# Locate Python in venv if available, otherwise fallback to sys.executable
if os.name == "nt":
    venv_python = os.path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = os.path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe")
else:
    venv_python = os.path.join(PROJECT_ROOT, ".venv", "bin", "python")
    if not os.path.exists(venv_python):
        venv_python = os.path.join(BACKEND_DIR, ".venv", "bin", "python")

python_bin = venv_python if os.path.exists(venv_python) else sys.executable
npm_cmd = "npm.cmd" if os.name == "nt" else "npm"


def print_banner():
    print("=" * 65)
    print("  [*] GOLD CONTRACT RADAR - MCX DERIVATIVES INTELLIGENCE")
    print("=" * 65)
    print("  [-] Backend API:   http://127.0.0.1:8000")
    print("  [-] API Swagger:   http://127.0.0.1:8000/docs")
    print("  [-] Web Frontend:  http://localhost:3000")
    print("=" * 65)
    print("  Press Ctrl+C anytime to stop both servers.")
    print("=" * 65 + "\n")


def main():
    print_banner()

    # Check if port 8000 is already occupied
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        in_use = s.connect_ex(("127.0.0.1", 8000)) == 0
        if in_use:
            print("[!] Port 8000 is already in use by an existing process.")
            print("    Please close the existing backend or run taskkill /F /IM uvicorn.exe")
            sys.exit(1)

    # 1. Start FastAPI Backend
    api_cmd = [
        python_bin, "-m", "uvicorn",
        "api.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload"
    ]
    print("Starting FastAPI Backend (Port 8000)...")
    backend_proc = subprocess.Popen(api_cmd, cwd=BACKEND_DIR)

    time.sleep(1.5)

    # 2. Start Next.js Frontend
    frontend_cmd = [npm_cmd, "run", "dev"]
    print("Starting Next.js Frontend (Port 3000)...")
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=FRONTEND_DIR)

    def shutdown(sig, frame):
        print("\n\nShutting down servers cleanly...")
        try:
            frontend_proc.terminate()
            backend_proc.terminate()
            frontend_proc.wait(timeout=3)
            backend_proc.wait(timeout=3)
        except Exception:
            frontend_proc.kill()
            backend_proc.kill()
        print("Done. Goodbye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    # Keep alive and monitor child processes
    try:
        while True:
            b_ret = backend_proc.poll()
            f_ret = frontend_proc.poll()
            if b_ret is not None:
                print(f"Backend exited unexpectedly with code {b_ret}")
                shutdown(None, None)
            if f_ret is not None:
                print(f"Frontend exited unexpectedly with code {f_ret}")
                shutdown(None, None)
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown(None, None)


if __name__ == "__main__":
    main()
