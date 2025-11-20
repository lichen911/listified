"""Listified FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routers import items, lists

# Get the absolute path to static files directory
STATIC_DIR = Path(__file__).parent.parent.parent / "static"

app = FastAPI(
    title="Listified",
    description="A simple app for creating and managing lists",
    version="0.1.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(lists.router)
app.include_router(items.router)


@app.get("/")
def serve_index() -> FileResponse:
    """Serve the main SPA index.html at the root path."""
    index_path = STATIC_DIR / "index.html"
    return FileResponse(index_path)


# Mount static files (CSS, JS, etc.) at the root
# Note: This must come after other routes to avoid conflicts
if STATIC_DIR.exists():
    # Mount subdirectories directly under root paths
    css_dir = STATIC_DIR / "css"
    js_dir = STATIC_DIR / "js"
    if css_dir.exists():
        app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
    if js_dir.exists():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Dictionary with status information.
    """
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
