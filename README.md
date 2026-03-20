# DevOps RCA Assessment — Candidate Instructions

## Overview

Welcome to the Trilogy DevOps Root Cause Analysis (RCA) Real Work Assignment. This assessment evaluates your ability to investigate a production incident using AI-powered tools and write a professional RCA report.

You will use **Cline** (the AI assistant pre-installed in this Codespace) to connect to an MCP server that provides investigation tools for a production incident: **PRODUCT-48517**.

**Time Limit**: 120 minutes from session start.

---

## Prerequisites

- Your **Submission ID** (shown on the SurveyMonkey form that brought you here)
- Your **Crossover candidate email address**

---

## Getting Started

### Step 1: Configure Cline API

Cline is pre-installed in this Codespace. Configure it to use our API:

1. Open Cline from the VS Code sidebar (robot icon)
2. Open Cline settings (from the Cline landing page → **Bring my own API key**, or press `F1` → **Cline: Focus on View** → Settings wheel → **API Configuration** tab)
3. Set the following:
   - **Provider**: `OpenAI Compatible`
   - **Base URL**: `https://wnogqpmdu74ndach7m36xntowe0ecgzb.lambda-url.us-east-1.on.aws/v1/`
   - **API Key**: Your **Submission ID** (from the SurveyMonkey form)
   - **Model ID**: `gpt-5.2`
4. Click Continue
5. Do **NOT** use GitHub Copilot or any other AI assistant — use only Cline

### Step 2: Connect to the MCP Server

Configure Cline's MCP connection to the assessment server:

1. In the Cline panel, click the **Server Type** icon (stacked layers icon in the top bar)
2. Click **Remote MCP Servers**
3. Enter:
   - **Name**: `devops-rca` (or any name you prefer)
   - **URL**: `https://hiring.devops.trilogy.com/mcp`
   - **Transport Type**: `Streamable HTTP`
4. Click **Add Server** — you should see the available investigation tools listed
5. Click Done button to proceed further

### Step 3: Start Your Session

Ask Cline to call the `start_session` tool with:
- Your **Submission ID**
- Your **full name**
- Your **email address**

This validates your identity and starts a **120-minute timed session**.

### Step 4: Investigate the Incident

Use Cline to investigate **PRODUCT-48517** using the available tools:

| Tool | Purpose |
|------|---------|
| `get_cloudwatch_metrics` | Query CloudWatch metrics (CPU, memory, error rates, latency, etc.) |
| `get_logs` | Search CloudWatch Logs for application logs, error messages, stack traces |
| `describe_resource` | Inspect AWS resources (EC2 instances, RDS databases, ECS services, etc.) |
| `get_alarm_history` | View CloudWatch alarm state changes and triggers |
| `get_jira_issue` | Read JIRA tickets for incident details, comments, and related issues |

### Step 5: Write Your RCA Report

Create your RCA report in **`RCA_REPORT.md`** at the root of this repository. Use `RCA_TEMPLATE.md` as your starting point.

Focus on technical accuracy and evidence. No need for long prose — fill out every section with specific data from your investigation.

### Step 6: Submit

Run from the terminal:

```bash
./submit YOUR_SUBMISSION_ID
```

Replace `YOUR_SUBMISSION_ID` with the Submission ID from the SurveyMonkey form.

This automatically:
- Captures your RCA report from `RCA_REPORT.md`
- Captures your Cline conversation history
- Submits everything to the assessment server
- Ends your session

**Do not manually call `end_session`** — the submit script handles this.

---

## How You Will Be Evaluated

- **Root cause identification** — Did you find the infrastructure, monitoring, and process root causes?
- **Investigation methodology** — Was your approach systematic and evidence-driven?
- **Fix recommendations** — Are your proposed fixes specific and actionable?
- **Technical correctness** — Are your conclusions supported by data?
- **AI usage quality** — Did you drive the investigation, or did you let AI run autonomously?

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Session required" error | Ask Cline to call `start_session` first |
| "No active session" after already starting | Cline may have reconnected to the MCP server (new transport session). Simply ask Cline to call `start_session` again with the same credentials — the server will automatically resume your existing session and timer. |
| "SF validation failed" | Double-check your Submission ID |
| "Rate limited" | Wait a moment, then try again (max 30 calls/minute) |
| Connection timeout | Verify your MCP server URL in Cline MCP settings |
| Session expired | Your 120-minute window has elapsed — contact your recruiter |
| Cline can't connect to MCP | Ensure the server URL is `https://hiring.devops.trilogy.com/mcp` |

---

## Important Rules

- Use **only Cline** for AI assistance. Do not use ChatGPT, Claude.ai, GitHub Copilot, or any other external AI tool.
- Do not share your MCP server URL or session credentials.
- Your Cline conversation history is **automatically captured and reviewed** as part of the assessment.
- Write your RCA in `RCA_REPORT.md` — the submit script looks for this file.

---

## Support

If you experience technical issues with the Codespace or MCP server (not the assessment content), contact your recruiter who will escalate to the DevOps team.

Good luck!
