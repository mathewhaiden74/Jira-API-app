import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("jira_assistant.parser")

# Keywords that signal the user is asking a general/analytical question, not a CRUD Jira action.
GENERAL_QUESTION_SIGNALS = [
    "how many", "how much", "who ", "whose", "which ",
    "what is", "what are", "what was", "what were",
    "when was", "when is", "when did",
    "tell me", "explain", "describe",
    "give me a count", "count of", "number of",
    "how often", "percentage", "ratio",
    "persons", "people", "members", "contributors", "assignees",
    "worked on", "involved in", "participated",
    "health of", "status of", "overview of",
    "latest update", "recent activity", "history",
    "what happened", "progress of", "report on",
    "can you", "could you", "would you",
    "hi ", "hello", "hey ", "thanks", "thank you",
    "what can you", "help me", "what do you",
    "how is", "how was", "how are",
]

# Strong action keywords that override the general-question detection.
STRONG_JIRA_ACTION_SIGNALS = [
    "create a bug", "create a task", "create a story", "create an epic", "create epic",
    "create a subtask", "create subtask", "create a sub-task", "create sub-task",
    "create subtasks", "create multiple subtasks", "add subtasks",
    "add a subtask", "add subtask", "add an epic", "add epic", "file an epic",
    "file a bug", "open a bug", "add a bug", "update priority", "change priority",
    "assign ", "move to", "transition to",
    "add a comment", "add comment", "generate test cases",
    "find duplicate", "find similar",
]


