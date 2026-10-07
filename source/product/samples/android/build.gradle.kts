// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
import com.android.build.api.variant.ApplicationAndroidComponentsExtension

plugins {
    id("com.android.application") version "9.4.1" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.4.20" apply false
}

/** The repository's root: the sample compiles product/ and bundles type/fonts from there instead of copying them. */
val repo: File = rootDir.resolve("../../../..").canonicalFile

/**
 * Resources taken from the repository at build time instead of committed twice: Cascadia Mono (SIL OFL) from type/fonts into
 * res/font, the FusionSpace icons from product/icons/android into res/drawable, and the adaptive app icon from
 * kit/apps/android into res/mipmap.
 */
abstract class FsResources : DefaultTask() {
    @get:InputFiles abstract val fonts: ConfigurableFileCollection
    @get:InputFiles abstract val icons: ConfigurableFileCollection
    @get:InputDirectory abstract val launcher: DirectoryProperty
    @get:OutputDirectory abstract val outputDir: DirectoryProperty

    @TaskAction fun copy() {
        val root = outputDir.get().asFile.apply { deleteRecursively() }
        val font = root.resolve("font").apply { mkdirs() }
        val drawable = root.resolve("drawable").apply { mkdirs() }
        fonts.forEach { it.copyTo(font.resolve(it.name.replace("CascadiaMono", "cascadia_mono").replace('-', '_').lowercase()), true) }
        // The icons tint with ?attr/colorControlNormal, which only exists with AppCompat; this app has none, so point
        // them at the framework's attribute of the same name.
        icons.forEach { drawable.resolve(it.name).writeText(it.readText().replace("?attr/colorControlNormal", "?android:attr/colorControlNormal")) }
        val kit = launcher.get().asFile
        kit.resolve("ic_launcher.xml").copyTo(root.resolve("mipmap-anydpi/ic_launcher.xml"), true)
        for (layer in listOf("background", "foreground", "monochrome"))
            kit.resolve("ic_launcher_$layer.png").copyTo(root.resolve("mipmap-xxxhdpi/ic_launcher_$layer.png"), true)
    }
}

subprojects {
    extra["repo"] = repo
    pluginManager.withPlugin("com.android.application") {
        val res = tasks.register<FsResources>("fsResources") {
            fonts.from(repo.resolve("type/fonts/CascadiaMono-Regular.ttf"), repo.resolve("type/fonts/CascadiaMono-SemiBold.ttf"))
            icons.from(fileTree(repo.resolve("product/icons/android")) { include("*.xml") }) // all; R8 drops unused ones in release
            launcher.set(repo.resolve("kit/apps/android"))
            outputDir.set(layout.buildDirectory.dir("generated/fsResources"))
        }
        extensions.getByType<ApplicationAndroidComponentsExtension>().onVariants { variant ->
            variant.sources.res?.addGeneratedSourceDirectory(res, FsResources::outputDir)
        }
    }
}
