"""DevOps RCA Assessment — Submission Preparation Tool.

Reads the candidate's RCA report and Cline conversation history,
extracts tool call data, and writes a SUBMISSION.json file that
the candidate then submits via Cline's submit_rca_v2 MCP tool.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

# Cline stores conversation history in VSCode extension globalStorage.
# These are the known paths across platforms (Codespaces use vscode-server).
CLINE_HISTORY_SEARCH_PATHS = [
    "{home}/.vscode-remote/data/User/globalStorage/saoudrizwan.claude-dev/tasks",
    "{home}/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/tasks",
    "{home}/.config/Code/User/globalStorage/saoudrizwan.claude-dev/tasks",
    "{home}/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/tasks",
    "{home}/AppData/Roaming/Code/User/globalStorage/saoudrizwan.claude-dev/tasks",
]

HISTORY_FILENAMES = ["api_conversation_history.json", "ui_messages.json"]


# ---------------------------------------------------------------------------
# Cline history discovery
# ---------------------------------------------------------------------------


def find_cline_history_dir() -> Optional[Path]:
    """Search known Cline storage locations for the tasks directory."""
    home = Path.home()
    for template in CLINE_HISTORY_SEARCH_PATHS:
        candidate = Path(template.format(home=home))
        if candidate.is_dir():
            # Verify it has at least one task with conversation data
            for task_dir in candidate.iterdir():
                if not task_dir.is_dir():
                    continue
                for fname in HISTORY_FILENAMES:
                    history_file = task_dir / fname
                    if history_file.is_file() and history_file.stat().st_size > 0:
                        return candidate
    return None


def collect_cline_history(tasks_dir: Path) -> tuple[str, int]:
    """Read all Cline conversation history files. Returns (json_string, task_count)."""
    conversations = []
    for task_dir in sorted(tasks_dir.iterdir()):
        if not task_dir.is_dir():
            continue
        for fname in HISTORY_FILENAMES:
            history_file = task_dir / fname
            if not history_file.is_file():
                continue
            try:
                content = history_file.read_text(encoding="utf-8")
                parsed = json.loads(content)
                if isinstance(parsed, list) and len(parsed) > 0:
                    conversations.append({"taskId": task_dir.name, "file": fname, "messages": parsed})
            except (json.JSONDecodeError, OSError):
                continue

    if not conversations:
        return "", 0
    return json.dumps(conversations), len(conversations)


# ---------------------------------------------------------------------------
# Tool call extraction
# ---------------------------------------------------------------------------


def extract_tool_calls(history_json: str) -> str:
    """Parse Cline history and extract MCP tool calls into a structured summary.

    Extracts: tool name, parameters, and timestamps for each MCP tool invocation.
    This data replaces the server-side session audit for grading Items 4, 5, 6, B1.
    """
    try:
        conversations = json.loads(history_json)
    except (json.JSONDecodeError, TypeError):
        return "[]"

    tool_calls = []

    for conv in conversations:
        messages = conv.get("messages", [])
        for msg in messages:
            # Cline logs MCP tool requests as "mcp_server_request_started" events
            if msg.get("type") == "say" and msg.get("say") == "mcp_server_request_started":
                try:
                    req_data = json.loads(msg.get("text", "{}"))
                    tool_calls.append({
                        "timestamp": _format_ts(msg.get("ts")),
                        "tool_name": req_data.get("tool_name") or req_data.get("name", "unknown"),
                        "parameters": req_data.get("arguments") or req_data.get("input", {}),
                    })
                except (json.JSONDecodeError, TypeError):
                    continue

            # Also check content blocks for tool_use entries
            if isinstance(msg.get("content"), list):
                for block in msg["content"]:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_calls.append({
                            "timestamp": _format_ts(msg.get("ts")),
                            "tool_name": block.get("name", "unknown"),
                            "parameters": block.get("input", {}),
                        })

    return json.dumps(tool_calls, indent=2)


def _format_ts(ts) -> Optional[str]:
    """Convert Cline timestamp (ms since epoch) to ISO 8601."""
    if ts is None:
        return None
    try:
        from datetime import datetime, timezone
        return datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc).isoformat()
    except (ValueError, TypeError, OSError):
        return None


# ---------------------------------------------------------------------------
# Read RCA report
# ---------------------------------------------------------------------------


def read_rca_report(repo_root: Path) -> str:
    """Read RCA_REPORT.md from the repo root."""
    rca_path = repo_root / "RCA_REPORT.md"
    if not rca_path.is_file():
        print("Error: RCA_REPORT.md not found.", file=sys.stderr)
        print("Please write your RCA report in RCA_REPORT.md before submitting.", file=sys.stderr)
        print("Use RCA_TEMPLATE.md as a starting point.", file=sys.stderr)
        sys.exit(1)

    text = rca_path.read_text(encoding="utf-8")
    if len(text.strip()) < 100:
        print("Error: RCA_REPORT.md is too short (< 100 characters).", file=sys.stderr)
        print("Please complete your RCA report before submitting.", file=sys.stderr)
        sys.exit(1)

    return text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def get_submission_id() -> str:
    """Get the Submission ID from CLI argument or interactive prompt."""
    if len(sys.argv) > 1:
        return sys.argv[1].strip()

    print("  Enter your Submission ID (from SurveyMonkey): ", end="", flush=True)
    sid = input().strip()
    if not sid:
        print("Error: Submission ID is required.", file=sys.stderr)
        sys.exit(1)
    return sid


def main():
    repo_root = Path.cwd()

    print()
    print("=== DevOps RCA Assessment — Prepare Submission ===")
    print()

    # 0. Get Submission ID
    submission_id = get_submission_id()
    print(f"  Submission ID:   {submission_id[:8]}...")

    # 1. Read RCA
    rca_text = read_rca_report(repo_root)
    print(f"  RCA report:      {len(rca_text)} characters")

    # 2. Find and collect Cline history
    tasks_dir = find_cline_history_dir()
    cline_history = ""
    tool_call_summary = "[]"

    if tasks_dir:
        cline_history, task_count = collect_cline_history(tasks_dir)
        if cline_history:
            tool_call_summary = extract_tool_calls(cline_history)
            tool_count = len(json.loads(tool_call_summary))
            print(f"  Cline tasks:     {task_count}")
            print(f"  Tool calls:      {tool_count}")
        else:
            print("  Warning: Cline history found but empty.")
    else:
        print()
        print("  Warning: No Cline conversation history found.")
        print("  Your AI interaction data will not be included.")
        print()

    # 3. Write SUBMISSION.json
    submission = {
        "submission_id": submission_id,
        "rca_summary": rca_text,
    }
    if cline_history:
        submission["cline_history"] = cline_history
        submission["tool_call_summary"] = tool_call_summary

    output_path = repo_root / "SUBMISSION.json"
    output_path.write_text(json.dumps(submission, indent=2), encoding="utf-8")

    print()
    print(f"  SUBMISSION.json written ({output_path.stat().st_size} bytes)")
    print()
    print("=== Preparation complete! ===")
    print()
    print("Now ask Cline to submit by saying:")
    print()
    print('  "Read SUBMISSION.json and call submit_rca_v2 with its contents."')
    print()


if __name__ == "__main__":
    main()
