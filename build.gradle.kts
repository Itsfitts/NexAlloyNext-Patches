// Puts the Android Gradle Plugin on the classpath of all projects, via the build logic of patch bundles.
plugins {
    alias(libs.plugins.nexfusion.bundle) apply false
}
