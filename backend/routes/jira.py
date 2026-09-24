import logging
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List, Dict, Any

from models.schemas import (
    JiraIssue, JiraProject, JiraUser, JiraComment, 
    JiraSprint, JiraIssueType, JiraPriority
)
from services.jira_service import JiraService

logger = logging.getLogger("jira_assistant.routes.jira")
router = APIRouter(prefix="/jira", tags=["Jira Operations"])

@router.get("/myself", response_model=JiraUser, summary="Get current Jira user profile")
async def get_myself(session_id: str = Query(default="default_user")):
    try:
        service = JiraService(session_id=session_id)
        return await service.get_current_user()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/projects", response_model=List[JiraProject], summary="Get Jira projects")
async def get_projects(session_id: str = Query(default="default_user")):
    try:
        service = JiraService(session_id=session_id)
        return await service.get_projects()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/issues", response_model=List[JiraIssue], summary="Search Jira issues using JQL")
async def search_issues(
    jql: str = Query(..., description="JQL search query"),
    max_results: int = Query(default=50, le=100),
    session_id: str = Query(default="default_user")
):
    try:
        service = JiraService(session_id=session_id)
        return await service.search_issues(jql=jql, max_results=max_results)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/issues/{issue_key}", response_model=JiraIssue, summary="Get single Jira issue")
async def get_issue(issue_key: str, session_id: str = Query(default="default_user")):
    try:
        service = JiraService(session_id=session_id)
        return await service.get_issue(issue_key=issue_key)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/issues", response_model=JiraIssue, summary="Create new Jira issue")
async def create_issue(
    payload: Dict[str, Any] = Body(...),
    session_id: str = Query(default="default_user")
):
    try:
        service = JiraService(session_id=session_id)
        return await service.create_issue(
            project_key=payload.get("project_key", "PROJ"),
            summary=payload.get("summary", "New Issue"),
            issue_type=payload.get("issue_type", "Bug"),
            description=payload.get("description", ""),
            priority=payload.get("priority", "Medium"),
            components=payload.get("components"),
            labels=payload.get("labels")
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/issues/{issue_key}", response_model=JiraIssue, summary="Update Jira issue")
async def update_issue(
    issue_key: str,
    payload: Dict[str, Any] = Body(...),
    session_id: str = Query(default="default_user")
):
    try:
        service = JiraService(session_id=session_id)
        return await service.update_issue(issue_key=issue_key, fields=payload.get("fields", payload))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/issues/{issue_key}/transitions", response_model=JiraIssue, summary="Transition Jira issue status")
async def transition_issue(
    issue_key: str,
    payload: Dict[str, Any] = Body(...),
    session_id: str = Query(default="default_user")
):
    try:
        service = JiraService(session_id=session_id)
        status_name = payload.get("status") or payload.get("transition_id")
        if not status_name:
            raise HTTPException(status_code=400, detail="Missing 'status' in request body")
        return await service.transition_issue(issue_key=issue_key, transition_name_or_id=status_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/issues/{issue_key}/assignee", response_model=JiraIssue, summary="Assign Jira issue")
async def assign_issue(
    issue_key: str,
    payload: Dict[str, Any] = Body(...),
    session_id: str = Query(default="default_user")
):
    try:
        service = JiraService(session_id=session_id)
        assignee = payload.get("assignee") or payload.get("accountId")
        if not assignee:
            raise HTTPException(status_code=400, detail="Missing 'assignee' in request body")
        return await service.assign_issue(issue_key=issue_key, account_id_or_name=assignee)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/issues/{issue_key}/comment", response_model=JiraComment, summary="Add comment to Jira issue")
async def add_comment(
    issue_key: str,
    payload: Dict[str, Any] = Body(...),
    session_id: str = Query(default="default_user")
):
    try:
        service = JiraService(session_id=session_id)
        body = payload.get("body", "")
        if not body:
            raise HTTPException(status_code=400, detail="Missing 'body' in comment request")
        return await service.add_comment(issue_key=issue_key, body=body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/issues/{issue_key}/comment", response_model=List[JiraComment], summary="Get issue comments")
async def get_comments(issue_key: str, session_id: str = Query(default="default_user")):
    try:
        service = JiraService(session_id=session_id)
        return await service.get_issue_comments(issue_key=issue_key)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sprints", response_model=List[JiraSprint], summary="Get active sprints")
async def get_sprints(project_key: Optional[str] = None, session_id: str = Query(default="default_user")):
    try:
        service = JiraService(session_id=session_id)
        return await service.get_sprints(project_key=project_key)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/issue-types", response_model=List[JiraIssueType], summary="Get issue types")
async def get_issue_types(session_id: str = Query(default="default_user")):
    try:
        service = JiraService(session_id=session_id)
        return await service.get_issue_types()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/priorities", response_model=List[JiraPriority], summary="Get issue priorities")
async def get_priorities(session_id: str = Query(default="default_user")):
    try:
        service = JiraService(session_id=session_id)
        return await service.get_priorities()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
