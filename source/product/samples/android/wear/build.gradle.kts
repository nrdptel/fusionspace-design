// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// The Wear OS app: Find, Pad and Unfired, the Find tile and complication, compiled from product/watch/compose in place.
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
}

val repo = extra["repo"] as File

android {
    namespace = "co.fusionspace.sample.wear"
    compileSdk = 37
    defaultConfig {
        applicationId = "co.fusionspace.sample.wear"
        minSdk = 33  // Wear OS 4
        targetSdk = 37
        versionCode = 1
        versionName = "1.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
    sourceSets["main"].kotlin.srcDirs(repo.resolve("product/watch/compose"))  // FsWear.kt, FsWearTile.kt
    buildFeatures { compose = true }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    implementation(platform("androidx.compose:compose-bom:2026.09.00"))
    implementation("androidx.wear.compose:compose-material3:1.7.0")
    implementation("androidx.wear.compose:compose-foundation:1.7.0")
    implementation("androidx.activity:activity-compose:1.13.0")
    implementation("androidx.core:core-ktx:1.19.1")

    // Accessibility checks (Accessibility Test Framework) on the screens: gradle :wear:connectedDebugAndroidTest
    androidTestImplementation(platform("androidx.compose:compose-bom:2026.09.00"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4-accessibility")
    androidTestImplementation("androidx.test.ext:junit:1.3.0")
    androidTestImplementation("androidx.test:runner:1.7.0")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.7.0")  // 3.5 (Compose's) can't inject input on API 37
    debugImplementation("androidx.compose.ui:ui-test-manifest")
    implementation("androidx.wear:wear-ongoing:1.1.0")
    implementation("androidx.wear.tiles:tiles:1.6.2")
    implementation("androidx.wear.protolayout:protolayout:1.4.2")
    implementation("androidx.wear.protolayout:protolayout-material3:1.4.2")
    implementation("androidx.wear.watchface:watchface-complications-data-source-ktx:1.3.0")
    implementation("androidx.concurrent:concurrent-futures:1.3.0")
    implementation("com.google.guava:listenablefuture:1.0")
}
