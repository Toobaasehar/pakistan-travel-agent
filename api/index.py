import os
import sys
import traceback

# Ensure root directory is in sys.path so all imports work seamlessly on Vercel
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from main import app
except Exception as e:
    print(f"[FATAL VERCEL INITIALIZATION ERROR]: {e}", flush=True)
    traceback.print_exc()
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    app = FastAPI()

    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def catch_all_fallback(path_name: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Serverless Initialization Error",
                "detail": str(e),
                "traceback": traceback.format_exc()
            }
        )
