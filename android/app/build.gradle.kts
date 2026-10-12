plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "com.collectanimals.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.collectanimals.app"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
        // Phones are arm64; leaving out other ABIs keeps the APK ~15 MB smaller.
        ndk { abiFilters += listOf("arm64-v8a") }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    buildFeatures { compose = true }
    // Pokédex data (details.csv, ranges.json, california_outline.json) is shared with
    // the web app, so it's packaged straight from species/ rather than copied.
    sourceSets { getByName("main") { assets.srcDir("../../species") } }
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
    implementation("com.microsoft.onnxruntime:onnxruntime-android:1.20.0")
    debugImplementation("androidx.compose.ui:ui-tooling")

    testImplementation("junit:junit:4.13.2")
    // Desktop build of the same runtime, so the classifier can be checked on the JVM.
    testImplementation("com.microsoft.onnxruntime:onnxruntime:1.20.0")
    testImplementation("org.json:json:20240303")
}
