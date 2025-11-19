"""Listified FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import items, lists

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


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Dictionary with status information.
    """
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint.

    Returns:
        Dictionary with welcome message.
    """
    return {"message": "Welcome to Listified"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
