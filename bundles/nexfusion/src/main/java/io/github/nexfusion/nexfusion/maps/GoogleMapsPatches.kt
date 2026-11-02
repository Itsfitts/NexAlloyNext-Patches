package io.github.nexfusion.nexfusion.maps

import android.app.Activity
import android.content.Context
import android.content.res.Configuration
import android.graphics.Color
import android.graphics.drawable.ColorDrawable
import android.view.View
import android.view.ViewGroup
import android.view.Window
import android.view.WindowManager
import android.webkit.URLUtil
import android.widget.TextView
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XC_MethodReplacement
import de.robv.android.xposed.XposedBridge
import de.robv.android.xposed.XposedHelpers
import io.github.nexfusion.PatcherLog
import io.github.nexfusion.patch

val MapsHideAds = patch(
    name = "Hide ads",
    description = "Hides promoted map pins, sponsored search result rows, navigation ad labels, and ad impression beacons in Google Maps.",
) {
    // 1. Suppress ad impression beacons and telemetry pings
    runCatching {
        XposedBridge.hookAllMethods(
            URLUtil::class.java,
            "isNetworkUrl",
            object : XC_MethodHook() {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    val url = param.args.firstOrNull() as? String ?: return
                    if (url.contains("/adview") ||
                        url.contains("google.com/adview") ||
                        url.contains("adview?avs=") ||
                        url.contains("pagead") ||
                        url.contains("googleads") ||
                        url.contains("&ved=")
                    ) {
                        param.result = false
                    }
                }
            }
        )
    }

    // 2. Filter sponsored oneof case (c == 5) from search rows and result lists
    runCatching {
        val adapterClass = runCatching { classLoader.loadClass("androidx.recyclerview.widget.RecyclerView\$Adapter") }.getOrNull()
        if (adapterClass != null) {
            XposedBridge.hookAllMethods(
                adapterClass,
                "onBindViewHolder",
                object : XC_MethodHook() {
                    override fun afterHookedMethod(param: MethodHookParam) {
                        val holder = param.args.firstOrNull() ?: return
                        val itemView = runCatching {
                            XposedHelpers.getObjectField(holder, "itemView") as? View
                        }.getOrNull() ?: return

                        itemView.scanAndCollapseAdView()
                    }
                }
            )
        }
    }

    // 3. Navigation ad label controller and promoted pin drawers
    runCatching {
        val navAdControllers = listOf(
            "com.google.android.apps.gmm.navigation.ui.NavigationAdsLabelController",
            "NavigationAdsLabelController",
        )
        for (controllerName in navAdControllers) {
            val clazz = runCatching { classLoader.loadClass(controllerName) }.getOrNull() ?: continue
            clazz.declaredMethods.forEach { method ->
                if (method.name.contains("onNavigationUiStateChanged", ignoreCase = true) ||
                    method.name.contains("draw", ignoreCase = true)
                ) {
                    XposedBridge.hookMethod(method, XC_MethodReplacement.DO_NOTHING)
                }
            }
        }
    }

    // 4. Suppress sponsored placemark objects and ad view impression pings
    runCatching {
        val metricClass = runCatching {
            classLoader.loadClass("com.google.android.apps.gmm.util.clearcut.metrics.Metrics\$IntegerMetric")
        }.getOrNull()

        if (metricClass != null) {
            val pingSenders = listOf(
                "com.google.android.apps.gmm.shared.ad.AdViewImpressionSender",
                "com.google.android.apps.gmm.search.ads.SearchAdPingSender",
            )
            for (senderName in pingSenders) {
                val clazz = runCatching { classLoader.loadClass(senderName) }.getOrNull() ?: continue
                clazz.declaredMethods.forEach { method ->
                    XposedBridge.hookMethod(method, XC_MethodReplacement.DO_NOTHING)
                }
            }
        }
    }
}

