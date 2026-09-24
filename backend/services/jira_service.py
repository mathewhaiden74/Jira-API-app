import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from config import settings
from models.schemas import (
    JiraIssue, JiraProject, JiraUser, JiraStatus, JiraPriority, 
    JiraIssueType, JiraComment, JiraSprint
)
from services.oauth_service import oauth_service

logger = logging.getLogger("jira_assistant.jira")

class JiraService:
    def __init__(self, session_id: str = "default_user"):
        self.session_id = session_id

    async def _get_auth_headers_and_base_url(self):
        """Helper to get access token and Jira base URL for the active session."""
        session = oauth_service.get_session(self.session_id)
        if not session:
            # Check if mock fallback
            if settings.ENABLE_MOCK_FALLBACK:
                oauth_service.enable_mock_session(self.session_id)
                session = oauth_service.get_session(self.session_id)
            else:
                raise Exception("Authentication required: Please log in to Jira Cloud.")

        is_mock = bool(session.get("is_mock"))
        if is_mock:
            return None, None, True

        token = await oauth_service.refresh_access_token_if_needed(self.session_id)
        if not token:
            token = session.get("access_token")

        cloud_id = session.get("cloud_id")
        if not token or not cloud_id:
            raise Exception("Your Jira authorization is missing or expired. Please reconnect your Jira account.")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        base_url = f"https://api.atlassian.com/ex/jira/{cloud_id}"
        return headers, base_url, False

    def _convert_text_to_adf(self, text: str) -> Dict[str, Any]:
        """Convert plain text into Atlassian Document Format (ADF) for Jira v3 API."""
        if not text:
            return {
                "type": "doc",
                "version": 1,
                "content": []
            }
        paragraphs = text.split("\n")
        content = []
        for p in paragraphs:
            if p.strip():
                content.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": p}]
                })
        return {
            "type": "doc",
            "version": 1,
            "content": content if content else [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]
        }

    def _extract_adf_text(self, adf: Any) -> str:
        """Extract plain text from Atlassian Document Format (ADF)."""
        if not adf:
            return ""
        if isinstance(adf, str):
            return adf
        if isinstance(adf, dict):
            text_parts = []
            if adf.get("type") == "text":
                return adf.get("text", "")
            for child in adf.get("content", []):
                child_text = self._extract_adf_text(child)
                if child_text:
                    text_parts.append(child_text)
            return "\n".join(text_parts) if adf.get("type") == "doc" else " ".join(text_parts)
        return ""

    def _parse_jira_issue_json(self, item: Dict[str, Any], site_url: str = "") -> JiraIssue:
        """Parse raw Jira REST API v3 issue JSON to JiraIssue model."""
        fields = item.get("fields", {})
        status_field = fields.get("status") or {}
        status_category = status_field.get("statusCategory", {}).get("key", "indeterminate")
        
        priority_field = fields.get("priority") or {}
        issuetype_field = fields.get("issuetype") or {}
        assignee_field = fields.get("assignee")
        reporter_field = fields.get("reporter")
        project_field = fields.get("project") or {}
        
        components = [c.get("name") for c in fields.get("components", []) if isinstance(c, dict)]
        labels = fields.get("labels", [])

        # Sprint parsing
        sprint_name = None
        sprint_field = fields.get("sprint") or fields.get("customfield_10020")
        if isinstance(sprint_field, dict):
            sprint_name = sprint_field.get("name")
        elif isinstance(sprint_field, list) and len(sprint_field) > 0:
            if isinstance(sprint_field[-1], dict):
                sprint_name = sprint_field[-1].get("name")
            else:
                sprint_name = str(sprint_field[-1])

        # Issue URL
        key = item.get("key", "")
        issue_url = f"{site_url.rstrip('/')}/browse/{key}" if site_url else f"https://jira.atlassian.com/browse/{key}"

        return JiraIssue(
            id=item.get("id"),
            key=key,
            summary=fields.get("summary", "No summary"),
            description=self._extract_adf_text(fields.get("description")),
            status=JiraStatus(
                id=status_field.get("id"),
                name=status_field.get("name", "Open"),
                category=status_category
            ),
            priority=JiraPriority(
                id=priority_field.get("id"),
                name=priority_field.get("name", "Medium"),
                iconUrl=priority_field.get("iconUrl")
            ),
            issue_type=JiraIssueType(
                id=issuetype_field.get("id"),
                name=issuetype_field.get("name", "Task"),
                iconUrl=issuetype_field.get("iconUrl"),
                subtask=issuetype_field.get("subtask", False)
            ),
            assignee=JiraUser(
                accountId=assignee_field.get("accountId"),
                displayName=assignee_field.get("displayName"),
                emailAddress=assignee_field.get("emailAddress"),
                avatarUrl=assignee_field.get("avatarUrls", {}).get("48x48") if assignee_field else None
            ) if assignee_field else None,
            reporter=JiraUser(
                accountId=reporter_field.get("accountId"),
                displayName=reporter_field.get("displayName"),
                emailAddress=reporter_field.get("emailAddress"),
                avatarUrl=reporter_field.get("avatarUrls", {}).get("48x48") if reporter_field else None
            ) if reporter_field else None,
            created=fields.get("created"),
            updated=fields.get("updated"),
            sprint=sprint_name,
            project_key=project_field.get("key"),
            components=components,
            labels=labels,
            url=issue_url
        )

    # --- JIRA API METHODS ---

    async def get_current_user(self) -> JiraUser:
        """Get the authenticated Jira user profile."""
        headers, base_url, is_mock = await self._get_auth_headers_and_base_url()
        if is_mock:
            return MockJiraDatabase.get_current_user()

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{base_url}/rest/api/3/myself", headers=headers)
            if resp.status_code != 200:
                self._handle_http_error(resp)
            data = resp.json()
            return JiraUser(
                accountId=data.get("accountId"),
                displayName=data.get("displayName", "Jira User"),
                emailAddress=data.get("emailAddress"),
                avatarUrl=data.get("avatarUrls", {}).get("48x48")
            )

    async def get_projects(self) -> List[JiraProject]:
        """Get list of visible projects in the Jira Cloud site."""
        headers, base_url, is_mock = await self._get_auth_headers_and_base_url()
        if is_mock:
            return MockJiraDatabase.get_projects()

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{base_url}/rest/api/3/project", headers=headers)
            if resp.status_code != 200:
                self._handle_http_error(resp)
            data = resp.json()
            return [
                JiraProject(
                    id=p.get("id"),
                    key=p.get("key"),
                    name=p.get("name"),
                    projectTypeKey=p.get("projectTypeKey"),
                    avatarUrl=p.get("avatarUrls", {}).get("48x48")
                )
                for p in data
            ]

    async def get_project(self, project_key: str) -> JiraProject:
        """Get specific project details."""
        headers, base_url, is_mock = await self._get_auth_headers_and_base_url()
        if is_mock:
            proj = MockJiraDatabase.get_project(project_key)
            if not proj:
                raise Exception(f"Project '{project_key}' not found in Jira.")
            return proj

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{base_url}/rest/api/3/project/{project_key}", headers=headers)
            if resp.status_code != 200:
                self._handle_http_error(resp, item_name=f"Project {project_key}")
            p = resp.json()
            return JiraProject(
                id=p.get("id"),
                key=p.get("key"),
                name=p.get("name"),
                projectTypeKey=p.get("projectTypeKey"),
                avatarUrl=p.get("avatarUrls", {}).get("48x48")
            )

    async def search_issues(self, jql: str, max_results: int = 50, fields: Optional[List[str]] = None) -> List[JiraIssue]:
        """Search Jira issues using JQL."""
        headers, base_url, is_mock = await self._get_auth_headers_and_base_url()
        if is_mock:
            return MockJiraDatabase.search_issues(jql, max_results=max_results)

        session = oauth_service.get_session(self.session_id) or {}
        site_url = session.get("site_url", "")

        payload = {
            "jql": jql,
            "maxResults": max_results,
            "fields": fields or ["summary", "description", "status", "priority", "issuetype", "assignee", "reporter", "created", "updated", "components", "labels", "project", "customfield_10020", "sprint"]
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(f"{base_url}/rest/api/3/search/jql", headers=headers, json=payload)
            if resp.status_code != 200:
                self._handle_http_error(resp, context=f"JQL: '{jql}'")
            data = resp.json()
            issues_json = data.get("issues", [])
            return [self._parse_jira_issue_json(item, site_url) for item in issues_json]

    async def get_issue(self, issue_key: str) -> JiraIssue:
        """Fetch details of a single Jira issue."""
        headers, base_url, is_mock = await self._get_auth_headers_and_base_url()
        if is_mock:
            issue = MockJiraDatabase.get_issue(issue_key)
            if not issue:
                raise Exception(f"Issue '{issue_key}' does not exist or you do not have permission to view it.")
            return issue

        session = oauth_service.get_session(self.session_id) or {}
        site_url = session.get("site_url", "")

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{base_url}/rest/api/3/issue/{issue_key}", headers=headers)
            if resp.status_code != 200:
                self._handle_http_error(resp, item_name=f"Issue {issue_key}")
            return self._parse_jira_issue_json(resp.json(), site_url)

    async def create_issue(
        self,
        project_key: str,
        summary: str,
        issue_type: str = "Bug",
        description: str = "",
        priority: Optional[str] = "Medium",
        components: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        assignee_account_id: Optional[str] = None,
        parent_key: Optional[str] = None
    ) -> JiraIssue:
        """Create a new Jira issue, Subtask, or Epic."""
        headers, base_url, is_mock = await self._get_auth_headers_and_base_url()
        if is_mock:
            return MockJiraDatabase.create_issue(
                project_key=project_key,
                summary=summary,
                issue_type=issue_type,
                description=description,
                priority=priority,
                components=components,
                labels=labels,
                assignee_name="Mathew Thomas" if not assignee_account_id else assignee_account_id,
                parent_key=parent_key
            )

        # Normalize issue type names
        norm_type = issue_type.strip()
        is_subtask = norm_type.lower() in ["subtask", "sub-task", "sub task"] or bool(parent_key)

        # If parent key is provided, deduce project_key from parent key if needed
        if parent_key and "-" in parent_key:
            parent_key = parent_key.strip().upper()
            if not project_key or project_key == "PROJ":
                project_key = parent_key.split("-")[0]

        target_issue_type = norm_type
        if is_subtask:
            target_issue_type = "Subtask"
        elif norm_type.lower() == "epic":
            target_issue_type = "Epic"

        fields: Dict[str, Any] = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": target_issue_type},
            "description": self._convert_text_to_adf(description)
        }

        if is_subtask and parent_key:
            fields["parent"] = {"key": parent_key}

        if priority:
            fields["priority"] = {"name": priority}
        if components:
            fields["components"] = [{"name": c} for c in components]
        if labels:
            fields["labels"] = labels
        if assignee_account_id:
            fields["assignee"] = {"accountId": assignee_account_id}

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(f"{base_url}/rest/api/3/issue", headers=headers, json={"fields": fields})
            
            # If Subtask failed due to naming difference ("Sub-task" vs "Subtask"), retry with alternate name
            if resp.status_code not in (200, 201) and is_subtask:
                alternate_type = "Sub-task" if target_issue_type == "Subtask" else "Subtask"
                fields["issuetype"] = {"name": alternate_type}
                resp = await client.post(f"{base_url}/rest/api/3/issue", headers=headers, json={"fields": fields})

            if resp.status_code not in (200, 201):
                self._handle_http_error(resp, context=f"creating {target_issue_type}")
            created_data = resp.json()
            new_key = created_data.get("key")
            return await self.get_issue(new_key)

    async def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> JiraIssue:
        """Update fields of an existing Jira issue."""
        headers, base_url, is_mock = await self._get_auth_headers_and_base_url()
        if is_mock:
            return MockJiraDatabase.update_issue(issue_key, fields)

        # Convert simple fields to Jira v3 format if necessary
        formatted_fields: Dict[str, Any] = {}
        for k, v in fields.items():
            if k == "summary":
                formatted_fields["summary"] = v
            elif k == "description":
                formatted_fields["description"] = self._convert_text_to_adf(v)
            elif k == "priority":
                formatted_fields["priority"] = {"name": v} if isinstance(v, str) else v
            elif k == "labels":
                formatted_fields["labels"] = v
            else:
                formatted_fields[k] = v

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.put(f"{base_url}/rest/api/3/issue/{issue_key}", headers=headers, json={"fields": formatted_fields})
            if resp.status_code not in (200, 204):
                self._handle_http_error(resp, item_name=f"Updating {issue_key}")
            return await self.get_issue(issue_key)

    async def transition_issue(self, issue_key: str, transition_name_or_id: str) -> JiraIssue:
        """Transition Jira issue status (e.g. 'In Progress', 'Done', 'To Do')."""
        headers, base_url, is_mock = await self._get_auth_headers_and_base_url()
        if is_mock:
            return MockJiraDatabase.transition_issue(issue_key, transition_name_or_id)

        async with httpx.AsyncClient(timeout=15.0) as client:
            # First fetch available transitions for this issue
            trans_resp = await client.get(f"{base_url}/rest/api/3/issue/{issue_key}/transitions", headers=headers)
            if trans_resp.status_code != 200:
                self._handle_http_error(trans_resp, item_name=f"Transitions for {issue_key}")
            
            transitions = trans_resp.json().get("transitions", [])
            target_id = None
            for t in transitions:
                if t.get("id") == transition_name_or_id or t.get("name", "").lower() == transition_name_or_id.lower():
                    target_id = t.get("id")
                    break
            
            if not target_id:
                available = ", ".join([f"'{t.get('name')}'" for t in transitions])
                raise Exception(f"Cannot transition '{issue_key}' to '{transition_name_or_id}'. Available transitions are: {available or 'None'}")

            payload = {"transition": {"id": target_id}}
            resp = await client.post(f"{base_url}/rest/api/3/issue/{issue_key}/transitions", headers=headers, json=payload)
            if resp.status_code not in (200, 204):
                self._handle_http_error(resp, item_name=f"Transitioning {issue_key}")

            return await self.get_issue(issue_key)

    async def assign_issue(self, issue_key: str, account_id_or_name: str) -> JiraIssue:
        """Assign Jira issue to a user."""
        headers, base_url, is_mock = await self._get_auth_headers_and_base_url()
        if is_mock:
            return MockJiraDatabase.assign_issue(issue_key, account_id_or_name)

        async with httpx.AsyncClient(timeout=15.0) as client:
            payload = {"accountId": account_id_or_name if account_id_or_name != "-1" else None}
            resp = await client.put(f"{base_url}/rest/api/3/issue/{issue_key}/assignee", headers=headers, json=payload)
            if resp.status_code not in (200, 204):
                self._handle_http_error(resp, item_name=f"Assigning {issue_key}")

            return await self.get_issue(issue_key)

    async def add_comment(self, issue_key: str, body: str) -> JiraComment:
        """Add a comment to an issue."""
        headers, base_url, is_mock = await self._get_auth_headers_and_base_url()
        if is_mock:
            return MockJiraDatabase.add_comment(issue_key, body)

        payload = {"body": self._convert_text_to_adf(body)}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(f"{base_url}/rest/api/3/issue/{issue_key}/comment", headers=headers, json=payload)
            if resp.status_code not in (200, 201):
                self._handle_http_error(resp, item_name=f"Adding comment to {issue_key}")
            c = resp.json()
            author = c.get("author") or {}
            return JiraComment(
                id=c.get("id"),
                author=JiraUser(
                    accountId=author.get("accountId"),
                    displayName=author.get("displayName", "User"),
                    emailAddress=author.get("emailAddress"),
                    avatarUrl=author.get("avatarUrls", {}).get("48x48")
                ),
                body=self._extract_adf_text(c.get("body")),
                created=c.get("created"),
                updated=c.get("updated")
            )

    async def get_issue_comments(self, issue_key: str) -> List[JiraComment]:
        """Get all comments for an issue."""
        headers, base_url, is_mock = await self._get_auth_headers_and_base_url()
        if is_mock:
            return MockJiraDatabase.get_issue_comments(issue_key)

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{base_url}/rest/api/3/issue/{issue_key}/comment", headers=headers)
            if resp.status_code != 200:
                self._handle_http_error(resp, item_name=f"Comments for {issue_key}")
            comments_json = resp.json().get("comments", [])
            return [
                JiraComment(
                    id=c.get("id"),
                    author=JiraUser(
                        accountId=c.get("author", {}).get("accountId"),
                        displayName=c.get("author", {}).get("displayName", "User"),
                        emailAddress=c.get("author", {}).get("emailAddress"),
                        avatarUrl=c.get("author", {}).get("avatarUrls", {}).get("48x48")
                    ),
                    body=self._extract_adf_text(c.get("body")),
                    created=c.get("created"),
                    updated=c.get("updated")
                )
                for c in comments_json
            ]

    async def get_sprints(self, board_id: Optional[int] = None, project_key: Optional[str] = None) -> List[JiraSprint]:
        """Fetch active/recent sprints using Jira Agile API."""
        headers, base_url, is_mock = await self._get_auth_headers_and_base_url()
        if is_mock:
            return MockJiraDatabase.get_sprints()

        async with httpx.AsyncClient(timeout=15.0) as client:
            # If board_id is not given, find board first
            if not board_id:
                boards_resp = await client.get(f"{base_url}/rest/agile/1.0/board", headers=headers)
                if boards_resp.status_code == 200:
                    boards = boards_resp.json().get("values", [])
                    if boards:
                        board_id = boards[0].get("id")

            if not board_id:
                return []

            resp = await client.get(f"{base_url}/rest/agile/1.0/board/{board_id}/sprint", headers=headers)
            if resp.status_code != 200:
                return []
            sprints_data = resp.json().get("values", [])
            return [
                JiraSprint(
                    id=s.get("id"),
                    name=s.get("name"),
                    state=s.get("state", "active"),
                    startDate=s.get("startDate"),
                    endDate=s.get("endDate"),
                    goal=s.get("goal")
                )
                for s in sprints_data
            ]

    async def get_sprint_issues(self, sprint_id: int) -> List[JiraIssue]:
        """Get issues in a specific sprint."""
        headers, base_url, is_mock = await self._get_auth_headers_and_base_url()
        if is_mock:
            return MockJiraDatabase.get_sprint_issues(sprint_id)

        session = oauth_service.get_session(self.session_id) or {}
        site_url = session.get("site_url", "")

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{base_url}/rest/agile/1.0/sprint/{sprint_id}/issue", headers=headers)
            if resp.status_code != 200:
                self._handle_http_error(resp, item_name=f"Sprint {sprint_id} issues")
            data = resp.json()
            return [self._parse_jira_issue_json(item, site_url) for item in data.get("issues", [])]

    async def get_issue_types(self) -> List[JiraIssueType]:
        """Get available issue types."""
        headers, base_url, is_mock = await self._get_auth_headers_and_base_url()
        if is_mock:
            return MockJiraDatabase.get_issue_types()

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{base_url}/rest/api/3/issuetype", headers=headers)
            if resp.status_code != 200:
                self._handle_http_error(resp)
            return [
                JiraIssueType(
                    id=it.get("id"),
                    name=it.get("name"),
                    iconUrl=it.get("iconUrl"),
                    subtask=it.get("subtask", False)
                )
                for it in resp.json()
            ]

    async def get_priorities(self) -> List[JiraPriority]:
        """Get available issue priorities."""
        headers, base_url, is_mock = await self._get_auth_headers_and_base_url()
        if is_mock:
            return MockJiraDatabase.get_priorities()

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{base_url}/rest/api/3/priority", headers=headers)
            if resp.status_code != 200:
                self._handle_http_error(resp)
            return [
                JiraPriority(
                    id=p.get("id"),
                    name=p.get("name"),
                    iconUrl=p.get("iconUrl")
                )
                for p in resp.json()
            ]

    def _handle_http_error(self, response: httpx.Response, item_name: str = "Resource", context: str = ""):
        """Handle Jira REST API HTTP error codes gracefully."""
        status = response.status_code
        logger.error(f"Jira API Error {status}: {response.text} | Context: {context}")
        
        try:
            err_json = response.json()
            err_msgs = err_json.get("errorMessages", [])
            errors_dict = err_json.get("errors", {})
            detailed = " ".join(err_msgs) if err_msgs else " ".join([f"{k}: {v}" for k, v in errors_dict.items()])
        except Exception:
            detailed = response.text[:200]

        if status == 401:
            raise Exception("Your Jira authorization has expired or is invalid. Please reconnect your Jira account.")
        elif status == 403:
            raise Exception(f"Permission denied by Jira for {item_name}. Ensure your Atlassian account has sufficient project permissions.")
        elif status == 404:
            raise Exception(f"{item_name} was not found on Jira Cloud. Please check the key or identifier.")
        elif status == 429:
            raise Exception("Jira API rate limit reached. Please wait a moment before trying again.")
        elif status == 400:
            raise Exception(f"Invalid Jira request: {detailed or 'Check your input or JQL syntax.'}")
        elif status >= 500:
            raise Exception(f"Jira Cloud encountered a temporary server error ({status}). Please retry shortly.")
        else:
            raise Exception(f"Jira API error ({status}): {detailed or 'Unexpected error'}")


