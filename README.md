# 🚀 Jira AI Assistant

An external, enterprise-grade AI application that connects to **Jira Cloud** through the official **Jira Cloud REST API (v3)** and enables users to interact with their projects using natural language.

---

## 🌟 Key Features

- 💬 **Natural Language Jira Interaction**: Query, create, update, assign, transition, and triage Jira issues effortlessly.
- 🛡️ **Safe Write Confirmation Gates**: Destructive or modifying operations (`CREATE_ISSUE`, `UPDATE_ISSUE`, `ASSIGN_ISSUE`, `TRANSITION_ISSUE`, `ADD_COMMENT`) require explicit user confirmation before executing against Jira Cloud.
- 📋 **AI Test Case Generator**: Converts Jira stories and requirements into structured QA test cases (Functional, Negative, Security, Boundary) with copy-to-clipboard and JSON export capabilities.
- 📊 **Sprint & Bug Analytics**: Generates real-time statistics (total bugs, severity breakdown, assignee distribution, component health, active blockers).
- 🔍 **Duplicate Bug Detection**: Compares new or existing bug reports against existing project issues using NLP and symptom matching to prevent duplicate tickets.
- 🔐 **Atlassian OAuth 2.0 (3LO)**: Official 3-Legged OAuth with secure token management and Cloud ID resolution. Tokens and API keys are **never** exposed to the frontend.
- ⚡ **Interactive Demo / Mock Mode**: High-fidelity demo mode included out-of-the-box so you can test all features immediately without requiring live Atlassian credentials.

---

## 🏛 Architecture Overview

```
User / Browser (React + Vite)
       │  (Chat UI, Issue Cards, Confirmation Dialogs, Analytics)
       ▼
Backend (FastAPI, httpx, pydantic)
       ├── 1. Intent Detection & Classification (OpenAI GPT-4o / Rule-Based NLP)
       ├── 2. Safe Write Gate (Pending Actions in SQLite)
       ├── 3. Jira REST API Service (Cloud REST API v3)
       └── 4. Response Synthesis (AI summaries based strictly on real Jira data)
       │
       ▼
Atlassian Jira Cloud (REST API v3 / Agile API) & OpenAI API
```

---

## 📁 Project Structure

```
jira-ai-assistant/
├── backend/
│   ├── main.py                     # FastAPI application entrypoint & middleware
│   ├── config.py                   # Pydantic Settings & environment variables
│   ├── requirements.txt            # Python dependencies
│   ├── .env.example                # Backend environment template
│   │
│   ├── routes/
│   │   ├── auth.py                 # OAuth 2.0 (3LO) endpoints & session state
│   │   ├── chat.py                 # Natural language chat & confirmation routes
│   │   └── jira.py                 # Jira REST proxy endpoints
│   │
│   ├── services/
│   │   ├── ai_service.py           # Two-phase AI workflow & synthesis engine
│   │   ├── jira_service.py         # Official Jira Cloud REST API client
│   │   ├── oauth_service.py        # Atlassian 3LO token exchange & refresh
│   │   └── command_parser.py       # Intent extraction & NLP parser
│   │
│   └── models/
│       └── schemas.py              # Pydantic data models & validation
│
├── frontend/
│   ├── package.json                # Frontend dependencies
│   ├── vite.config.js              # Vite server & proxy configuration
│   ├── index.html                  # HTML entry point with Google Fonts
│   └── src/
│       ├── main.jsx                # React root
│       ├── App.jsx                 # Application controller & state
│       ├── api.js                  # Backend API client
│       ├── components/
│       │   ├── Chat.jsx            # Main chat interface & welcome prompts
│       │   ├── Message.jsx         # Message bubble with markdown & widgets
│       │   ├── JiraIssueCard.jsx   # Interactive Jira issue cards
│       │   ├── ConfirmationDialog.jsx # Safe write confirmation gate
│       │   ├── TestCaseCard.jsx    # Test case table with copy/export
│       │   ├── BugAnalysisCard.jsx # Metrics dashboard
│       │   ├── DuplicateAnalysisCard.jsx # Similar bug detector
│       │   └── Sidebar.jsx         # Project switcher, quick actions, user card
│       └── styles/
│           └── app.css             # Modern dark/light Jira theme design system
│
├── README.md
└── .gitignore
```

---

## ⚙️ Prerequisites

- **Python**: 3.10+ (tested on Python 3.14)
- **Node.js**: 18+ (tested on Node v24)
- **Atlassian Developer Account** (optional for live OAuth; Demo Mode works without it)
- **OpenAI API Key** (optional for advanced LLM synthesis; built-in NLP parser included)

---

## 🔑 Atlassian Developer Console Setup (OAuth 2.0 3LO)

To connect to your live Jira Cloud instance:

