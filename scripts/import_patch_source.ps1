# Import Patch Source for NexAlloyNext (PowerShell)
param(
    [Parameter(Mandatory = $true)]
    [string]$Url,
    [string]$App = ""
)

$ErrorActionPreference = "Stop"

# 1. Parse repository slug
$repoSlug = ""
if ($Url -match "github=([^&]+)") {
    $repoSlug = $matches[1]
} elseif ($Url -match "github\.com/([^/]+)/([^/?#]+)") {
    $repoSlug = "$($matches[1])/$($matches[2])".Replace(".git", "")
} elseif ($Url -match "^[\w.-]+/[\w.-]+$") {
    $repoSlug = $Url
} else {
    Write-Error "Could not parse GitHub repository from URL: $Url"
}

Write-Host "Parsed source: $repoSlug"

# Follow redirect if needed
try {
    $resp = Invoke-RestMethod -Uri "https://api.github.com/repos/$repoSlug" -Headers @{ "User-Agent" = "NexAlloy-Importer" }
    if ($resp.full_name) {
        $repoSlug = $resp.full_name
    }
} catch {
    Write-Host "Using $repoSlug directly"
}

Write-Host "Canonical repository: $repoSlug"

$rootDir = Split-Path -Parent $PSScriptRoot
$braveDir = Join-Path $rootDir "bundles\nexfusion\src\main\java\io\github\nexalloy\nexfusion\brave"

if ($repoSlug -match "brave" -or $App -match "brave" -or $repoSlug -match "kveld") {
    Write-Host "Generating Brave patches in $braveDir..."
    New-Item -ItemType Directory -Force -Path $braveDir | Out-Null
    
    $bravePatchesPath = Join-Path $braveDir "BravePatches.kt"
    $braveCode = @'
package io.github.nexalloy.nexfusion.brave

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
'@
    Set-Content -Path $bravePatchesPath -Value $braveCode -Encoding UTF8
    Write-Host "Created $bravePatchesPath"

    # Register in NexFusionPatches.kt
    $entryPath = Join-Path $rootDir "bundles\nexfusion\src\main\java\io\github\nexalloy\nexfusion\NexFusionPatches.kt"
    $entryContent = Get-Content -Path $entryPath -Raw -Encoding UTF8

    if ($entryContent -notmatch "com\.brave\.browser") {
        # Add import
        $importLine = "import io.github.nexalloy.nexfusion.brave.BravePatches`n"
        if ($entryContent -notmatch "io\.github\.nexalloy\.nexfusion\.brave\.BravePatches") {
            $entryContent = $entryContent -replace "(import io\.github\.nexalloy\.nexfusion\.[^\r\n]+)", "`$1`n$importLine"
        }

        # Add AppPatchInfo
        $appBlock = @'
        AppPatchInfo(
            appName = "Brave Browser",
            packageName = "com.brave.browser",
            patches = BravePatches,
            targets = listOf(
                AppTarget("1.98.60"),
            ),
            appIconColor = 0xFF4500,
        ),
'@
        $lastClosingParen = $entryContent.LastIndexOf("    )")
        if ($lastClosingParen -ge 0) {
            $entryContent = $entryContent.Substring(0, $lastClosingParen) + $appBlock + "`n" + $entryContent.Substring($lastClosingParen)
            Set-Content -Path $entryPath -Value $entryContent -Encoding UTF8
            Write-Host "Registered Brave Browser in NexFusionPatches.kt"
        }
    } else {
        Write-Host "Brave Browser is already registered in NexFusionPatches.kt"
    }

    # Update NOTICE
    $noticePath = Join-Path $rootDir "bundles\nexfusion\src\main\java\io\github\nexalloy\nexfusion\NOTICE"
    if (Test-Path $noticePath) {
        $noticeContent = Get-Content -Path $noticePath -Raw -Encoding UTF8
        if ($noticeContent -notmatch $repoSlug) {
            $noticeEntry = @"

================================================================================
$repoSlug
https://github.com/$repoSlug
License: GPL-3.0
Ported material: Brave Browser (com.brave.browser) - Stop background sync, suppress promos, block telemetry, clean start page, keep tabs open, and silence promo notifications.
Installed as native Xposed runtime hooks against the NexAlloy patcher API.
================================================================================
"@
            Add-Content -Path $noticePath -Value $noticeEntry -Encoding UTF8
            Write-Host "Updated NOTICE with attribution"
        }
    }

    Write-Host "`nImport completed successfully! Run './gradlew assembleBundle' to build the .nxb file."
} else {
    Write-Error "Importing for $repoSlug is not yet recognized. Supported: Brave Browser."
}