val MapsHighRefreshRate = patch(
    name = "High refresh rate",
    description = "Removes Google Maps' 60 Hz window cap and unlocks 90 Hz / 120 Hz display refresh rate and map rendering.",
) {
    // 1. Remove 60.0 Hz preferredRefreshRate cap on Window.setAttributes
    runCatching {
        XposedBridge.hookAllMethods(
            Window::class.java,
            "setAttributes",
            object : XC_MethodHook() {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    val lp = param.args.firstOrNull() as? WindowManager.LayoutParams ?: return
                    if (lp.preferredRefreshRate == 60.0f) {
                        lp.preferredRefreshRate = 0.0f
                    }
                }
            }
        )
    }

    // 2. Reset preferredRefreshRate on Activity lifecycle callbacks
    runCatching {
        XposedBridge.hookAllMethods(
            Activity::class.java,
            "onStart",
            object : XC_MethodHook() {
                override fun afterHookedMethod(param: MethodHookParam) {
                    val activity = param.thisObject as? Activity ?: return
                    val window = activity.window ?: return
                    val lp = window.attributes
                    if (lp != null && lp.preferredRefreshRate == 60.0f) {
                        lp.preferredRefreshRate = 0.0f
                        window.attributes = lp
                    }
                }
            }
        )
    }

    runCatching {
        XposedBridge.hookAllMethods(
            Activity::class.java,
            "onResume",
            object : XC_MethodHook() {
                override fun afterHookedMethod(param: MethodHookParam) {
                    val activity = param.thisObject as? Activity ?: return
                    val window = activity.window ?: return
                    val lp = window.attributes
                    if (lp != null && lp.preferredRefreshRate == 60.0f) {
                        lp.preferredRefreshRate = 0.0f
                        window.attributes = lp
                    }
                }
            }
        )
    }

    // 3. Unlock frame rate controller adaptive limits
    runCatching {
        val frameControllerClasses = listOf(
            "com.google.android.apps.gmm.mapcore.FrameRateController",
            "com.google.android.apps.gmm.mapcore.MapFrameLimiter",
        )
        for (className in frameControllerClasses) {
            val clazz = runCatching { classLoader.loadClass(className) }.getOrNull() ?: continue
            clazz.declaredMethods.forEach { method ->
                if (method.name.contains("setTargetFrameRate", ignoreCase = true) ||
                    method.name.contains("setMinAdaptiveFrameRate", ignoreCase = true)
                ) {
                    XposedBridge.hookMethod(
                        method,
                        object : XC_MethodHook() {
                            override fun beforeHookedMethod(param: MethodHookParam) {
                                // Default target rate unconstrained
                                val fps = param.args.firstOrNull() as? Long
                                if (fps != null && (fps == 0L || fps == 30L || fps == 60L)) {
                                    param.args[0] = 120L
                                }
                            }
                        }
                    )
                }
            }
        }
    }
}

val MapsDisableTelemetry = patch(
    name = "Disable telemetry",
    description = "Disables Clearcut logging, Firebase analytics, Play services compliance check-ins, and performance monitoring in Google Maps.",
) {
    // 1. Clearcut Logger
    runCatching {
        val clearcutClass = runCatching { classLoader.loadClass("com.google.android.gms.clearcut.ClearcutLogger") }.getOrNull()
        if (clearcutClass != null) {
            clearcutClass.declaredMethods.forEach { method ->
                if (method.name == "log" || method.name == "logAsync") {
                    XposedBridge.hookMethod(method, XC_MethodReplacement.DO_NOTHING)
                }
            }
        }
    }

    // 2. Firebase Analytics
    runCatching {
        val firebaseClass = runCatching { classLoader.loadClass("com.google.firebase.analytics.FirebaseAnalytics") }.getOrNull()
        if (firebaseClass != null) {
            XposedBridge.hookAllMethods(
                firebaseClass,
                "setAnalyticsCollectionEnabled",
                object : XC_MethodHook() {
                    override fun beforeHookedMethod(param: MethodHookParam) {
                        param.args[0] = false
                    }
                }
            )
            XposedBridge.hookAllMethods(
                firebaseClass,
                "logEvent",
                XC_MethodReplacement.returnConstant(null)
            )
        }
    }

    // 3. Primes Performance Monitoring
    runCatching {
        val lifeboatClass = runCatching {
            classLoader.loadClass("com.google.android.libraries.performance.primes.transmitter.LifeboatReceiver")
        }.getOrNull()
        if (lifeboatClass != null) {
            XposedBridge.hookAllMethods(lifeboatClass, "onReceive", XC_MethodReplacement.DO_NOTHING)
        }
    }
}

