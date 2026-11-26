#!/usr/bin/env bash
# Build the two launcher apps ("Lights" and "TV") without Gradle.
#
# Needs: a JDK (17+), and Android SDK pieces:
#   brew install --cask android-commandlinetools
#   sdkmanager "platforms;android-25" "build-tools;34.0.0"
# Output: out/MotoE-Lights.apk, out/MotoE-TV.apk
set -euo pipefail
cd "$(dirname "$0")"

SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-/opt/homebrew/share/android-commandlinetools}}"
BT="$SDK/build-tools/34.0.0"
JAR="$SDK/platforms/android-25/android.jar"
[ -f "$JAR" ] || { echo "missing $JAR (run sdkmanager, see header)"; exit 1; }

KS=out/motoe.keystore
mkdir -p out
if [ ! -f "$KS" ]; then
  keytool -genkeypair -keystore "$KS" -storepass motoe-local -keypass motoe-local \
    -alias motoe -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=MotoE Remote" >/dev/null
fi

build() {  # name package url icon [stand]
  local name=$1 pkg=$2 url=$3 icon=$4 stand=${5:-}
  local w=out/build-$icon
  rm -rf "$w" && mkdir -p "$w/res/values" "$w/gen" "$w/classes"
  for d in mdpi hdpi xhdpi; do
    mkdir -p "$w/res/mipmap-$d"
    cp "icons/$icon-$d.png" "$w/res/mipmap-$d/ic_launcher.png"
  done
  cat > "$w/res/values/strings.xml" <<EOF
<resources>
  <string name="app_name">$name</string>
  <string name="page_url">$url</string>
</resources>
EOF
  local recv="" perms="" orient=portrait
  if [ "$icon" = clock ] || [ "$icon" = stand ]; then
    orient=sensor  # clock and stand turn with the phone
    perms='    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" /><uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />'
  fi
  if [ -n "$stand" ]; then
    recv='        <receiver android:name="com.motoe.webapp.PowerReceiver"><intent-filter><action android:name="android.intent.action.ACTION_POWER_CONNECTED" /></intent-filter></receiver>'
  fi
  sed -e "s/@PACKAGE@/$pkg/" -e "s#@RECEIVER@#$recv#" -e "s#@PERMS@#$perms#" -e "s#@ORIENT@#$orient#" AndroidManifest.xml.in > "$w/AndroidManifest.xml"

  "$BT/aapt2" compile --dir "$w/res" -o "$w/res.zip"
  "$BT/aapt2" link -o "$w/base.apk" -I "$JAR" --manifest "$w/AndroidManifest.xml" \
    --java "$w/gen" --custom-package com.motoe.webapp "$w/res.zip"
  javac -source 8 -target 8 -bootclasspath "$JAR" -classpath "$JAR" -d "$w/classes" \
    "$w/gen/com/motoe/webapp/R.java" src/com/motoe/webapp/*.java 2>&1 | grep -v "warning" || true
  "$BT/d8" --min-api 21 --lib "$JAR" --output "$w" $(find "$w/classes" -name '*.class')
  (cd "$w" && zip -q base.apk classes.dex)
  "$BT/zipalign" -f 4 "$w/base.apk" "$w/aligned.apk"
  "$BT/apksigner" sign --ks "$KS" --ks-pass pass:motoe-local --key-pass pass:motoe-local \
    --out "out/MotoE-$name.apk" "$w/aligned.apk"
  echo "built out/MotoE-$name.apk"
}

build Lights com.motoe.lights http://127.0.0.1:8765/lights lights
build TV     com.motoe.tv     http://127.0.0.1:8765/tv     tv
build Clock  com.motoe.clock  http://127.0.0.1:8765/clock  clock
build Stand  com.motoe.stand  http://127.0.0.1:8765/stand  stand stand
