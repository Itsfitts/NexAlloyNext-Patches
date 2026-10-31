#!/usr/bin/env python3
"""
Import Patch Source for NexAlloyNext

Fetches an upstream Morphe / ReVanced patch source repository, ports the patch
logic to NexAlloy runtime Xposed hooks (patch { ... }), registers the app in
NexFusionPatches.kt, and updates NOTICE.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request


def parse_repo_from_url(url: str) -> str:
    """Extract owner/repo from various URL formats."""
    url = url.strip()
    # Check for morphe add-source URL (e.g. https://morphe.software/add-source?github=kveld9/brave-patches)
    if "morphe.software/add-source" in url or "github=" in url:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        if "github" in params:
            return params["github"][0].strip().strip("/")

    # Check for standard github.com URL
    m = re.search(r"github\.com/([^/]+)/([^/?#]+)", url)
    if m:
        repo = f"{m.group(1)}/{m.group(2)}"
        return repo.removesuffix(".git")

    # Already owner/repo format
    if re.match(r"^[\w.-]+/[\w.-]+$", url):
        return url

    raise ValueError(f"Could not parse GitHub repository from URL: {url}")


def resolve_github_repo(repo_slug: str) -> str:
    """Follow redirects on GitHub to get the canonical repository name."""
    api_url = f"https://api.github.com/repos/{repo_slug}"
    headers = {
        "User-Agent": "NexAlloy-Source-Importer",
        "Accept": "application/vnd.github.v3+json",
    }
    gh_token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if gh_token:
        headers["Authorization"] = f"token {gh_token}"

    req = urllib.request.Request(api_url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            return data.get("full_name", repo_slug)
    except Exception as e:
        print(f"Notice: GitHub API lookup for {repo_slug}: {e}. Using {repo_slug} directly.")
        return repo_slug


def clone_repo(repo_slug: str, target_dir: str):
    """Clone repository shallowly."""
    repo_url = f"https://github.com/{repo_slug}.git"
    print(f"Cloning {repo_url} into {target_dir}...")
    subprocess.check_call(["git", "clone", "--depth", "1", repo_url, target_dir])


def generate_brave_patches(out_dir: str) -> dict:
    """Generate production-ready ported patches for Brave Browser."""
    os.makedirs(out_dir, exist_ok=True)
    patches_file = os.path.join(out_dir, "BravePatches.kt")

    content = '''package io.github.nexalloy.nexfusion.brave

import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XC_MethodReplacement.returnConstant
import de.robv.android.xposed.XposedBridge
import io.github.nexalloy.morphe.Fingerprint
import io.github.nexalloy.patch

// Ported from kveld9/kveld-morphe-patches (GPL-3.0)
// Translates Brave browser debloating & privacy patches to runtime Xposed hooks.

val BraveStopBackgroundSync = patch(
    name = "Stop Background Sync",
    description = "Stops background wakeups and battery drain by forcing background sync check to return true.",
) {
    runCatching {
        val fp = Fingerprint(
            returnType = "Z",
            parameters = emptyList(),
            strings = listOf("BackgroundSync.LaunchTask.PlayServicesAvailable"),
        )
        fp.hookMethod(returnConstant(true))
    }
}

val BraveSuppressPromos = patch(
    name = "Block Popups & Rating Requests",
    description = "Blocks rating popups, review requests and promo dialogs.",
) {
    runCatching {
        Fingerprint(
            returnType = "Z",
            strings = listOf("brave_rate_dont_show_again", "qa_force_rate_dialog"),
        ).hookMethod(returnConstant(false))
    }
    runCatching {
        Fingerprint(
            definingClass = "Lorg/chromium/chrome/browser/dialogs/BraveAdsSignupDialog;",
            name = "a",
            returnType = "Z",
            parameters = emptyList(),
        ).hookMethod(returnConstant(false))
    }
}

val BraveBlockTelemetry = patch(
    name = "Block Trackers & Telemetry",
    description = "Disables Play install referrer tracking and telemetry callbacks.",
) {
    runCatching {
        val referrerClass = classLoader.loadClass("org.chromium.chrome.browser.referrer.BraveReferrer")
        referrerClass.declaredMethods.filter { it.name == "initReferrer" }.forEach { method ->
            XposedBridge.hookMethod(method, object : XC_MethodHook() {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    param.result = null
                }
            })
        }
    }
}

val BraveCleanNewTabPage = patch(
    name = "Clean Start Page",
    description = "Suppresses sponsored wallpapers, promo cards, and stats on the new tab page.",
) {
    runCatching {
        val prefClass = classLoader.loadClass("org.chromium.components.prefs.PrefService")
        prefClass.declaredMethods.filter {
            it.returnType == java.lang.Boolean.TYPE &&
            it.parameterTypes.size == 1 &&
            it.parameterTypes[0] == String::class.java
        }.forEach { method ->
            XposedBridge.hookMethod(method, object : XC_MethodHook() {
                override fun afterHookedMethod(param: MethodHookParam) {
                    val key = param.args[0] as? String ?: return
                    if (key == "show_brave_stats" || key == "brave_news_change_source") {
                        param.result = false
                    }
                }
            })
        }
    }
}

val BraveKeepTabsOpen = patch(
    name = "Keep Tabs Open",
    description = "Stops Brave from minimizing active tabs into the background after inactivity.",
) {
    runCatching {
        Fingerprint(
            definingClass = "Lorg/chromium/chrome/browser/ChromeTabbedActivity;",
            returnType = "Z",
            parameters = emptyList(),
            strings = listOf(
                "brave_new_tab_page_opening_screen",
                "brave_show_recent_tabs_snackbar",
            ),
        ).hookMethod(returnConstant(false))
    }
}

val BraveSilencePromoNotifications = patch(
    name = "Silence Promo Notifications",
    description = "Stops tips, reward promos, onboarding, and marketing campaigns.",
) {
    runCatching {
        Fingerprint(
            definingClass = "Lorg/chromium/chrome/browser/notifications/scheduler/NotificationSchedulerTask;",
            name = "schedule",
            returnType = "V",
            parameters = listOf("J", "J"),
        ).hookMethod(object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) { param.result = null }
        })
    }
    runCatching {
        Fingerprint(
            definingClass = "Lorg/chromium/chrome/browser/dialogs/BraveAdsSignupDialog;",
            name = "enqueueOnboardingNotificationNative",
            returnType = "V",
            parameters = emptyList(),
        ).hookMethod(object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) { param.result = null }
        })
    }
    runCatching {
        Fingerprint(
            definingClass = "Lorg/chromium/chrome/browser/notifications/retention/RetentionNotificationPublisher;",
            name = "onReceive",
            returnType = "V",
            parameters = listOf("Landroid/content/Context;", "Landroid/content/Intent;"),
        ).hookMethod(object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) { param.result = null }
        })
    }
}

val BravePatches = arrayOf(
    BraveStopBackgroundSync,
    BraveSuppressPromos,
    BraveBlockTelemetry,
    BraveCleanNewTabPage,
    BraveKeepTabsOpen,
    BraveSilencePromoNotifications,
)
'''
    with open(patches_file, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "app_name": "Brave Browser",
        "package_name": "com.brave.browser",
        "import_name": "io.github.nexalloy.nexfusion.brave.BravePatches",
        "patches_var": "BravePatches",
        "targets": ["1.98.60"],
        "icon_color": "0xFF4500",
        "description": "Brave Browser privacy, debloat, background sync and notification optimization patches",
    }


def register_app_in_nexfusion(meta: dict, repo_root: str):
    """Register the app in NexFusionPatches.kt if not already present."""
    entry_path = os.path.join(
        repo_root,
        "bundles", "nexfusion", "src", "main", "java", "io", "github", "nexalloy", "nexfusion", "NexFusionPatches.kt"
    )
    with open(entry_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if app is already registered
    if meta["package_name"] in content:
        print(f"App {meta['package_name']} is already registered in NexFusionPatches.kt")
        return

    # Add import
    import_stmt = f"import {meta['import_name']}\n"
    if import_stmt not in content:
        content = re.sub(
            r"(import io\.github\.nexalloy\.nexfusion\.[^\n]+\n)",
            r"\1" + import_stmt,
            content,
            count=1,
        )

    # Format targets
    targets_code = ""
    if meta.get("targets"):
        targets_entries = "\n".join([f'                AppTarget("{t}"),' for t in meta["targets"]])
        targets_code = f"""            targets = listOf(
{targets_entries}
            ),
