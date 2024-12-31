---
title: Android Hidden Root through N-day
description: >-
  rooting through N-day
author: 3zcs
date: 2024-07-07 20:55:00 +0800
categories: [Blogging]
tags: [android, pentest]
pin: true
---

## Android Hidden Root through N-day
When I am doing a sort of PT or even exploring an app, a critical issue that can be time-consuming is root detection bypass, the same technique used around the world by using the [Magisk](https://github.com/topjohnwu/Magisk) tool and then patching an Android image with a root.

As this is the standard way of gaining root privilege, Apps detect that either manually or using some known library.

I came across [securitylab](https://github.com/github/securitylab/tree/main/SecurityExploits/Android) , and I found that they have many Android exploits for patched Vulrnablity (N-days), I tried some of them and it worked, it gave me a a root shell.

that made me want to dig a bit deep by downloading some apps with root detection mitigation like banking apps, also I made an app with a known library to check how things going on. with this technique, you'll literally have a rooted shell almost impossible to be detected.

Here we'll take a look at a specific bug which is GHSL-2023-005 but the process should be the same more or less for other bugs.

To start, you should have pixel device, then search in the repo the vulnerable android version, something like this

```google/oriole/oriole:13/TQ1A.230105.002/9325679:user/release-keys```

then download it from Android [factory images](https://developers.google.com/android/images), make sure to download the compatible  image with your pixel model.

have a copy from [securitylab](https://github.com/github/securitylab/tree/main/SecurityExploits/Android) in your machine, compile and push the executable then run it.

here is a video that shows how it works with normal root 

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/qq0KQ1My2VM/0.jpg)](https://www.youtube.com/watch?v=qq0KQ1My2VM)