# --- MOCK JIRA STORE FOR DEMO & TESTING ---

class MockJiraDatabase:
    """Provides high-fidelity mock Jira data when testing without live OAuth credentials."""
    _projects = [
        JiraProject(id="10001", key="PROJ", name="Cloud Platform & Core Services", projectTypeKey="software", avatarUrl="https://cdn.iconscout.com/icon/free/png-256/free-jira-3628859-3030006.png"),
        JiraProject(id="10002", key="AUTH", name="Identity & Access Management", projectTypeKey="software", avatarUrl="https://cdn.iconscout.com/icon/free/png-256/free-jira-3628859-3030006.png"),
        JiraProject(id="10003", key="PAY", name="Billing & Payments Service", projectTypeKey="software", avatarUrl="https://cdn.iconscout.com/icon/free/png-256/free-jira-3628859-3030006.png")
    ]

    _users = {
        "mathew": JiraUser(accountId="usr-demo-789", displayName="Mathew Thomas", emailAddress="mathew@acme-software.com", avatarUrl="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80"),
        "sarah": JiraUser(accountId="usr-sarah-102", displayName="Sarah Connor", emailAddress="sarah@acme-software.com", avatarUrl="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&auto=format&fit=crop&q=80"),
        "alex": JiraUser(accountId="usr-alex-103", displayName="Alex Rivera", emailAddress="alex@acme-software.com", avatarUrl="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80")
    }

    _sprints = [
        JiraSprint(id=42, name="Sprint 24 - Q3 Core Hardening", state="active", startDate="2026-09-15T09:00:00Z", endDate="2026-09-29T18:00:00Z", goal="Stabilize Microsoft OAuth flow and resolve critical payment gateway timeouts.")
    ]

    _issues: Dict[str, JiraIssue] = {}

    @classmethod
    def _initialize_mock_data(cls):
        if cls._issues:
            return
        
        now_str = datetime.now(timezone.utc).isoformat()
        
        demo_issues = [
            JiraIssue(
                id="10101",
                key="PROJ-123",
                summary="Microsoft OAuth 2.0 login failure with PKCE on iOS Safari",
                description="Users attempting to authenticate via Microsoft Azure AD on mobile Safari receive error 400 'invalid_grant' after redirect callback.",
                status=JiraStatus(id="1", name="In Progress", category="indeterminate"),
                priority=JiraPriority(id="1", name="P0", iconUrl=""),
                issue_type=JiraIssueType(id="1", name="Bug"),
                assignee=cls._users["mathew"],
                reporter=cls._users["sarah"],
                created="2026-09-20T10:30:00Z",
                updated=now_str,
                sprint="Sprint 24 - Q3 Core Hardening",
                project_key="PROJ",
                components=["Authentication", "Mobile Web"],
                labels=["oauth", "p0", "ios", "security"],
                url="https://acme-engineering.atlassian.net/browse/PROJ-123"
            ),
            JiraIssue(
                id="10102",
                key="PROJ-124",
                summary="OAuth token refresh loop when session expires during checkout",
                description="Token refresh request results in infinite HTTP 401 retry cycle when customer checkout session is idle for > 15 minutes.",
                status=JiraStatus(id="2", name="Open", category="new"),
                priority=JiraPriority(id="2", name="P1", iconUrl=""),
                issue_type=JiraIssueType(id="1", name="Bug"),
                assignee=cls._users["mathew"],
                reporter=cls._users["alex"],
                created="2026-09-21T14:15:00Z",
                updated=now_str,
                sprint="Sprint 24 - Q3 Core Hardening",
                project_key="PROJ",
                components=["Authentication", "Checkout"],
                labels=["oauth", "p1", "token-refresh"],
                url="https://acme-engineering.atlassian.net/browse/PROJ-124"
            ),
            JiraIssue(
                id="10103",
                key="PROJ-125",
                summary="Implement Single Sign-On (SSO) SAML and Azure OAuth Requirement",
                description="As an Enterprise Admin, I want to enforce corporate SSO via Microsoft Azure AD and SAML 2.0 so that enterprise users can securely log in with MFA.",
                status=JiraStatus(id="3", name="In Review", category="indeterminate"),
                priority=JiraPriority(id="3", name="P2", iconUrl=""),
                issue_type=JiraIssueType(id="2", name="Story"),
                assignee=cls._users["sarah"],
                reporter=cls._users["mathew"],
                created="2026-09-18T08:00:00Z",
                updated=now_str,
                sprint="Sprint 24 - Q3 Core Hardening",
                project_key="PROJ",
                components=["Authentication", "Enterprise"],
                labels=["sso", "saml", "azure-ad"],
                url="https://acme-engineering.atlassian.net/browse/PROJ-125"
            ),
            JiraIssue(
                id="10104",
                key="PROJ-126",
                summary="Stripe payment webhook timeout under high concurrent load",
                description="During flash sales, Stripe webhook handler takes > 5000ms causing Stripe to retry webhooks and generate duplicate transaction records.",
                status=JiraStatus(id="2", name="Open", category="new"),
                priority=JiraPriority(id="1", name="P0", iconUrl=""),
                issue_type=JiraIssueType(id="1", name="Bug"),
                assignee=cls._users["alex"],
                reporter=cls._users["mathew"],
                created="2026-09-22T11:00:00Z",
                updated=now_str,
                sprint="Sprint 24 - Q3 Core Hardening",
                project_key="PROJ",
                components=["Billing", "Webhooks"],
                labels=["payments", "stripe", "p0", "scalability"],
                url="https://acme-engineering.atlassian.net/browse/PROJ-126"
            ),
            JiraIssue(
                id="10105",
                key="PROJ-127",
                summary="Database deadlocks during bulk Jira issue status sync",
                description="Simultaneous updates from multiple microservices cause row-lock contention on the issues table.",
                status=JiraStatus(id="4", name="Done", category="done"),
                priority=JiraPriority(id="2", name="P1", iconUrl=""),
                issue_type=JiraIssueType(id="1", name="Bug"),
                assignee=cls._users["mathew"],
                reporter=cls._users["alex"],
                created="2026-09-16T16:20:00Z",
                updated="2026-09-23T12:00:00Z",
                sprint="Sprint 24 - Q3 Core Hardening",
                project_key="PROJ",
                components=["Database", "Sync Engine"],
                labels=["db", "deadlock", "resolved"],
                url="https://acme-engineering.atlassian.net/browse/PROJ-127"
            ),
            JiraIssue(
                id="10106",
                key="AUTH-45",
                summary="Microsoft Azure AD login fails when state parameter contains special characters",
                description="Similar to PROJ-123, OAuth handshake breaks if state query parameter has unescaped characters during Azure AD redirect.",
                status=JiraStatus(id="2", name="Open", category="new"),
                priority=JiraPriority(id="2", name="P1", iconUrl=""),
                issue_type=JiraIssueType(id="1", name="Bug"),
                assignee=cls._users["sarah"],
                reporter=cls._users["sarah"],
                created="2026-09-19T09:10:00Z",
                updated=now_str,
                sprint="Sprint 24 - Q3 Core Hardening",
                project_key="AUTH",
                components=["Authentication"],
                labels=["oauth", "azure", "duplicate-candidate"],
                url="https://acme-engineering.atlassian.net/browse/AUTH-45"
            )
        ]

        for issue in demo_issues:
            cls._issues[issue.key] = issue

    @classmethod
    def get_current_user(cls) -> JiraUser:
        return cls._users["mathew"]

    @classmethod
    def get_projects(cls) -> List[JiraProject]:
        return cls._projects

    @classmethod
    def get_project(cls, key: str) -> Optional[JiraProject]:
        for p in cls._projects:
            if p.key.upper() == key.upper():
                return p
        return None

    @classmethod
    def search_issues(cls, jql: str, max_results: int = 50) -> List[JiraIssue]:
        cls._initialize_mock_data()
        jql_lower = jql.lower()
        results = list(cls._issues.values())

        # Filter by project
        if "project" in jql_lower:
            for p in cls._projects:
                if f"project = {p.key.lower()}" in jql_lower or f"project={p.key.lower()}" in jql_lower:
                    results = [i for i in results if i.project_key == p.key]

        # Filter by assignee
        if "currentuser()" in jql_lower or "mathew" in jql_lower:
            results = [i for i in results if i.assignee and "mathew" in i.assignee.displayName.lower()]

        # Filter by issuetype
        if "issuetype = bug" in jql_lower or "issuetype=bug" in jql_lower or "type = bug" in jql_lower:
            results = [i for i in results if i.issue_type.name.lower() == "bug"]
        elif "issuetype = story" in jql_lower:
            results = [i for i in results if i.issue_type.name.lower() == "story"]

        # Filter by status / statusCategory
        if "statuscategory != done" in jql_lower or "open" in jql_lower:
            results = [i for i in results if i.status.name.lower() != "done"]
        elif "status = done" in jql_lower:
            results = [i for i in results if i.status.name.lower() == "done"]

        # Filter by priority
        if "priority = p0" in jql_lower or "priority in (p0, p1)" in jql_lower or "priority in (highest, high)" in jql_lower:
            results = [i for i in results if i.priority.name in ["P0", "P1", "Highest", "High"]]
        elif "priority = p1" in jql_lower:
            results = [i for i in results if i.priority.name in ["P1", "High"]]
        elif "priority = high" in jql_lower or "highest" in jql_lower:
            results = [i for i in results if i.priority.name in ["P0", "P1", "Highest", "High"]]

        # Text search
        if "text ~" in jql_lower or "summary ~" in jql_lower:
            for word in ["oauth", "payment", "sso", "login", "stripe"]:
                if word in jql_lower:
                    results = [i for i in results if word in (i.summary + " " + (i.description or "")).lower()]

        return results[:max_results]

    @classmethod
    def get_issue(cls, key: str) -> Optional[JiraIssue]:
        cls._initialize_mock_data()
        return cls._issues.get(key.upper())

    @classmethod
    def create_issue(
        cls,
        project_key: str,
        summary: str,
        issue_type: str = "Bug",
        description: str = "",
        priority: Optional[str] = "Medium",
        components: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        assignee_name: Optional[str] = None,
        parent_key: Optional[str] = None
    ) -> JiraIssue:
        cls._initialize_mock_data()
        next_num = len(cls._issues) + 128
        new_key = f"{project_key.upper()}-{next_num}"
        
        assignee = cls._users.get("mathew") if assignee_name and "mathew" in assignee_name.lower() else cls._users["mathew"]
        is_sub = (issue_type or "").lower() in ["subtask", "sub-task"] or bool(parent_key)

        new_issue = JiraIssue(
            id=str(next_num + 10000),
            key=new_key,
            summary=summary,
            description=description,
            status=JiraStatus(id="1", name="Open", category="new"),
            priority=JiraPriority(id="2", name=priority or "Medium", iconUrl=""),
            issue_type=JiraIssueType(id="1", name=issue_type or "Bug", subtask=is_sub),
            assignee=assignee,
            reporter=cls._users["mathew"],
            created=datetime.now(timezone.utc).isoformat(),
            updated=datetime.now(timezone.utc).isoformat(),
            sprint="Sprint 24 - Q3 Core Hardening",
            project_key=project_key.upper(),
            components=components or ["Authentication"],
            labels=labels or ["ai-created"],
            url=f"https://acme-engineering.atlassian.net/browse/{new_key}"
        )
        cls._issues[new_key] = new_issue
        return new_issue

    @classmethod
    def update_issue(cls, key: str, fields: Dict[str, Any]) -> JiraIssue:
        cls._initialize_mock_data()
        issue = cls._issues.get(key.upper())
        if not issue:
            raise Exception(f"Issue {key} not found.")

        if "summary" in fields:
            issue.summary = fields["summary"]
        if "description" in fields:
            issue.description = fields["description"]
        if "priority" in fields:
            p_val = fields["priority"]
            p_name = p_val if isinstance(p_val, str) else p_val.get("name", "Medium")
            issue.priority = JiraPriority(id="2", name=p_name)
        if "labels" in fields:
            issue.labels = fields["labels"]

        issue.updated = datetime.now(timezone.utc).isoformat()
        cls._issues[key.upper()] = issue
        return issue

    @classmethod
    def transition_issue(cls, key: str, target_status: str) -> JiraIssue:
        cls._initialize_mock_data()
        issue = cls._issues.get(key.upper())
        if not issue:
            raise Exception(f"Issue {key} not found.")

        target = target_status.strip().title()
        if "progress" in target.lower():
            target = "In Progress"
            cat = "indeterminate"
        elif "done" in target.lower() or "close" in target.lower() or "resolve" in target.lower():
            target = "Done"
            cat = "done"
        else:
            target = "Open"
            cat = "new"

        issue.status = JiraStatus(id="1", name=target, category=cat)
        issue.updated = datetime.now(timezone.utc).isoformat()
        cls._issues[key.upper()] = issue
        return issue

    @classmethod
    def assign_issue(cls, key: str, user_query: str) -> JiraIssue:
        cls._initialize_mock_data()
        issue = cls._issues.get(key.upper())
        if not issue:
            raise Exception(f"Issue {key} not found.")

        if "mathew" in user_query.lower():
            issue.assignee = cls._users["mathew"]
        elif "sarah" in user_query.lower():
            issue.assignee = cls._users["sarah"]
        elif "alex" in user_query.lower():
            issue.assignee = cls._users["alex"]
        else:
            issue.assignee = JiraUser(accountId="usr-custom", displayName=user_query, emailAddress=f"{user_query.lower().replace(' ', '.')}@acme.com")

        issue.updated = datetime.now(timezone.utc).isoformat()
        cls._issues[key.upper()] = issue
        return issue

    @classmethod
    def add_comment(cls, key: str, body: str) -> JiraComment:
        return JiraComment(
            id=f"comment-{int(datetime.now().timestamp())}",
            author=cls._users["mathew"],
            body=body,
            created=datetime.now(timezone.utc).isoformat(),
            updated=datetime.now(timezone.utc).isoformat()
        )

    @classmethod
    def get_issue_comments(cls, key: str) -> List[JiraComment]:
        return [
            JiraComment(
                id="comm-101",
                author=cls._users["sarah"],
                body="Reproduced on Safari 17.4 on iOS 17. Checking redirect URI query parameter encoding.",
                created="2026-09-20T11:00:00Z"
            ),
            JiraComment(
                id="comm-102",
                author=cls._users["mathew"],
                body="Found root cause in PKCE code_verifier generation. Preparing fix.",
                created="2026-09-21T09:30:00Z"
            )
        ]

    @classmethod
    def get_sprints(cls) -> List[JiraSprint]:
        return cls._sprints

    @classmethod
    def get_sprint_issues(cls, sprint_id: int) -> List[JiraIssue]:
        cls._initialize_mock_data()
        return list(cls._issues.values())

    @classmethod
    def get_issue_types(cls) -> List[JiraIssueType]:
        return [
            JiraIssueType(id="1", name="Bug", subtask=False),
            JiraIssueType(id="2", name="Story", subtask=False),
            JiraIssueType(id="3", name="Task", subtask=False),
            JiraIssueType(id="4", name="Epic", subtask=False),
            JiraIssueType(id="5", name="Sub-task", subtask=True)
        ]

    @classmethod
    def get_priorities(cls) -> List[JiraPriority]:
        return [
            JiraPriority(id="1", name="P0 / Highest"),
            JiraPriority(id="2", name="P1 / High"),
            JiraPriority(id="3", name="P2 / Medium"),
            JiraPriority(id="4", name="P3 / Low"),
            JiraPriority(id="5", name="P4 / Lowest")
        ]
