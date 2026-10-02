import os
import sys

# Ensure root directory is in sys.path so all imports work seamlessly on Vercel
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from main import app

# Export for ASGI handler
app = app
