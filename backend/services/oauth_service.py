import httpx
import sqlite3
import time
import json
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode

from config import settings
from models.schemas import AuthStatus, JiraUser

logger = logging.getLogger("jira_assistant.oauth")

class OAuthService:
    def __init__(self, db_path: str = settings.DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database for sessions and pending actions."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        access_token TEXT,
                        refresh_token TEXT,
                        token_expires_at REAL,
                        cloud_id TEXT,
                        site_name TEXT,
                        site_url TEXT,
                        user_account_id TEXT,
                        user_display_name TEXT,
                        user_email TEXT,
                        user_avatar_url TEXT,
                        is_mock INTEGER DEFAULT 0,
                        updated_at REAL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pending_actions (
                        action_id TEXT PRIMARY KEY,
                        session_id TEXT,
                        action TEXT,
                        issue_key TEXT,
                        summary_text TEXT,
                        parameters TEXT,
                        expires_at REAL,
                        created_at REAL
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def get_authorization_url(self, session_id: str = "default_user") -> str:
        """Construct Atlassian OAuth 2.0 (3LO) authorization URL."""
        if not settings.ATLASSIAN_CLIENT_ID:
            # If client ID is missing, return a local mock callback redirect or info
            return f"{settings.FRONTEND_URL}?mock_auth=true"

        params = {
            "audience": "api.atlassian.com",
            "client_id": settings.ATLASSIAN_CLIENT_ID,
            "scope": settings.ATLASSIAN_SCOPES,
            "redirect_uri": settings.ATLASSIAN_REDIRECT_URI,
            "state": session_id,
            "response_type": "code",
            "prompt": "consent"
        }
        return f"{settings.ATLASSIAN_AUTH_URL}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str, session_id: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            payload = {
                "grant_type": "authorization_code",
                "client_id": settings.ATLASSIAN_CLIENT_ID,
                "client_secret": settings.ATLASSIAN_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.ATLASSIAN_REDIRECT_URI
            }
            response = await client.post(settings.ATLASSIAN_TOKEN_URL, json=payload)
            if response.status_code != 200:
                logger.error(f"OAuth token exchange error {response.status_code}: {response.text}")
                raise Exception(f"Failed to exchange OAuth token: {response.text}")

            token_data = response.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 3600)
            token_expires_at = time.time() + expires_in

            # Fetch accessible Jira resources (Cloud sites)
            resources = await self.fetch_accessible_resources(access_token)
            if not resources:
                raise Exception("No accessible Jira Cloud sites found for this Atlassian account.")

            primary_site = resources[0]
            cloud_id = primary_site.get("id")
            site_name = primary_site.get("name")
            site_url = primary_site.get("url")

            # Fetch current user profile
            user_info = await self.fetch_user_profile(access_token, cloud_id)

            # Store session in SQLite
            self.save_session(
                session_id=session_id,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=token_expires_at,
                cloud_id=cloud_id,
                site_name=site_name,
                site_url=site_url,
                user=user_info,
                is_mock=False
            )

            return {
                "access_token": access_token,
                "cloud_id": cloud_id,
                "site_name": site_name,
                "site_url": site_url,
                "user": user_info
            }

    async def fetch_accessible_resources(self, access_token: str) -> List[Dict[str, Any]]:
        """Fetch list of Jira Cloud instances accessible by user."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
            response = await client.get(settings.ATLASSIAN_RESOURCES_URL, headers=headers)
            if response.status_code == 200:
                return response.json()
            logger.error(f"Error fetching accessible resources: {response.text}")
            return []

    async def fetch_user_profile(self, access_token: str, cloud_id: str) -> JiraUser:
        """Fetch current Jira user details."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/myself"
            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                avatar_urls = data.get("avatarUrls", {})
                avatar = avatar_urls.get("48x48") or avatar_urls.get("32x32") or avatar_urls.get("24x24")
                return JiraUser(
                    accountId=data.get("accountId"),
                    displayName=data.get("displayName", "Jira User"),
                    emailAddress=data.get("emailAddress"),
                    avatarUrl=avatar,
                    active=data.get("active", True)
                )
            return JiraUser(displayName="Authorized Jira User")

    async def refresh_access_token_if_needed(self, session_id: str) -> Optional[str]:
        """Check if access token is expired and refresh using refresh_token."""
        session = self.get_session(session_id)
        if not session or session.get("is_mock"):
            return None

        expires_at = session.get("token_expires_at", 0)
        # Refresh if token expires in less than 60 seconds
        if time.time() < (expires_at - 60):
            return session.get("access_token")

        refresh_token = session.get("refresh_token")
        if not refresh_token:
            return None

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                payload = {
                    "grant_type": "refresh_token",
                    "client_id": settings.ATLASSIAN_CLIENT_ID,
                    "client_secret": settings.ATLASSIAN_CLIENT_SECRET,
                    "refresh_token": refresh_token
                }
                response = await client.post(settings.ATLASSIAN_TOKEN_URL, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    new_access_token = data.get("access_token")
                    new_refresh_token = data.get("refresh_token", refresh_token)
                    expires_in = data.get("expires_in", 3600)
                    new_expires_at = time.time() + expires_in

                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE sessions
                            SET access_token = ?, refresh_token = ?, token_expires_at = ?, updated_at = ?
                            WHERE session_id = ?
                        """, (new_access_token, new_refresh_token, new_expires_at, time.time(), session_id))
                        conn.commit()

                    return new_access_token
                else:
                    logger.error(f"Failed to refresh token: {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Error during token refresh: {e}")
            return None

    def save_session(
        self,
        session_id: str,
        access_token: Optional[str],
        refresh_token: Optional[str],
        token_expires_at: float,
        cloud_id: Optional[str],
        site_name: Optional[str],
        site_url: Optional[str],
        user: Optional[JiraUser],
        is_mock: bool = False
    ):
        """Save or update user session in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (
                    session_id, access_token, refresh_token, token_expires_at,
                    cloud_id, site_name, site_url,
                    user_account_id, user_display_name, user_email, user_avatar_url,
                    is_mock, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    access_token = excluded.access_token,
                    refresh_token = excluded.refresh_token,
                    token_expires_at = excluded.token_expires_at,
                    cloud_id = excluded.cloud_id,
                    site_name = excluded.site_name,
                    site_url = excluded.site_url,
                    user_account_id = excluded.user_account_id,
                    user_display_name = excluded.user_display_name,
                    user_email = excluded.user_email,
                    user_avatar_url = excluded.user_avatar_url,
                    is_mock = excluded.is_mock,
                    updated_at = excluded.updated_at
            """, (
                session_id, access_token, refresh_token, token_expires_at,
                cloud_id, site_name, site_url,
                user.accountId if user else None,
                user.displayName if user else "Mathew (Demo)",
                user.emailAddress if user else "mathew@company.com",
                user.avatarUrl if user else None,
                1 if is_mock else 0,
                time.time()
            ))
            conn.commit()

    def get_session(self, session_id: str = "default_user") -> Optional[Dict[str, Any]]:
        """Retrieve active session details."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def enable_mock_session(self, session_id: str = "default_user"):
        """Enable interactive demo mode when live Jira OAuth is not configured."""
        mock_user = JiraUser(
            accountId="usr-demo-789",
            displayName="Mathew Thomas",
            emailAddress="mathew@acme-software.com",
            avatarUrl="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80",
            active=True
        )
        self.save_session(
            session_id=session_id,
            access_token="mock_access_token_demo_mode",
            refresh_token="mock_refresh_token_demo_mode",
            token_expires_at=time.time() + 86400 * 30,
            cloud_id="mock-cloud-id-12345",
            site_name="acme-engineering.atlassian.net",
            site_url="https://acme-engineering.atlassian.net",
            user=mock_user,
            is_mock=True
        )

    def logout_session(self, session_id: str = "default_user"):
        """Remove active session from database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM pending_actions WHERE session_id = ?", (session_id,))
            conn.commit()

    def get_auth_status(self, session_id: str = "default_user") -> AuthStatus:
        """Get current authentication status."""
        session = self.get_session(session_id)
        if not session:
            # If mock fallback is enabled and no OAuth configured, setup mock session by default
            if settings.ENABLE_MOCK_FALLBACK and not settings.ATLASSIAN_CLIENT_ID:
                self.enable_mock_session(session_id)
                session = self.get_session(session_id)

        if not session:
            return AuthStatus(
                is_authenticated=False,
                is_mock_mode=False,
                message="Not connected to Jira Cloud. Please authenticate via OAuth."
            )

        is_mock = bool(session.get("is_mock"))
        user = JiraUser(
            accountId=session.get("user_account_id"),
            displayName=session.get("user_display_name") or "Jira User",
            emailAddress=session.get("user_email"),
            avatarUrl=session.get("user_avatar_url"),
            active=True
        )

        return AuthStatus(
            is_authenticated=True,
            is_mock_mode=is_mock,
            user=user,
            site_name=session.get("site_name"),
            site_url=session.get("site_url"),
            cloud_id=session.get("cloud_id"),
            message="Connected to Jira Cloud" if not is_mock else "Connected to Jira Demo Environment"
        )

    # Pending actions management for safe write confirmations
    def save_pending_action(self, action_id: str, session_id: str, action: str, issue_key: Optional[str], summary_text: str, parameters: Dict[str, Any], ttl_seconds: int = 600):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = time.time()
            cursor.execute("""
                INSERT INTO pending_actions (action_id, session_id, action, issue_key, summary_text, parameters, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (action_id, session_id, action, issue_key, summary_text, json.dumps(parameters), now + ttl_seconds, now))
            conn.commit()

    def get_pending_action(self, action_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pending_actions WHERE action_id = ?", (action_id,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                if data["expires_at"] < time.time():
                    # Expired
                    cursor.execute("DELETE FROM pending_actions WHERE action_id = ?", (action_id,))
                    conn.commit()
                    return None
                data["parameters"] = json.loads(data["parameters"])
                return data
        return None

    def delete_pending_action(self, action_id: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pending_actions WHERE action_id = ?", (action_id,))
            conn.commit()

oauth_service = OAuthService()
