import logging
from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from typing import Optional

from config import settings
from models.schemas import AuthStatus
from services.oauth_service import oauth_service

logger = logging.getLogger("jira_assistant.routes.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/login", summary="Initiate Atlassian Jira OAuth 2.0 (3LO) flow")
async def login(session_id: str = Query(default="default_user")):
    """
    Redirects the user to Atlassian OAuth 2.0 authorization page.
    If ATLASSIAN_CLIENT_ID is not set, enables mock demo session.
    """
    if not settings.ATLASSIAN_CLIENT_ID:
        oauth_service.enable_mock_session(session_id)
        return RedirectResponse(url=f"{settings.FRONTEND_URL}?mock_auth_success=true")

    auth_url = oauth_service.get_authorization_url(session_id=session_id)
    return RedirectResponse(url=auth_url)

@router.get("/callback", summary="Atlassian OAuth 2.0 redirect callback")
async def oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query("default_user"),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None)
):
    """
    Receives authorization code from Atlassian, exchanges for access/refresh tokens,
    retrieves accessible Jira Cloud sites, and securely saves session.
    """
    if error:
        logger.error(f"OAuth error from Atlassian: {error} - {error_description}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}?error={error}&msg={error_description}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code in OAuth callback")

    try:
        session_id = state or "default_user"
        await oauth_service.exchange_code_for_token(code=code, session_id=session_id)
        return RedirectResponse(url=f"{settings.FRONTEND_URL}?auth_success=true")
    except Exception as e:
        logger.error(f"Error handling OAuth callback: {e}", exc_info=True)
        return RedirectResponse(url=f"{settings.FRONTEND_URL}?auth_error={str(e)}")

@router.get("/status", response_model=AuthStatus, summary="Get Jira connection and user auth status")
async def get_status(session_id: str = Query(default="default_user")):
    """
    Check if the user is authenticated with Jira Cloud or in Mock Demo Mode.
    Never exposes access tokens to frontend.
    """
    return oauth_service.get_auth_status(session_id=session_id)

@router.post("/logout", summary="Disconnect Jira Cloud session")
async def logout(session_id: str = Query(default="default_user")):
    """
    Logs out the user and clears stored Jira access tokens and pending actions.
    """
    oauth_service.logout_session(session_id=session_id)
    return {"status": "success", "message": "Successfully logged out of Jira"}

@router.post("/demo-mode", summary="Toggle or enable demo mock mode")
async def enable_demo_mode(session_id: str = Query(default="default_user")):
    """
    Enables interactive high-fidelity Jira mock mode for instant testing without OAuth keys.
    """
    oauth_service.enable_mock_session(session_id=session_id)
    return oauth_service.get_auth_status(session_id=session_id)
