---
id: "b6362ec5-bc06-4970-9e5d-fbf9daed89f0"
title: "Git decision from ffdc0f5879a8"
kind: decision
created: 2026-11-02
updated: 2026-11-02
review_after: 2026-11-03
status: proposed
tags: ["decision", "git"]
filenames: ["bundles/nexfusion/src/main/java/io/github/nexfusion/morphe/shared/misc/litho/filter/LithoFilterPatch.kt", "bundles/nexfusion/src/main/java/io/github/nexfusion/morphe/shared/misc/proto/ElementProtoParserHookPatch.kt", "bundles/nexfusion/src/main/java/io/github/nexfusion/morphe/youtube/YoutubeHook.kt", "bundles/nexfusion/src/main/java/io/github/nexfusion/morphe/youtube/interaction/shorts/SkipLiveShortsPatch.kt", "bundles/nexfusion/src/main/java/io/github/nexfusion/morphe/youtube/interaction/swipecontrols/SwipeControlsPatch.kt", "bundles/nexfusion/src/main/java/io/github/nexfusion/morphe/youtube/layout/buttons/navigation/Fingerprints.kt", "bundles/nexfusion/src/main/java/io/github/nexfusion/morphe/youtube/layout/buttons/navigation/NavigationBarPatch.kt", "bundles/nexfusion/src/main/java/io/github/nexfusion/morphe/youtube/layout/captions/CaptionsInPipPatch.kt", "bundles/nexfusion/src/main/java/io/github/nexfusion/morphe/youtube/layout/captions/Fingerprints.kt", "bundles/nexfusion/src/main/java/io/github/nexfusion/morphe/youtube/layout/hide/ambientmode/AmbientModePatch.kt", "bundles/nexfusion/src/main/java/io/github/nexfusion/morphe/youtube/layout/hide/ambientmode/Fingerprints.kt", "bundles/nexfusion/src/main/java/io/github/nexfusion/morphe/youtube/layout/hide/general/Fingerprints.kt"]
created_at: "2026-11-03T03:45:29.710181200+00:00"
content_hash: "d2f1c4117d2f50924632b7b5980705c910ad577c1d1966316ee5fc740de4d218"
source_tool: "buddy_memory_lifecycle:git"
source_confidence: 0.820
source_commit: "ffdc0f5879a87ce850dda9318030350e0d1579b0"
source_content_hash: "d2f1c4117d2f50924632b7b5980705c910ad577c1d1966316ee5fc740de4d218"
review_needed: true
---

Git decision from ffdc0f5879a8

Source commit: ffdc0f5879a8
Paths: bundles/nexalloy/src/main/java/io/github/nexalloy/morphe/shared/misc/litho/filter/LithoFilterPatch.kt, bundles/nexalloy/src/main/java/io/github/nexalloy/morphe/shared/misc/proto/ElementProtoParserHookPatch.kt, bundles/nexalloy/src/main/java/io/github/nexalloy/morphe/youtube/YoutubeHook.kt, bundles/nexalloy/src/main/java/io/github/nexalloy/morphe/youtube/interaction/shorts/SkipLiveShortsPatch.kt, bundles/nexalloy/src/main/java/io/github/nexalloy/morphe/youtube/interaction/swipecontrols/SwipeControlsPatch.kt, bundles/nexalloy/src/main/java/io/github/nexalloy/morphe/youtube/layout/buttons/navigation/Fingerprints.kt, bundles/nexalloy/src/main/java/io/github/nexalloy/morphe/youtube/layout/buttons/navigation/NavigationBarPatch.kt, bundles/nexalloy/src/main/java/io/github/nexalloy/morphe/youtube/layout/captions/CaptionsInPipPatch.kt, bundles/nexalloy/src/main/java/io/github/nexalloy/morphe/youtube/layout/captions/Fingerprints.kt, bundles/nexalloy/src/main/java/io/github/nexalloy/morphe/youtube/layout/hide/ambientmode/AmbientModePatch.kt, bundles/nexalloy/src/main/java/io/github/nexalloy/morphe/youtube/layout/hide/ambientmode/Fingerprints.kt, bundles/nexalloy/src/main/java/io/github/nexalloy/morphe/youtube/layout/hide/general/Fingerprints.kt
Summary: fix: audit codebase, remove unwanted apps, migrate extensions, and update patch compatibility - Settings UI NPE: Handled null-key preference groups safely in sortPreferenceGroups and added SettingsSortRegressionTest. - Removed unwanted patches: Completely deleted Kleinanzeigen, Untappd, and InterPals extension patches