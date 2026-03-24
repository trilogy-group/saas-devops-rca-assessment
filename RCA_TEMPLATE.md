# Root Cause Analysis: [INCIDENT-KEY]

**Incident**: [Brief title]
**Date**: [YYYY-MM-DD]
**Investigator**: [Your Name]
**Investigation Date**: [Today's Date]

---

## What Happened (Technical Summary)

[Brief paragraph explaining specifically what broke technically and the immediate customer impact]

**Example for PRODUCT-123**:
> On July 25, 2025 at 09:21 UTC, the search feature became unresponsive due to a CloudFront outage in AWS. The CF rejected all HTTPS requests. The incident lasted 45 minutes until the cluster was manually scaled from 1 to 2 nodes at 09:43 UTC.

---

## Timeline

[Chronological sequence with precise timestamps and evidence]

**Format**: **HH:MM UTC** - Event description [Evidence: source]

**Example**:
- **09:21 UTC** - Search functionality becomes unresponsive, CPU spikes to 99%
- **09:25 UTC** - JIRA ticket PRODUCT-123 created by user report [Evidence: JIRA ticket]
- **09:56 UTC** - CloudFront starts rejecting HTTPS requests
- **10:06 UTC** - Incident marked resolved [Evidence: JIRA ticket]

---

## Root Cause Analysis

### Monitoring Root Cause

[Please comment on monitoring failures or potential improvements related to this incident.]

**Example** (unrelated to this incident):
> **1st Why — Q:** Why did the outage last 30 minutes before anyone noticed? **A:** The disk-space alarm never fired.
> **2nd Why — Q:** Why didn't the disk-space alarm fire? **A:** The alarm threshold was set to 95%, but the volume filled to 100% in a single burst between evaluation intervals.

1st Why — Q: [What alarm(s) should have fired but didn't?] A: [answer]
2nd Why — Q: [Why didn't that alarm fire?] A: [answer]
3rd Why — Q: A:
4th Why — Q: A:
5th Why — Q: A:

### Engineering Root Cause

[Please comment if software bugs or application behavior caused the incident.]

1st Why — Q: A:
2nd Why — Q: A:
3rd Why — Q: A:
4th Why — Q: A:
5th Why — Q: A:

### Process Root Cause (Change Management)

[Please comment if any provisioning, deployment, removal, or testing activities have impacted system stability and contributed to the incident.]

1st Why — Q: A:
2nd Why — Q: A:
3rd Why — Q: A:
4th Why — Q: A:
5th Why — Q: A:

### Infrastructure Root Cause

[Please evaluate the role of core services and components, such as databases and network infrastructure, in the incident.]

1st Why — Q: A:
2nd Why — Q: A:
3rd Why — Q: A:
4th Why — Q: A:
5th Why — Q: A:

---

## Summary

[Bullet list format at END of document - 4-6 bullets covering what happened, root causes, resolution]
**1-sentence summary**:
**1-sentence root-cause**:
**Permanent fixes**:
- Engineering team:
    [ ] fix bug 1
    [ ] ...
- DevOps team:
    [ ] fix monitoring #1
    [ ] fix infrastructure #2
    [ ] fix process #3


## Evidence Appendix

[Include key evidence snippets supporting conclusions: AWS metrics, screenshots, JIRA tickets etc]

---

---

_Note: This RCA follows the DevOps RCA standard format. All claims are supported by evidence from MCP tool queries (CloudWatch metrics, logs, alarm history, resource configs, JIRA tickets)._
