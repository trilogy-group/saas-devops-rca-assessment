"""Tests for the DevOps RCA Assessment submission tool."""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import submit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_repo(tmp_path):
    """Create a temporary repo root with a valid RCA_REPORT.md."""
    rca = tmp_path / "RCA_REPORT.md"
    rca.write_text("x" * 200, encoding="utf-8")
    return tmp_path


@pytest.fixture
def cline_tasks_dir(tmp_path):
    """Create a fake Cline tasks directory with conversation history."""
    tasks = tmp_path / "tasks"
    tasks.mkdir()

    task1 = tasks / "task_001"
    task1.mkdir()
    history = [
        {
            "type": "say",
            "say": "mcp_server_request_started",
            "ts": 1710000000000,
            "text": json.dumps({
                "tool_name": "get_logs",
                "arguments": {"service": "api-gateway", "hours": 2},
            }),
        },
        {
            "type": "say",
            "say": "mcp_server_request_started",
            "ts": 1710000060000,
            "text": json.dumps({
                "tool_name": "get_cloudwatch_metrics",
                "arguments": {"metric": "CPUUtilization"},
            }),
        },
        {"type": "say", "say": "text", "ts": 1710000120000, "text": "Analyzing logs..."},
    ]
    (task1 / "api_conversation_history.json").write_text(json.dumps(history), encoding="utf-8")

    return tasks


@pytest.fixture
def cline_tasks_with_tool_use(tmp_path):
    """Create a Cline tasks dir with content-block tool_use entries."""
    tasks = tmp_path / "tasks"
    tasks.mkdir()

    task1 = tasks / "task_002"
    task1.mkdir()
    history = [
        {
            "type": "assistant",
            "ts": 1710000000000,
            "content": [
                {
                    "type": "tool_use",
                    "name": "describe_resource",
                    "input": {"resource_id": "i-abc123"},
                },
                {
                    "type": "text",
                    "text": "Let me check that instance.",
                },
            ],
        },
    ]
    (task1 / "api_conversation_history.json").write_text(json.dumps(history), encoding="utf-8")

    return tasks


# ---------------------------------------------------------------------------
# _format_ts
# ---------------------------------------------------------------------------


class TestFormatTs:
    def test_none_returns_none(self):
        assert submit._format_ts(None) is None

    def test_valid_epoch_ms(self):
        result = submit._format_ts(1710000000000)
        assert result == "2024-03-09T16:00:00+00:00"

    def test_string_epoch_ms(self):
        result = submit._format_ts("1710000000000")
        assert result == "2024-03-09T16:00:00+00:00"

    def test_invalid_value_returns_none(self):
        assert submit._format_ts("not-a-number") is None

    def test_zero_epoch(self):
        result = submit._format_ts(0)
        assert result == "1970-01-01T00:00:00+00:00"


# ---------------------------------------------------------------------------
# read_rca_report
# ---------------------------------------------------------------------------


