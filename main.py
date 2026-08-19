import sys

# Ensure UTF-8 stdout/stderr so emoji in log lines don't crash on Windows (cp1252).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from database import init_db, init_doctors
from router import router
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_doctors()
    yield


app = FastAPI(
    title=settings.SITE_TITLE,
    lifespan=lifespan,
)

# Mount static files — React build output goes here
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    print(f" Avvio {settings.SITE_TITLE}...")
    print(f"   http://localhost:{getattr(settings, 'PORT', 8000)}")
    uvicorn.run("main:app", host=getattr(settings, 'HOST', '0.0.0.0'), port=getattr(settings, 'PORT', 8000), reload=False)
