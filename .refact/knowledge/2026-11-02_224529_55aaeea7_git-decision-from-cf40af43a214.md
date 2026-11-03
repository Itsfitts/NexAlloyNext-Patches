---
id: 482993e5-35dc-4a23-9047-692185d84056
title: Git decision from cf40af43a214
tags:
- decision
- git
created: 2026-11-02
updated: 2026-11-02
filenames:
- bundles/nexalloy/src/test/java/io/github/nexalloy/patches/InstalledAppAuditTest.kt
links: []
kind: decision
status: proposed
superseded_by: null
deprecated_at: null
review_after: 2026-11-03
source_chat_id: null
created_at: 2026-11-03T03:45:29.482100+00:00
summary: null
description: null
entities: []
related_files: []
related_entities: []
content_hash: 90fd659f003d437a48872363082287441848778e4dcd8ce92c7e63fdca8d2999
source_tool: buddy_memory_lifecycle:git
source_confidence: 0.8199999928474426
source_trajectory_id: null
source_message_range: null
source_commit: cf40af43a21444136fcda78805194b80f1f00419
topic: null
last_used_at: null
use_count: 0
last_injected_at: null
dismissed_count: 0
source_content_hash: 90fd659f003d437a48872363082287441848778e4dcd8ce92c7e63fdca8d2999
review_needed: true
occurrences: 0
---

Git decision from cf40af43a214

Source commit: cf40af43a214
Paths: bundles/nexalloy/src/test/java/io/github/nexalloy/patches/InstalledAppAuditTest.kt
Summary: fix: make InstalledAppAuditTest tolerant of missing audit doc The docs/installed-app-patch-audit.md file is kept locally but not published to GitHub. Instead of failing the build when the file is absent, skip the schema validation gracefully. When the file is present, the full validation still runs.