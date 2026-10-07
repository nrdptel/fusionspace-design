// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// A sample Android project that runs FusionSpace's Compose reference code (product/mobile/compose, product/watch/compose)
// on a phone and a Wear OS watch. It compiles the published files in place; see README.md.
pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
}
rootProject.name = "fusionspace-android-sample"
include(":phone", ":wear")