class CommandParser:
    """
    Parses natural language requests into structured Jira intent actions and parameters.
    Used as a reliable rule-based fallback when OpenAI is not configured.
    """

    @staticmethod
    def parse_intent_fallback(text: str, project_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Rule-based NLP matcher. Routes to the most specific action possible.
        Falls back to GENERAL_CONVERSATION (not SEARCH_ISSUES) for unknown/analytical questions.
        """
        t = text.strip()
        t_lower = t.lower()
        default_proj = project_context or "PROJ"

        # ── EARLY EXIT: Pure conversational / analytical questions ───────────────
        # If the text matches a general-question signal and has NO strong Jira action keyword,
        # send it to GENERAL_CONVERSATION so the AI can properly answer it.
        has_general_signal = any(sig in t_lower for sig in GENERAL_QUESTION_SIGNALS)
        has_strong_action = any(sig in t_lower for sig in STRONG_JIRA_ACTION_SIGNALS)
        if has_general_signal and not has_strong_action:
            return {
                "action": "GENERAL_CONVERSATION",
                "parameters": {
                    "query": text,
                    "project_context": default_proj
                }
            }

        # 1. GENERATE TEST CASES
        test_case_match = re.search(
            r'(?:generate|create|write|make)\s+test\s*cases?\s+(?:for\s+)?([A-Za-z0-9]+-\d+)',
            t, re.IGNORECASE
        )
        if test_case_match or "test case" in t_lower or "test cases" in t_lower:
            key_match = re.search(r'([A-Za-z0-9]+-\d+)', t)
            key = key_match.group(1).upper() if key_match else f"{default_proj}-1"
            return {
                "action": "GENERATE_TEST_CASES",
                "parameters": {"issue_key": key}
            }

        # 2. FIND SIMILAR / DUPLICATE ISSUES
        if "duplicate" in t_lower or "similar" in t_lower:
            key_match = re.search(r'([A-Za-z0-9]+-\d+)', t)
            key = key_match.group(1).upper() if key_match else f"{default_proj}-1"
            return {
                "action": "FIND_SIMILAR_ISSUES",
                "parameters": {"issue_key": key}
            }

        # 3. ANALYZE BUGS
        if "analyze bug" in t_lower or "bug analysis" in t_lower or "breakdown of bugs" in t_lower:
            return {
                "action": "ANALYZE_BUGS",
                "parameters": {
                    "jql": f"project = {default_proj} AND issuetype = Bug ORDER BY created DESC"
                }
            }

        # 4. SUMMARIZE SPRINT
        if (
            "summary of this sprint" in t_lower
            or "summarize sprint" in t_lower
            or "sprint summary" in t_lower
            or "this sprint" in t_lower
        ):
            return {
                "action": "SUMMARIZE_SPRINT",
                "parameters": {"project_key": default_proj}
            }

        # 5. TRANSITION ISSUE: "Move PROJ-123 to In Progress"
        trans_match = re.search(
            r'(?:move|transition|set|mark|close|reopen)\s+([A-Za-z0-9]+-\d+)\s+to\s+([A-Za-z0-9\s]+)',
            t, re.IGNORECASE
        )
        if trans_match:
            return {
                "action": "TRANSITION_ISSUE",
                "parameters": {
                    "issue_key": trans_match.group(1).upper(),
                    "status": trans_match.group(2).strip()
                }
            }

        # 6. ASSIGN ISSUE
        assign_match = re.search(
            r'assign\s+([A-Za-z0-9]+-\d+)\s+to\s+([A-Za-z0-9\s]+)',
            t, re.IGNORECASE
        )
        if assign_match:
            return {
                "action": "ASSIGN_ISSUE",
                "parameters": {
                    "issue_key": assign_match.group(1).upper(),
                    "assignee": assign_match.group(2).strip()
                }
            }

        # 7. UPDATE ISSUE priority
        prio_match = re.search(
            r'(?:update|change|set)\s+(?:the\s+)?priority\s+of\s+([A-Za-z0-9]+-\d+)\s+to\s+([A-Za-z0-9\s]+)',
            t, re.IGNORECASE
        )
        if prio_match:
            return {
                "action": "UPDATE_ISSUE",
                "parameters": {
                    "issue_key": prio_match.group(1).upper(),
                    "fields": {"priority": prio_match.group(2).strip()}
                }
            }

        # 8. ADD COMMENT
        comment_match = re.search(
            r'(?:add\s+a\s+comment|comment)\s+(?:to|on)\s+([A-Za-z0-9]+-\d+)(?:\s+saying|\s*:)?\s+(.+)',
            t, re.IGNORECASE
        )
        if comment_match:
            return {
                "action": "ADD_COMMENT",
                "parameters": {
                    "issue_key": comment_match.group(1).upper(),
                    "body": comment_match.group(2).strip()
                }
            }

        # 8b. CREATE MULTIPLE SUBTASKS
        # Examples:
        # "Create subtasks for KAN-1: 1. Setup DB 2. Build API 3. Write tests"
        # "Create multiple subtasks under KAN-1"
        # "Break down KAN-1 into subtasks"
        multi_subtask_match = re.search(
            r'(?:create|add|make|file|generate)\s+(?:multiple\s+|several\s+)?sub-?tasks\s+(?:for|to|under|in)\s+([A-Za-z0-9]+-\d+)(?:\s*[:\-]?\s*(.+))?',
            t, re.IGNORECASE | re.DOTALL
        )
        break_down_match = re.search(
            r'break\s+down\s+([A-Za-z0-9]+-\d+)\s+into\s+(?:sub-?tasks?|tasks)',
            t, re.IGNORECASE
        )
        if multi_subtask_match or break_down_match:
            key_m = break_down_match or multi_subtask_match
            parent_key = key_m.group(1).upper()
            raw_tasks = multi_subtask_match.group(2).strip() if (multi_subtask_match and len(multi_subtask_match.groups()) >= 2 and multi_subtask_match.group(2)) else ""
            
            subtask_objects = []
            if raw_tasks:
                items = re.split(r'(?:\r?\n|;|\b\d+[\.\)]|\s*[\-\*]\s*)', raw_tasks)
                for item in items:
                    clean_item = re.sub(r'^(?:and|or|\d+[\.\)]|\s*[\-\*])\s*', '', item, flags=re.IGNORECASE).strip().rstrip('.')
                    if clean_item and len(clean_item) > 2:
                        subtask_objects.append({"summary": clean_item.capitalize(), "priority": "Medium"})
            
            if not subtask_objects:
                # Standard comprehensive breakdown presets
                subtask_objects = [
                    {"summary": f"Backend API & Logic for {parent_key}", "priority": "High"},
                    {"summary": f"Frontend UI Implementation for {parent_key}", "priority": "Medium"},
                    {"summary": f"Integration Testing & QA Verification for {parent_key}", "priority": "Medium"},
                    {"summary": f"Documentation & Release Review for {parent_key}", "priority": "Low"}
                ]

            proj_from_key = parent_key.split("-")[0] if "-" in parent_key else default_proj
            return {
                "action": "CREATE_MULTIPLE_SUBTASKS",
                "parameters": {
                    "project_key": proj_from_key,
                    "parent_key": parent_key,
                    "subtasks": subtask_objects,
                    "priority": "High" if any(p in t_lower for p in ["critical", "p0", "p1"]) else "Medium"
                }
            }

        # 9. CREATE SUBTASK
        # Examples:
        # "create a subtask for KAN-1 with summary: Implement unit test coverage."
        # "create subtask under KAN-5: update ui"
        # "add a subtask to KAN-3 for database migration"
        subtask_match = re.search(
            r'(?:create|add|make|file)\s+(?:a\s+)?sub-?task\s+(?:for|to|under|in)\s+([A-Za-z0-9]+-\d+)(?:\s*(?:with\s+summary|with\s+title|named|saying|for)?\s*[:\-]?\s*)(.+)',
            t, re.IGNORECASE
        )
        if subtask_match:
            parent_key = subtask_match.group(1).upper()
            raw_summary = subtask_match.group(2).strip().rstrip('.')
            clean_summary = re.sub(r'^(?:with\s+summary|with\s+title|named|saying|for)?\s*[:\-]?\s*', '', raw_summary, flags=re.IGNORECASE).strip()
            clean_summary = clean_summary or "New Subtask"
            proj_from_key = parent_key.split("-")[0] if "-" in parent_key else default_proj
            return {
                "action": "CREATE_ISSUE",
                "parameters": {
                    "project_key": proj_from_key,
                    "parent_key": parent_key,
                    "issue_type": "Subtask",
                    "summary": clean_summary.capitalize(),
                    "priority": "High" if any(p in t_lower for p in ["critical", "p0", "p1"]) else "Medium",
                    "description": f"Subtask under {parent_key} created via Jira AI Assistant.\nSummary: {clean_summary}"
                }
            }

        # Alternate format: "create subtask Implement unit tests for KAN-12"
        subtask_match_alt = re.search(
            r'(?:create|add|make|file)\s+(?:a\s+)?sub-?task\s+(?:with\s+summary|named|saying|for)?\s*[:\-]?\s*(.+?)\s+(?:for|to|under|in)\s+([A-Za-z0-9]+-\d+)',
            t, re.IGNORECASE
        )
        if subtask_match_alt:
            parent_key = subtask_match_alt.group(2).upper()
            clean_summary = subtask_match_alt.group(1).strip().rstrip('.')
            clean_summary = clean_summary or "New Subtask"
            proj_from_key = parent_key.split("-")[0] if "-" in parent_key else default_proj
            return {
                "action": "CREATE_ISSUE",
                "parameters": {
                    "project_key": proj_from_key,
                    "parent_key": parent_key,
                    "issue_type": "Subtask",
                    "summary": clean_summary.capitalize(),
                    "priority": "High" if any(p in t_lower for p in ["critical", "p0", "p1"]) else "Medium",
                    "description": f"Subtask under {parent_key} created via Jira AI Assistant.\nSummary: {clean_summary}"
                }
            }

        # Fallback for "create subtask <summary>" without explicit parent key
        if "subtask" in t_lower or "sub-task" in t_lower:
            key_in_text = re.search(r'([A-Za-z0-9]+-\d+)', t)
            parent_k = key_in_text.group(1).upper() if key_in_text else f"{default_proj}-1"
            clean_summary = re.sub(r'^(?:create|add|make|file)\s+(?:a\s+)?sub-?task\s+(?:for|about|with\s+summary)?', '', t, flags=re.IGNORECASE).strip().rstrip('.')
            clean_summary = clean_summary or "New Subtask"
            return {
                "action": "CREATE_ISSUE",
                "parameters": {
                    "project_key": parent_k.split("-")[0] if "-" in parent_k else default_proj,
                    "parent_key": parent_k,
                    "issue_type": "Subtask",
                    "summary": clean_summary.capitalize(),
                    "priority": "High" if any(p in t_lower for p in ["critical", "p0", "p1"]) else "Medium",
                    "description": f"Subtask under {parent_k} created via Jira AI Assistant.\nSummary: {clean_summary}"
                }
            }

        # 10. CREATE EPIC
        # Examples: "create an epic for Core Platform Architecture in KAN.", "create epic Mobile App Redesign"
        epic_match = re.search(
            r'(?:create|add|make|file|open)\s+(?:an?\s+)?epic\s+(?:for|about|named|with\s+summary|with\s+title)?\s*(?::\s*)?(.+)',
            t, re.IGNORECASE
        )
        if epic_match:
            raw_summary = epic_match.group(1).strip().rstrip('.')
            proj_in_text = re.search(r'\s+in\s+([A-Za-z0-9]+)$', raw_summary, re.IGNORECASE)
            target_proj = default_proj
            clean_summary = raw_summary
            if proj_in_text:
                target_proj = proj_in_text.group(1).upper()
                clean_summary = raw_summary[:proj_in_text.start()].strip()
            
            clean_summary = clean_summary or "New Epic"
            return {
                "action": "CREATE_ISSUE",
                "parameters": {
                    "project_key": target_proj,
                    "issue_type": "Epic",
                    "summary": clean_summary.capitalize(),
                    "priority": "High" if any(p in t_lower for p in ["critical", "p0", "p1"]) else "Medium",
                    "description": f"Epic initiative created via Jira AI Assistant.\nSummary: {clean_summary}"
                }
            }

        # 11. CREATE ISSUE / BUG / STORY / TASK
        create_match = re.search(
            r'(?:create|file|open|add)\s+(?:a\s+)?(bug|task|story|ticket|issue)\s+(?:for|about|with\s+summary)?\s+(.+)',
            t, re.IGNORECASE
        )
        if create_match:
            issue_type = create_match.group(1).capitalize()
            if issue_type.lower() in ["ticket", "issue"]:
                issue_type = "Bug"
            summary = create_match.group(2).strip().capitalize()
            return {
                "action": "CREATE_ISSUE",
                "parameters": {
                    "project_key": default_proj,
                    "issue_type": issue_type,
                    "summary": summary,
                    "priority": "High" if any(p in t_lower for p in ["critical", "p0", "p1"]) else "Medium",
                    "description": f"Automated ticket created via Jira AI Assistant.\nSummary: {summary}"
                }
            }

        # 10. GET SINGLE ISSUE: "Show PROJ-123"
        single_issue_match = re.search(
            r'^(?:show|get|view|details\s+of|what\s+is)\s+([A-Za-z0-9]+-\d+)$',
            t, re.IGNORECASE
        )
        if single_issue_match:
            return {
                "action": "GET_ISSUE",
                "parameters": {"issue_key": single_issue_match.group(1).upper()}
            }

        # 11. SUMMARIZE BUGS / ISSUES
        if "summarize" in t_lower and ("bug" in t_lower or "issue" in t_lower):
            return {
                "action": "SUMMARIZE_ISSUES",
                "parameters": {
                    "jql": (
                        f"project = {default_proj} AND issuetype = Bug "
                        f"AND statusCategory != Done ORDER BY created DESC"
                    )
                }
            }

        # 12. EXPLICIT SEARCH: user clearly said "show me / list / find / search" + Jira entity
        explicit_search = any(kw in t_lower for kw in ["show me", "list ", "find ", "search ", "get all", "show all", "fetch "])
        has_jira_entity = any(kw in t_lower for kw in ["bug", "issue", "task", "story", "ticket", "backlog"])

        if explicit_search and has_jira_entity:
            jql_parts = [f"project = {default_proj}"]

            if "bug" in t_lower:
                jql_parts.append("issuetype = Bug")
            elif "story" in t_lower or "stories" in t_lower:
                jql_parts.append("issuetype = Story")
            elif "task" in t_lower:
                jql_parts.append("issuetype = Task")

            if "assigned to me" in t_lower or "my bugs" in t_lower or "my issues" in t_lower:
                jql_parts.append("assignee = currentUser()")

            if "p0 and p1" in t_lower or "p0, p1" in t_lower:
                jql_parts.append("priority in (P0, P1, Highest, High)")
            elif "p0" in t_lower or "highest" in t_lower:
                jql_parts.append("priority in (P0, Highest)")
            elif "p1" in t_lower or "high priority" in t_lower:
                jql_parts.append("priority in (P1, High)")

            if "open" in t_lower or "unresolved" in t_lower:
                jql_parts.append("statusCategory != Done")
            elif "done" in t_lower or "resolved" in t_lower or "closed" in t_lower:
                jql_parts.append("statusCategory = Done")
            elif "in progress" in t_lower:
                jql_parts.append("status = 'In Progress'")

            jql_parts.append("ORDER BY priority DESC, created DESC")
            return {
                "action": "SEARCH_ISSUES",
                "parameters": {
                    "jql": " AND ".join(jql_parts[:-1]) + " " + jql_parts[-1]
                }
            }

        # ── DEFAULT: anything else is a general question for the AI agent ────────
        return {
            "action": "GENERAL_CONVERSATION",
            "parameters": {
                "query": text,
                "project_context": default_proj
            }
        }
