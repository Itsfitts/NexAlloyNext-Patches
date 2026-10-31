plugins {
    id("nexalloy.bundle")
}

android {
    namespace = "io.github.nexalloy.patches.nxb_extended"

    lint {
        abortOnError = false
    }

    defaultConfig {
        applicationId = "io.github.nexalloy.patches.nxb_extended"
        versionCode = 1
        versionName = "1.0.0"
    }
}

nexalloyBundle {
    entry = "io.github.nexalloy.nxb_extended.NxbExtendedPatches"
    author = "NexAlloy Community"
    descriptionResource = "bundle_description"
    resourcePackageId = 0x4f
    compatibilitySeries = "3.5"
    minManagerVersion = "3.5.0"
}

dependencies {
    compileOnly(libs.nexalloy.patcher)
    compileOnly(project(":stub"))
    implementation(libs.annotation)
    implementation(libs.gson)
    implementation(libs.kotlinx.coroutines.android)
    implementation(libs.lang3)
}
