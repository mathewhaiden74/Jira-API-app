import logging
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any

from models.schemas import ChatRequest, ChatResponse, ConfirmActionRequest
from services.ai_service import AIService

logger = logging.getLogger("jira_assistant.routes.chat")
router = APIRouter(prefix="/chat", tags=["AI Chat & Natural Language"])

@router.post("/message", response_model=ChatResponse, summary="Send natural language prompt to Jira AI Assistant")
async def chat_message(payload: ChatRequest):
    """
    Main conversational endpoint:
    Processes user input -> classifies intent -> queries Jira API or requests safe confirmation -> returns synthesized response.
    """
    try:
        session_id = payload.session_id or "default_user"
        ai_service = AIService(session_id=session_id)
        return await ai_service.process_user_message(
            user_message=payload.message,
            project_context=payload.project_context
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/confirm", response_model=ChatResponse, summary="Confirm or cancel a pending Jira write action")
async def confirm_action(payload: ConfirmActionRequest):
    """
    User safety gate:
    Confirms and executes (or cancels) a write/modifying action against Jira Cloud.
    """
    try:
        session_id = payload.session_id or "default_user"
        ai_service = AIService(session_id=session_id)
        return await ai_service.execute_confirmed_action(
            action_id=payload.action_id,
            confirmed=payload.confirmed
        )
    except Exception as e:
        logger.error(f"Error executing confirmed action: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/examples", summary="Get suggested starter prompts")
async def get_example_prompts():
    """
    Returns curated quick-start prompts for user interaction.
    """
    return {
        "categories": [
            {
                "category": "Query & Search",
                "prompts": [
                    "Show me all open bugs.",
                    "Show P0 and P1 bugs assigned to me.",
                    "Summarize the latest bugs.",
                    "Show PROJ-123"
                ]
            },
            {
                "category": "Issue Management (Safe Confirmation)",
                "prompts": [
                    "Create a bug for Microsoft OAuth login failure.",
                    "Update the priority of PROJ-123 to High.",
                    "Move PROJ-123 to In Progress.",
                    "Assign PROJ-123 to Mathew.",
                    "Add a comment to PROJ-123 saying root cause is identified."
                ]
            },
            {
                "category": "AI QA & Analytics",
                "prompts": [
                    "Generate test cases for PROJ-125.",
                    "Find duplicate or similar bugs for PROJ-123.",
                    "Analyze bugs from this sprint.",
                    "Give me a summary of this sprint."
                ]
            }
        ]
    }
