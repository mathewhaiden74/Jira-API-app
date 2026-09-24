from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class JiraUser(BaseModel):
    accountId: Optional[str] = None
    displayName: Optional[str] = "Unassigned"
    emailAddress: Optional[str] = None
    avatarUrl: Optional[str] = None
    active: bool = True

class JiraProject(BaseModel):
    id: str
    key: str
    name: str
    projectTypeKey: Optional[str] = None
    avatarUrl: Optional[str] = None

class JiraStatus(BaseModel):
    id: Optional[str] = None
    name: str
    category: Optional[str] = "indeterminate" # new, indeterminate, done

class JiraPriority(BaseModel):
    id: Optional[str] = None
    name: str
    iconUrl: Optional[str] = None

class JiraIssueType(BaseModel):
    id: Optional[str] = None
    name: str
    iconUrl: Optional[str] = None
    subtask: bool = False

class JiraComment(BaseModel):
    id: Optional[str] = None
    author: Optional[JiraUser] = None
    body: str
    created: Optional[str] = None
    updated: Optional[str] = None

class JiraSprint(BaseModel):
    id: int
    name: str
    state: str # active, closed, future
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    goal: Optional[str] = None

class JiraIssue(BaseModel):
    id: Optional[str] = None
    key: str
    summary: str
    description: Optional[str] = ""
    status: JiraStatus
    priority: JiraPriority
    issue_type: JiraIssueType
    assignee: Optional[JiraUser] = None
    reporter: Optional[JiraUser] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    sprint: Optional[str] = None
    project_key: Optional[str] = None
    components: List[str] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)
    url: Optional[str] = None

class TestCase(BaseModel):
    id: str
    title: str
    priority: str
    type: str # Functional, Negative, Security, Performance, Regression, Boundary
    preconditions: Optional[str] = ""
    steps: List[str]
    test_data: Optional[str] = ""
    expected_result: str

class TestCaseGenerationResult(BaseModel):
    issue_key: str
    issue_summary: str
    test_cases: List[TestCase]

class BugAnalysisResult(BaseModel):
    total_bugs: int = 0
    open_bugs: int = 0
    in_progress_bugs: int = 0
    resolved_bugs: int = 0
    highest_priority_count: int = 0
    bugs_by_assignee: Dict[str, int] = Field(default_factory=dict)
    bugs_by_status: Dict[str, int] = Field(default_factory=dict)
    bugs_by_component: Dict[str, int] = Field(default_factory=dict)
    bugs_by_priority: Dict[str, int] = Field(default_factory=dict)
    summary_text: str

class DuplicateCandidate(BaseModel):
    issue_key: str
    summary: str
    status: str
    priority: str
    similarity_score: int # 0-100
    similarity_reason: str
    matching_symptoms: List[str] = Field(default_factory=list)
    matching_component: Optional[str] = None
    possible_duplicate_explanation: str

class DuplicateAnalysisResult(BaseModel):
    target_issue_key: str
    target_summary: str
    candidates: List[DuplicateCandidate] = Field(default_factory=list)
    conclusion: str

class PendingAction(BaseModel):
    action_id: str
    action: str # CREATE_ISSUE, UPDATE_ISSUE, ASSIGN_ISSUE, TRANSITION_ISSUE, ADD_COMMENT
    issue_key: Optional[str] = None
    summary_text: str
    parameters: Dict[str, Any]
    expires_at: Optional[float] = None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default_user"
    project_context: Optional[str] = None

class ChatResponse(BaseModel):
    role: str = "assistant"
    message: str
    action: Optional[str] = None
    issues: Optional[List[JiraIssue]] = None
    confirmation_required: bool = False
    pending_action: Optional[PendingAction] = None
    test_cases: Optional[List[TestCase]] = None
    bug_analysis: Optional[BugAnalysisResult] = None
    duplicate_analysis: Optional[DuplicateAnalysisResult] = None
    timestamp: str

class ConfirmActionRequest(BaseModel):
    action_id: str
    confirmed: bool
    session_id: Optional[str] = "default_user"
    modified_parameters: Optional[Dict[str, Any]] = None

class AuthStatus(BaseModel):
    is_authenticated: bool
    is_mock_mode: bool
    user: Optional[JiraUser] = None
    site_name: Optional[str] = None
    site_url: Optional[str] = None
    cloud_id: Optional[str] = None
    available_sites: List[Dict[str, Any]] = Field(default_factory=list)
    message: Optional[str] = None