val MapsHideClutter = patch(
    name = "Hide clutter & AI summaries",
    description = "Hides Gemini AI summaries, Ask Maps navigation entrypoints, promotional sign-in prompts, and place sheet clutter.",
) {
    // 1. Disable Ask Maps in navigation
    runCatching {
        val askMapsClasses = listOf(
            "com.google.android.apps.gmm.features.askmaps.AskMapsNavigationFeatureAvailabilityImpl",
            "AskMapsNavigationFeatureAvailabilityImpl",
        )
        for (className in askMapsClasses) {
            val clazz = runCatching { classLoader.loadClass(className) }.getOrNull() ?: continue
            clazz.declaredMethods.filter { it.name.contains("isAskMapsInNavigationEnabled") }.forEach { method ->
                XposedBridge.hookMethod(method, XC_MethodReplacement.returnConstant(false))
            }
        }
    }

    // 2. Collapse promotional cards and AI review summaries on attach
    runCatching {
        val viewGroupClass = ViewGroup::class.java
        XposedBridge.hookAllMethods(
            viewGroupClass,
            "addView",
            object : XC_MethodHook() {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    val child = param.args.firstOrNull() as? View ?: return
                    child.scanAndCollapseClutterView()
                }
            }
        )
    }
}

val MapsBlackTheme = patch(
    name = "AMOLED black theme",
    description = "Applies pure AMOLED black backgrounds to Google Maps dark mode interface elements.",
    use = false,
) {
    runCatching {
        XposedBridge.hookAllMethods(
            Activity::class.java,
            "onPostCreate",
            object : XC_MethodHook() {
                override fun afterHookedMethod(param: MethodHookParam) {
                    val activity = param.thisObject as? Activity ?: return
                    val isDark = (activity.resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES
                    if (isDark) {
                        activity.window?.setBackgroundDrawable(ColorDrawable(Color.BLACK))
                        activity.window?.decorView?.setBackgroundColor(Color.BLACK)
                    }
                }
            }
        )
    }
}

val GoogleMapsPatches = arrayOf(
    MapsHideAds,
    MapsHighRefreshRate,
    MapsDisableTelemetry,
    MapsHideClutter,
    MapsBlackTheme,
)

private fun View.scanAndCollapseAdView() {
    val desc = contentDescription?.toString().orEmpty()
    val tag = tag?.toString().orEmpty()
    if (desc.contains("Sponsored", ignoreCase = true) ||
        desc.contains("Ad ", ignoreCase = true) ||
        desc.startsWith("Ad") ||
        tag.contains("sponsored", ignoreCase = true) ||
        tag.contains("ad_view", ignoreCase = true)
    ) {
        collapse()
        return
    }

    if (this is ViewGroup) {
        for (i in 0 until childCount) {
            val child = getChildAt(i)
            if (child is TextView) {
                val text = child.text?.toString().orEmpty()
                if (text.equals("Ad", ignoreCase = true) ||
                    text.equals("Sponsored", ignoreCase = true) ||
                    text.startsWith("Sponsored ·", ignoreCase = true)
                ) {
                    collapse()
                    return
                }
            }
        }
    }
}

private fun View.scanAndCollapseClutterView() {
    val desc = contentDescription?.toString().orEmpty()
    val tag = tag?.toString().orEmpty()
    if (desc.contains("Know before you go", ignoreCase = true) ||
        desc.contains("Summarized with Gemini", ignoreCase = true) ||
        tag.contains("SuggestPromoCard", ignoreCase = true)
    ) {
        collapse()
        return
    }

    if (this is ViewGroup) {
        for (i in 0 until childCount) {
            val child = getChildAt(i)
            if (child is TextView) {
                val text = child.text?.toString().orEmpty()
                if (text.contains("Summarized with Gemini", ignoreCase = true) ||
                    text.contains("Know before you go", ignoreCase = true) ||
                    text.contains("Ask Maps", ignoreCase = true) ||
                    text.contains("Tired of typing? Sign in", ignoreCase = true)
                ) {
                    collapse()
                    return
                }
            }
        }
    }
}

private fun View.collapse() {
    if (visibility != View.GONE) visibility = View.GONE
    val lp = layoutParams ?: return
    if (lp.height != 0) {
        lp.height = 0
        if (lp is ViewGroup.MarginLayoutParams) {
            lp.topMargin = 0
            lp.bottomMargin = 0
        }
        layoutParams = lp
    }
}

