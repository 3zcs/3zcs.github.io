---
title: Build Sqlite for Android
description: >-
  setps to build Sqlite for android
author: 3zcs
date: 2024-09-09 20:55:00 +0800
categories: [Blogging]
tags: [android]
pin: true
---

## Build Sqlite for Android

One of the essential tools in your Android development toolkit is SQLite.

When I connected to my physical device using adb, I encountered the error: `sqlite3: inaccessible or not found.`

After searching for a solution, I found several pre-built binaries for SQLite on unofficial sites. However, running these binaries with root privileges seemed like a highly questionable approach.

So, I decided to build SQLite for Android ARM myself.

## Steps to Build SQLite for Android ARM

1. Download the [Android NDK](https://developer.android.com/ndk/downloads).
2. Download the [SQLite source code](https://www.sqlite.org/download.html).

Here’s the `.sh` script I prepared and executed in the SQLite folder (feel free to customize it as needed):

```console
export NDK=/home/user/Downloads/android-ndk-r27-linux/android-ndk-r27-linux

export TOOLCHAIN=$NDK/toolchains/llvm/prebuilt/linux-x86_64

export TARGET=aarch64-linux-android

# Set this to your minSdkVersion.
export API=26
# Configure and build.
export AR=$TOOLCHAIN/bin/llvm-ar
export CC="$TOOLCHAIN/bin/clang --target=$TARGET$API"
export AS=$CC
export CXX="$TOOLCHAIN/bin/clang++ --target=$TARGET$API"
export LD=$TOOLCHAIN/bin/ld
export RANLIB=$TOOLCHAIN/bin/llvm-ranlib
export STRIP=$TOOLCHAIN/bin/llvm-strip
./configure --host $TARGET
make
```