class TestReadRcaReport:
    def test_reads_valid_report(self, tmp_repo):
        text = submit.read_rca_report(tmp_repo)
        assert len(text) == 200

    def test_missing_file_exits(self, tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            submit.read_rca_report(tmp_path)
        assert exc_info.value.code == 1

    def test_too_short_exits(self, tmp_path):
        rca = tmp_path / "RCA_REPORT.md"
        rca.write_text("short", encoding="utf-8")
        with pytest.raises(SystemExit) as exc_info:
            submit.read_rca_report(tmp_path)
        assert exc_info.value.code == 1

    def test_whitespace_only_exits(self, tmp_path):
        rca = tmp_path / "RCA_REPORT.md"
        rca.write_text("   \n\n   ", encoding="utf-8")
        with pytest.raises(SystemExit) as exc_info:
            submit.read_rca_report(tmp_path)
        assert exc_info.value.code == 1

    def test_exactly_100_chars_passes(self, tmp_path):
        rca = tmp_path / "RCA_REPORT.md"
        rca.write_text("a" * 100, encoding="utf-8")
        text = submit.read_rca_report(tmp_path)
        assert len(text) == 100


# ---------------------------------------------------------------------------
# find_cline_history_dir
# ---------------------------------------------------------------------------


class TestFindClineHistoryDir:
    def test_finds_valid_dir(self, tmp_path):
        # Create a fake Cline tasks directory in a known search path
        tasks_path = tmp_path / ".vscode-server" / "data" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "tasks"
        tasks_path.mkdir(parents=True)
        task = tasks_path / "task_001"
        task.mkdir()
        (task / "api_conversation_history.json").write_text('[{"msg": "hi"}]', encoding="utf-8")

        with mock.patch.object(Path, "home", return_value=tmp_path):
            result = submit.find_cline_history_dir()
        assert result == tasks_path

    def test_returns_none_when_no_dirs_exist(self, tmp_path):
        with mock.patch.object(Path, "home", return_value=tmp_path):
            result = submit.find_cline_history_dir()
        assert result is None

    def test_skips_empty_tasks_dir(self, tmp_path):
        tasks_path = tmp_path / ".vscode-server" / "data" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "tasks"
        tasks_path.mkdir(parents=True)
        # Empty dir — no task subdirectories
        with mock.patch.object(Path, "home", return_value=tmp_path):
            result = submit.find_cline_history_dir()
        assert result is None

    def test_skips_task_with_empty_history(self, tmp_path):
        tasks_path = tmp_path / ".vscode-server" / "data" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "tasks"
        tasks_path.mkdir(parents=True)
        task = tasks_path / "task_001"
        task.mkdir()
        (task / "api_conversation_history.json").write_text("", encoding="utf-8")

        with mock.patch.object(Path, "home", return_value=tmp_path):
            result = submit.find_cline_history_dir()
        assert result is None


# ---------------------------------------------------------------------------
# collect_cline_history
# ---------------------------------------------------------------------------


class TestCollectClineHistory:
    def test_collects_valid_history(self, cline_tasks_dir):
        history_json, count = submit.collect_cline_history(cline_tasks_dir)
        assert count == 1
        parsed = json.loads(history_json)
        assert len(parsed) == 1
        assert parsed[0]["taskId"] == "task_001"
        assert parsed[0]["file"] == "api_conversation_history.json"
        assert len(parsed[0]["messages"]) == 3

    def test_empty_dir_returns_empty(self, tmp_path):
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        history_json, count = submit.collect_cline_history(tasks)
        assert history_json == ""
        assert count == 0

    def test_skips_invalid_json(self, tmp_path):
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        task = tasks / "task_bad"
        task.mkdir()
        (task / "api_conversation_history.json").write_text("not json{{{", encoding="utf-8")

        history_json, count = submit.collect_cline_history(tasks)
        assert history_json == ""
        assert count == 0

    def test_skips_non_list_json(self, tmp_path):
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        task = tasks / "task_obj"
        task.mkdir()
        (task / "api_conversation_history.json").write_text('{"not": "a list"}', encoding="utf-8")

        history_json, count = submit.collect_cline_history(tasks)
        assert history_json == ""
        assert count == 0

    def test_skips_empty_list(self, tmp_path):
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        task = tasks / "task_empty"
        task.mkdir()
        (task / "api_conversation_history.json").write_text("[]", encoding="utf-8")

        history_json, count = submit.collect_cline_history(tasks)
        assert history_json == ""
        assert count == 0

    def test_collects_both_history_files(self, tmp_path):
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        task = tasks / "task_both"
        task.mkdir()
        (task / "api_conversation_history.json").write_text('[{"m": 1}]', encoding="utf-8")
        (task / "ui_messages.json").write_text('[{"m": 2}]', encoding="utf-8")

        history_json, count = submit.collect_cline_history(tasks)
        assert count == 2
        parsed = json.loads(history_json)
        assert len(parsed) == 2

    def test_multiple_tasks(self, tmp_path):
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        for i in range(3):
            task = tasks / f"task_{i:03d}"
            task.mkdir()
            (task / "api_conversation_history.json").write_text(f'[{{"task": {i}}}]', encoding="utf-8")

        history_json, count = submit.collect_cline_history(tasks)
        assert count == 3

    def test_skips_non_directory_entries(self, tmp_path):
        tasks = tmp_path / "tasks"
        tasks.mkdir()
        # A file at top level (not a task dir)
        (tasks / "readme.txt").write_text("ignore me", encoding="utf-8")
        task = tasks / "task_real"
        task.mkdir()
        (task / "api_conversation_history.json").write_text('[{"m": 1}]', encoding="utf-8")

        history_json, count = submit.collect_cline_history(tasks)
        assert count == 1


# ---------------------------------------------------------------------------
# extract_tool_calls
# ---------------------------------------------------------------------------


class TestExtractToolCalls:
    def test_extracts_mcp_server_requests(self, cline_tasks_dir):
        history_json, _ = submit.collect_cline_history(cline_tasks_dir)
        result = submit.extract_tool_calls(history_json)
        calls = json.loads(result)
        assert len(calls) == 2
        assert calls[0]["tool_name"] == "get_logs"
        assert calls[0]["parameters"] == {"service": "api-gateway", "hours": 2}
        assert calls[0]["timestamp"] is not None
        assert calls[1]["tool_name"] == "get_cloudwatch_metrics"

    def test_extracts_tool_use_content_blocks(self, cline_tasks_with_tool_use):
        history_json, _ = submit.collect_cline_history(cline_tasks_with_tool_use)
        result = submit.extract_tool_calls(history_json)
        calls = json.loads(result)
        assert len(calls) == 1
        assert calls[0]["tool_name"] == "describe_resource"
        assert calls[0]["parameters"] == {"resource_id": "i-abc123"}

    def test_invalid_json_returns_empty_list(self):
        result = submit.extract_tool_calls("not json")
        assert result == "[]"

    def test_none_input_returns_empty_list(self):
        result = submit.extract_tool_calls(None)
        assert result == "[]"

    def test_empty_string_returns_empty_list(self):
        result = submit.extract_tool_calls("")
        assert result == "[]"

    def test_no_tool_calls_in_history(self):
        history = json.dumps([{
            "taskId": "task_001",
            "file": "api_conversation_history.json",
            "messages": [
                {"type": "say", "say": "text", "ts": 1710000000000, "text": "Hello"},
            ],
        }])
        result = submit.extract_tool_calls(history)
        calls = json.loads(result)
        assert calls == []

    def test_handles_malformed_tool_request_text(self):
        history = json.dumps([{
            "taskId": "task_001",
            "file": "api_conversation_history.json",
            "messages": [
                {
                    "type": "say",
                    "say": "mcp_server_request_started",
                    "ts": 1710000000000,
                    "text": "not valid json{{{",
                },
            ],
        }])
        result = submit.extract_tool_calls(history)
        calls = json.loads(result)
        assert calls == []

    def test_fallback_name_field(self):
        """Tests the fallback from tool_name to name field."""
        history = json.dumps([{
            "taskId": "task_001",
            "file": "api_conversation_history.json",
            "messages": [
                {
                    "type": "say",
                    "say": "mcp_server_request_started",
                    "ts": 1710000000000,
                    "text": json.dumps({"name": "get_alarm_history", "input": {"alarm": "cpu-high"}}),
                },
            ],
        }])
        result = submit.extract_tool_calls(history)
        calls = json.loads(result)
        assert len(calls) == 1
        assert calls[0]["tool_name"] == "get_alarm_history"
        assert calls[0]["parameters"] == {"alarm": "cpu-high"}

    def test_mixed_mcp_and_tool_use(self):
        """Both mcp_server_request_started and content tool_use in same conversation."""
        history = json.dumps([{
            "taskId": "task_001",
            "file": "api_conversation_history.json",
            "messages": [
                {
                    "type": "say",
                    "say": "mcp_server_request_started",
                    "ts": 1710000000000,
                    "text": json.dumps({"tool_name": "get_logs", "arguments": {}}),
                },
                {
                    "type": "assistant",
                    "ts": 1710000060000,
                    "content": [
                        {"type": "tool_use", "name": "describe_resource", "input": {"id": "rds-1"}},
                    ],
                },
            ],
        }])
        result = submit.extract_tool_calls(history)
        calls = json.loads(result)
        assert len(calls) == 2
        assert calls[0]["tool_name"] == "get_logs"
        assert calls[1]["tool_name"] == "describe_resource"


# ---------------------------------------------------------------------------
# MCP transport (mocked)
# ---------------------------------------------------------------------------


class TestMcpPost:
    def test_sends_correct_request(self):
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = b'{"result": "ok"}'
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.__enter__ = mock.MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = mock.MagicMock(return_value=False)

        with mock.patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
            body, headers = submit.mcp_post("sid-123", {"jsonrpc": "2.0", "id": 1})

        assert body == '{"result": "ok"}'
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Content-type") == "application/json"
        assert req.get_header("Mcp-session-id") == "sid-123"

    def test_no_session_id_header_when_empty(self):
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = b'{}'
        mock_resp.headers = {}
        mock_resp.__enter__ = mock.MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = mock.MagicMock(return_value=False)

        with mock.patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
            submit.mcp_post("", {"jsonrpc": "2.0"})

        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Mcp-session-id") is None


class TestInitMcpSession:
    def test_returns_session_id(self):
        with mock.patch.object(submit, "mcp_post") as mock_post:
            mock_post.return_value = ("", {"mcp-session-id": "abc-123"})
            sid = submit.init_mcp_session()

        assert sid == "abc-123"
        assert mock_post.call_count == 2  # initialize + notifications/initialized

    def test_raises_on_missing_session_id(self):
        with mock.patch.object(submit, "mcp_post") as mock_post:
            mock_post.return_value = ("", {})
            with pytest.raises(RuntimeError, match="no session ID"):
                submit.init_mcp_session()

    def test_case_insensitive_header(self):
        with mock.patch.object(submit, "mcp_post") as mock_post:
            mock_post.return_value = ("", {"Mcp-Session-Id": "def-456"})
            sid = submit.init_mcp_session()
        assert sid == "def-456"


class TestCallTool:
    def test_successful_call(self):
        response = {
            "result": {
                "content": [{"text": '{"status": "ok", "rca_size_bytes": 500}'}]
            }
        }
        with mock.patch.object(submit, "mcp_post") as mock_post:
            mock_post.return_value = (json.dumps(response), {})
            result = submit.call_tool("sid", "submit_rca_v2", {"rca_summary": "test"})

        assert result == {"status": "ok", "rca_size_bytes": 500}

    def test_error_response_raises(self):
        response = {"error": {"message": "Tool not found"}}
        with mock.patch.object(submit, "mcp_post") as mock_post:
            mock_post.return_value = (json.dumps(response), {})
            with pytest.raises(RuntimeError, match="Tool not found"):
                submit.call_tool("sid", "bad_tool", {})

    def test_error_without_message(self):
        response = {"error": {"code": -32601}}
        with mock.patch.object(submit, "mcp_post") as mock_post:
            mock_post.return_value = (json.dumps(response), {})
            with pytest.raises(RuntimeError):
                submit.call_tool("sid", "bad_tool", {})


# ---------------------------------------------------------------------------
# main() integration
# ---------------------------------------------------------------------------


class TestMain:
    def test_full_flow_with_cline_history(self, tmp_repo, cline_tasks_dir):
        with (
            mock.patch.object(submit, "init_mcp_session", return_value="sid-test"),
            mock.patch.object(submit, "call_tool") as mock_call,
            mock.patch.object(submit, "find_cline_history_dir", return_value=cline_tasks_dir),
            mock.patch("submit.Path") as mock_path_cls,
        ):
            # Make Path(__file__).resolve().parent.parent return tmp_repo
            mock_path_cls.return_value.resolve.return_value.parent.parent = tmp_repo
            mock_path_cls.home = Path.home

            mock_call.side_effect = [
                {"status": "ok", "rca_size_bytes": 200, "cline_history_size_bytes": 5000},
                {"tool_calls_made": 5},
            ]

            submit.main()

        # submit_rca_v2 called with all three fields
        first_call = mock_call.call_args_list[0]
        assert first_call[0][1] == "submit_rca_v2"
        args = first_call[0][2]
        assert "rca_summary" in args
        assert "cline_history" in args
        assert "tool_call_summary" in args

        # end_session called
        second_call = mock_call.call_args_list[1]
        assert second_call[0][1] == "end_session"

    def test_fallback_to_submit_rca(self, tmp_repo):
        with (
            mock.patch.object(submit, "init_mcp_session", return_value="sid-test"),
            mock.patch.object(submit, "call_tool") as mock_call,
            mock.patch.object(submit, "find_cline_history_dir", return_value=None),
            mock.patch("submit.Path") as mock_path_cls,
        ):
            mock_path_cls.return_value.resolve.return_value.parent.parent = tmp_repo
            mock_path_cls.home = Path.home

            # submit_rca_v2 fails, submit_rca succeeds
            mock_call.side_effect = [
                RuntimeError("Unknown tool"),
                {"status": "ok"},
                {"tool_calls_made": 1},
            ]

            submit.main()

        # Fell back to submit_rca
        assert mock_call.call_args_list[1][0][1] == "submit_rca"

    def test_exits_on_mcp_connection_failure(self, tmp_repo):
        with (
            mock.patch.object(submit, "init_mcp_session", side_effect=Exception("Connection refused")),
            mock.patch.object(submit, "find_cline_history_dir", return_value=None),
            mock.patch("submit.Path") as mock_path_cls,
        ):
            mock_path_cls.return_value.resolve.return_value.parent.parent = tmp_repo
            mock_path_cls.home = Path.home

            with pytest.raises(SystemExit) as exc_info:
                submit.main()
            assert exc_info.value.code == 1
