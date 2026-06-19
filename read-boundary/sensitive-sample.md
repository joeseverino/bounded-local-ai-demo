---
doc_id: infra-service-handoff
title: Service Handoff Notes
doc_type: architecture_note
system: Demo
environment: local_mac
status: active
sensitivity: sensitive
last_reviewed: 2026-06-19
related_projects: []
related_assets: []
tags:
  - demo
  - handoff
---

# Service Handoff Notes

Sample `sensitive`-tier document for the demo. It holds operational handoff
detail that should be handled carefully but is not credential material.

The MCP returns this body because it is labeled `sensitive`, and it attaches a
handle-carefully advisory. This is the middle tier between `internal` (released
plainly) and `restricted` (withheld until an audited local unlock).
