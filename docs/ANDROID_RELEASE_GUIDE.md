# CardWise Android Release & Deployment Guide

## 1. Prerequisites
- JDK 17+ (JDK 21/25 supported).
- Android SDK Platform `android-36.1` with Build-Tools `36.1.0`.
- Gradle 8.x+ with Android Gradle Plugin (AGP) 8.x+.

---

## 2. Release Signing Configuration

### 2.1 Generating a Production Keystore
Execute using Java keytool:
```bash
keytool -genkey -v -keystore cardwise-release.keystore -alias cardwise-key \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -dname "CN=CardWise App, OU=Mobile, O=CardWise, L=Bengaluru, ST=Karnataka, C=IN"
```

### 2.2 Environment Variable Configuration
Do not commit raw passwords to source control. Set the following in CI/CD (e.g., GitHub Actions or local environment):
```bash
export KEYSTORE_PATH="/path/to/cardwise-release.keystore"
export KEYSTORE_PASSWORD="super-secret-store-password"
export KEY_ALIAS="cardwise-key"
export KEY_PASSWORD="super-secret-key-password"
```

In `android/app/build.gradle.kts`:
```kotlin
signingConfigs {
    create("release") {
        storeFile = file(System.getenv("KEYSTORE_PATH") ?: "release.keystore")
        storePassword = System.getenv("KEYSTORE_PASSWORD")
        keyAlias = System.getenv("KEY_ALIAS")
        keyPassword = System.getenv("KEY_PASSWORD")
    }
}
buildTypes {
    release {
        isMinifyEnabled = true
        isShrinkResources = true
        proguardFiles(
            getDefaultProguardFile("proguard-android-optimize.txt"),
            "proguard-rules.pro"
        )
        signingConfig = signingConfigs.getByName("release")
    }
}
```

---

## 3. Building Release Artifacts

### 3.1 Android App Bundle (AAB) for Google Play
Run from the `android/` directory:
```bash
./gradlew bundleRelease
```
Output artifact located at:
`android/app/build/outputs/bundle/release/app-release.aab`

### 3.2 Testing Signed APK Locally
```bash
./gradlew assembleRelease
adb install -r app/build/outputs/apk/release/app-release.apk
```

---

## 4. Google Play Store Readiness Checklist
- [ ] Application ID matches store listing (`com.cardwise.app`).
- [ ] Version code incremented sequentially (`versionCode` integer).
- [ ] App permissions minimized (only `POST_NOTIFICATIONS` and `INTERNET`).
- [ ] Financial declaration form completed (Declared as personal financial tracker, no banking authorization).
- [ ] Privacy policy published and linked in store metadata.
