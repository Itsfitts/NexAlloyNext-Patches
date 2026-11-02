pluginManagement {
    repositories {
        providers.gradleProperty("nexfusionMaven").orNull?.let { maven(url = it) }
        maven(url = "https://raw.githubusercontent.com/a092devs/NexFusion/maven")
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven(url = "https://api.xposed.info")
        // The NexFusion patcher API, published by https://github.com/a092devs/NexFusion.
        maven(url = providers.gradleProperty("nexfusionMaven").get())
    }
}

plugins {
    id("com.android.settings") version ("9.2.1")
}

android {
    compileSdk = 37
    minSdk = 27
}

rootProject.name = "Nexfusion-Patches"

include(":stub")
include(":bundles:nexfusion")
