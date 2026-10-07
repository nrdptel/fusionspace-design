// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// The phone app: Pad, Track and the Live Update, compiled from the published files in product/ (not copies of them).
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
}

val repo = extra["repo"] as File

android {
    namespace = "co.fusionspace.sample"
    compileSdk = 37
    defaultConfig {
        applicationId = "co.fusionspace.sample"
        minSdk = 31
        targetSdk = 37
        versionCode = 1
        versionName = "1.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
    sourceSets["main"].kotlin.srcDirs(
        repo.resolve("product/tokens"),          // FusionSpaceColors.kt (the only Kotlin file there)
        repo.resolve("product/mobile/compose"),  // FsComponents.kt, FsLiveUpdate.kt
    )
    buildFeatures { compose = true }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    implementation(platform("androidx.compose:compose-bom:2026.09.00"))
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material:material-icons-core:1.7.8")
    implementation("androidx.activity:activity-compose:1.13.0")
    implementation("androidx.core:core-ktx:1.19.1")

    // Accessibility checks (Accessibility Test Framework) on the screens: gradle :phone:connectedDebugAndroidTest
    androidTestImplementation(platform("androidx.compose:compose-bom:2026.09.00"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4-accessibility")
    androidTestImplementation("androidx.test.ext:junit:1.3.0")
    androidTestImplementation("androidx.test:runner:1.7.0")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.7.0")  // 3.5 (Compose's) can't inject input on API 37
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