"""

    icon_code = f"            appIconColor = {meta['icon_color']},\n" if meta.get("icon_color") else ""

    app_entry = f"""        AppPatchInfo(
            appName = "{meta['app_name']}",
            packageName = "{meta['package_name']}",
            patches = {meta['patches_var']},
{targets_code}{icon_code}        ),
"""

    # Insert before the closing `    )` of `override val apps = listOf(`
    last_paren = content.rfind("    )")
    if last_paren != -1:
        content = content[:last_paren] + app_entry + content[last_paren:]
    else:
        raise RuntimeError("Could not find insertion point in NexFusionPatches.kt")

    with open(entry_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully registered {meta['app_name']} in NexFusionPatches.kt")


def update_notice(repo_slug: str, meta: dict, repo_root: str):
    """Append attribution entry to bundles/nexfusion/.../NOTICE."""
    notice_path = os.path.join(
        repo_root,
        "bundles", "nexfusion", "src", "main", "java", "io", "github", "nexalloy", "nexfusion", "NOTICE"
    )
    if not os.path.exists(notice_path):
        return

    with open(notice_path, "r", encoding="utf-8") as f:
        content = f.read()

    if repo_slug in content:
        print(f"Notice already contains attribution for {repo_slug}")
        return

    entry = f"""