1. Go to the [Atlassian Developer Console](https://developer.atlassian.com/console/myapps/).
2. Click **Create** > **OAuth 2.0 (3LO) integration**.
3. Name your app (e.g., `Jira AI Assistant`).
4. In the left navigation, click **Permissions**:
   - Next to **Jira API**, click **Add**.
   - Add the following User Scopes:
     - `read:jira-work`
     - `write:jira-work`
     - `read:jira-user`
     - `read:me`
     - `offline_access`
5. In the left navigation, click **Authorization**:
   - Add Callback URL: `http://localhost:8000/auth/callback`
6. In the left navigation, click **Settings**:
   - Copy the **Client ID** and **Client Secret**.

---

## 📝 Environment Configuration

Create a `.env` file in the project root or in `backend/.env`:

```ini
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Atlassian Jira Cloud OAuth 2.0 (3LO) Configuration
ATLASSIAN_CLIENT_ID=your_atlassian_client_id_here
ATLASSIAN_CLIENT_SECRET=your_atlassian_client_secret_here
ATLASSIAN_REDIRECT_URI=http://localhost:8000/auth/callback

# Security & CORS
SECRET_KEY=jira_ai_assistant_super_secret_session_key_2026
FRONTEND_URL=http://localhost:5173

# Mock Fallback (Allows testing full UI, queries, actions, test cases without live keys)
ENABLE_MOCK_FALLBACK=true
```

---

## 🚀 Running the Application

### 1. Start the Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
The backend will run on `http://localhost:8000`. Interactive Swagger API documentation is available at `http://localhost:8000/docs`.

### 2. Start the Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 💬 Example Natural Language Commands to Test

| Intent / Feature | Example Prompt | Action & Safety Gate |
|---|---|---|
| **Query Open Bugs** | `"Show me all open bugs."` | Searches Jira using JQL `issuetype = Bug AND statusCategory != Done` |
| **Assigned Work** | `"Show P0 and P1 bugs assigned to me."` | Searches high-severity bugs assigned to the current user |
| **Executive Summary** | `"Summarize the latest bugs."` | Generates a synthesized executive breakdown of open issues |
| **Create Bug** | `"Create a bug for Microsoft OAuth login failure."` | ⚠️ **Requires confirmation** -> Creates Jira Bug |
| **Update Priority** | `"Update the priority of PROJ-123 to High."` | ⚠️ **Requires confirmation** -> Updates Jira Issue |
| **Transition Issue** | `"Move PROJ-123 to In Progress."` | ⚠️ **Requires confirmation** -> Transitions Issue status |
| **Assign Issue** | `"Assign PROJ-123 to Mathew."` | ⚠️ **Requires confirmation** -> Updates Assignee |
| **Add Comment** | `"Add a comment to PROJ-123 saying root cause identified."` | ⚠️ **Requires confirmation** -> Adds Jira Comment |
| **Generate Test Cases** | `"Generate test cases for PROJ-125."` | Fetches requirement -> Generates structured test cases table |
| **Duplicate Bug Detection** | `"Find duplicate or similar bugs for PROJ-123."` | Searches similar issues -> AI similarity score & symptom match |
| **Bug Analysis** | `"Analyze bugs from this sprint."` | Aggregates bug metrics, assignee load, and health |
| **Sprint Summary** | `"Give me a summary of this sprint."` | Analyzes active sprint burndown, goal progress, and blockers |

---

## 🔒 Security & Privacy

1. **Zero Hardcoded Credentials**: All secrets are stored exclusively in `.env`.
2. **Server-Side Token Isolation**: OAuth tokens and OpenAI API keys are managed purely in the backend and are **never** transmitted to React.
3. **No Jira Passwords Stored**: Authentication uses official OAuth 2.0 (3LO) tokens with automatic refresh.
4. **Modifying Action Safety Gate**: Modifying Jira operations require human-in-the-loop review and approval before execution.
5. **Prompt Injection & Execution Protection**: The AI model is strictly constrained to standard structured JSON actions and cannot execute arbitrary shell commands, SQL, or arbitrary HTTP endpoints.

---

## 🛠 Troubleshooting

- **CORS Errors**: Ensure `FRONTEND_URL` in `.env` matches your Vite dev server port (default `http://localhost:5173`).
- **OAuth 401 Unauthorized**: Ensure your Atlassian App has the required scopes (`read:jira-work`, `write:jira-work`, `offline_access`) and that your redirect URI matches `http://localhost:8000/auth/callback`.
- **Token Expired**: Click "Disconnect Jira" in the sidebar and log in again to trigger fresh OAuth tokens.
- **Testing without credentials**: Set `ENABLE_MOCK_FALLBACK=true` in `.env` to explore all features in Demo Mode.
