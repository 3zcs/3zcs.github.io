---
layout: default
---

## Build Sqlite for Android

One of the important tools for your arsenal when it comes to Android is SQLITE

when I connect to my physical device through `adb` I found out that `sqlite3: inaccessible or not found`

I searched for a solution and found much pre-built binary for sqlite3 from the non-official site, and running these with root privilege is such a ridiculous idea.

so I decided to build sqlite for android arm

I started by downloading [androind ndk](https://developer.android.com/ndk/downloads), then downloading [sqlite source code](https://www.sqlite.org/download.html)

I prepare this `.sh` file and execute  it on the sqlite folder (customize it as you need)
```
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
