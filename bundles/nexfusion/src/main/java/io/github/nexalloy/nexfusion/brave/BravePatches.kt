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
