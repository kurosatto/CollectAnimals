import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "com.captureanimals.app"
    compileSdk = 36

    defaultConfig {
        // Permanent once uploaded to Google Play.
        applicationId = "com.captureanimals.app"
        minSdk = 26
        targetSdk = 36
        versionCode = 7
        versionName = "0.6.0"
        // Phones are arm64; leaving out other ABIs keeps the APK ~15 MB smaller.
        ndk { abiFilters += listOf("arm64-v8a") }
    }

    // Upload key for Google Play, read from android/keystore.properties (git-ignored) or,
    // on CI, from UPLOAD_* environment variables. Without either, bundleRelease still
    // builds, just unsigned. See "Release build" in the README.
    val keystoreProps = Properties().apply {
        rootProject.file("keystore.properties").takeIf { it.exists() }?.inputStream()?.use(::load)
    }
    fun signingValue(prop: String, env: String): String? =
        keystoreProps.getProperty(prop) ?: System.getenv(env)
    val uploadStoreFile = signingValue("storeFile", "UPLOAD_STORE_FILE")

    signingConfigs {
        if (uploadStoreFile != null) {
            create("upload") {
                storeFile = rootProject.file(uploadStoreFile)
                storePassword = signingValue("storePassword", "UPLOAD_STORE_PASSWORD")
                keyAlias = signingValue("keyAlias", "UPLOAD_KEY_ALIAS")
                keyPassword = signingValue("keyPassword", "UPLOAD_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfigs.findByName("upload")?.let { signingConfig = it }
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    buildFeatures { compose = true }
    // Field Guide data (details.csv, ranges.json, california_outline.json) is shared with
    // the web app, so it's packaged straight from species/ rather than copied. The same
    // goes for the website's habitat scene and Leaflet (backend/app/static).
    sourceSets { getByName("main") { assets.srcDirs("../../species", "../../backend/app/static") } }
    // The model is read straight from the APK; compressing 60 MB of floats gains little.
    androidResources { noCompress += "onnx" }
    testOptions { unitTests.isReturnDefaultValues = true }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.12.01")
    implementation(composeBom)
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.activity:activity-compose:1.9.3")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.7")
    implementation("androidx.exifinterface:exifinterface:1.3.7")
    implementation("com.microsoft.onnxruntime:onnxruntime-android:1.22.0")
    debugImplementation("androidx.compose.ui:ui-tooling")

    testImplementation("junit:junit:4.13.2")
    // Desktop build of the same runtime, so the classifier can be checked on the JVM.
    testImplementation("com.microsoft.onnxruntime:onnxruntime:1.22.0")
    testImplementation("org.json:json:20240303")
}