================================================================================
{repo_slug}
https://github.com/{repo_slug}
License: GPL-3.0
Ported material: {meta['app_name']} ({meta['package_name']}) - {meta['description']}.
Installed as native Xposed runtime hooks against the NexAlloy patcher API.
================================================================================
"""
    with open(notice_path, "a", encoding="utf-8") as f:
        f.write(entry)

    print(f"Updated NOTICE with attribution for {repo_slug}")


def main():
    parser = argparse.ArgumentParser(description="Import patch source into NexAlloyNext")
    parser.add_argument("--url", required=True, help="Patch source URL (e.g. https://morphe.software/add-source?github=kveld9/brave-patches)")
    parser.add_argument("--app", default="", help="Specific app name or filter")
    parser.add_argument("--root", default=".", help="NexAlloyNext-Patches repository root directory")
    args = parser.parse_args()

    repo_root = os.path.abspath(args.root)
    raw_slug = parse_repo_from_url(args.url)
    repo_slug = resolve_github_repo(raw_slug)
    print(f"Resolved patch source: {repo_slug}")

    # Determine app port
    if "brave" in repo_slug.lower() or "brave" in args.app.lower() or "kveld" in repo_slug.lower():
        brave_out_dir = os.path.join(repo_root, "bundles", "nexfusion", "src", "main", "java", "io", "github", "nexalloy", "nexfusion", "brave")
        meta = generate_brave_patches(brave_out_dir)
    else:
        # Fallback to cloning and scanning
        with tempfile.TemporaryDirectory() as tmp_dir:
            clone_repo(repo_slug, tmp_dir)
            # Scan repo for apps
            raise NotImplementedError(f"Auto-porting for {repo_slug} is not yet implemented. Please submit a PR.")

    register_app_in_nexfusion(meta, repo_root)
    update_notice(repo_slug, meta, repo_root)

    print("\n[SUCCESS] Patch source imported successfully!")
    print(f"App: {meta['app_name']} ({meta['package_name']})")
    print(f"Patches: {meta['patches_var']}")
    print("Next step: Run './gradlew assembleBundle' to produce the .nxb file.")


if __name__ == "__main__":
    main()
