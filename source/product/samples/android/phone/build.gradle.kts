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
}
