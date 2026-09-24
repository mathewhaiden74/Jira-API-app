import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from routes.auth import router as auth_router
from routes.jira import router as jira_router
from routes.chat import router as chat_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("jira_assistant.main")

app = FastAPI(
    title="Jira AI Assistant API",
    description="External AI-powered assistant connecting to Atlassian Jira Cloud REST API with natural language interaction, safety gates, test case generation, and bug analytics.",
    version="1.0.0"
)

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    settings.FRONTEND_URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if settings.ENVIRONMENT != "development" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include sub-routers
app.include_router(auth_router)
app.include_router(jira_router)
app.include_router(chat_router)

@app.get("/health", summary="Health check endpoint")
async def health_check():
    return {
        "status": "healthy",
        "service": "Jira AI Assistant Backend",
        "environment": settings.ENVIRONMENT,
        "mock_fallback_enabled": settings.ENABLE_MOCK_FALLBACK,
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "atlassian_oauth_configured": bool(settings.ATLASSIAN_CLIENT_ID)
    }

@app.get("/", summary="Root index")
async def root():
    return {
        "message": "Welcome to Jira AI Assistant API. Access /docs for interactive Swagger UI."
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or "An internal server error occurred."}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
