"""
check_groq.py
=============
Interactive diagnostic tool for checking Groq AI API key,
selected model, and function-calling connectivity.

Run with:
    python check_groq.py
"""

import os
import sys
from dotenv import load_dotenv

# Reconfigure Windows console to handle UTF-8 safely
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

load_dotenv()

from agent import get_clean_api_key, test_groq_connection

def main():
    print("=" * 60)
    print("  Pakistan Travel Agent -- Groq AI Diagnostics")
    print("=" * 60)

    raw_env_key = os.getenv("GROQ_API_KEY", "")
    clean_key = get_clean_api_key("GROQ_API_KEY")
    configured_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip() or "llama-3.3-70b-versatile"

    print(f"\n1. Environment Variable Status:")
    if not raw_env_key:
        print("   [!] GROQ_API_KEY is not set or empty in .env.")
    elif raw_env_key.strip().startswith("#"):
        print(f"   [!] WARNING: Your .env entry contains a comment hash: {raw_env_key[:25]}...")
        print("       We cleaned it automatically, but please fix it in .env directly.")
    else:
        # Mask the key for display
        masked = clean_key[:7] + "..." + clean_key[-4:] if len(clean_key) > 12 else "(short key)"
        print(f"   [+] GROQ_API_KEY detected: {masked}")

    print(f"   [+] Configured Model: {configured_model}")

    print(f"\n2. Testing Connection to Groq Cloud API...")
    result = test_groq_connection()

    if result.get("status") == "ok":
        print("   [OK] Authentication successful! Your Groq API key is active.")
        print(f"   [OK] Model '{configured_model}' is accessible.")
        avail = result.get("available_models", [])
        if avail:
            print(f"   [+] Recommended available models: {', '.join(avail[:4])}")
        print("\n>> All checks passed! Your Groq AI Agent is ready to serve travel inquiries.")
    else:
        err = result.get("message", "Unknown error")
        err_type = result.get("error_type", "")
        print(f"   [FAILED] {err_type}: {err}")
        print("\n>> How to fix this:")
        print("   1. Open https://console.groq.com/keys in your browser (it's 100% free).")
        print("   2. Click 'Create API Key' and copy your new key (starts with 'gsk_').")
        print("   3. Open the '.env' file in this project folder.")
        print("   4. Set line: GROQ_API_KEY=gsk_your_new_key_here")
        print("   5. Make sure GROQ_MODEL=llama-3.3-70b-versatile is also set.")
        print("   6. Re-run: python check_groq.py")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
