"""
Pakistan Travel Agent — One-Command Launcher
=============================================
Starts the backend server and automatically opens your web browser!

Run with:
    python run.py
"""

import sys
import time
import threading
import webbrowser
import uvicorn


def launch_browser():
    """Waits for server to start, then automatically opens the default web browser."""
    time.sleep(1.2)
    url = "http://127.0.0.1:8000"
    print(f"\n🌐 Opening web application automatically in your browser: {url}\n")
    try:
        webbrowser.open(url, new=2)
    except Exception as e:
        print(f"Could not open browser automatically: {e}. Please visit {url} manually.")


def main():
    print("=" * 60)
    print("  🇵🇰 Pakistan Travel Agent — Starting Server & UI...")
    print("=" * 60)

    # Launch browser automatically in a background daemon thread
    threading.Thread(target=launch_browser, daemon=True).start()

    # Start the FastAPI server
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
