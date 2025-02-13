---
title: Flutter-parse stack under security lens
description: >-
  I decided to build a social app rapidly, and I managed to get the first version up and running in less than a month. Here are some tips and tricks I picked up along the way! 🚀
author: 3zcs
date: 2025-02-10 20:55:00 +0800
categories: [Blogging]
tags: [software development]
pin: true
---

If you choose to go with Flutter and Parse, it likely means you're prioritizing speed—just as I did with [oweekn](https://oweekn.netlify.app/). Before publishing the app, I wanted to understand what’s happening under the hood.  

Both Flutter and Parse offer rapid development, but this convenience often comes with hidden complexities. They abstract many details, which could potentially introduce security risks in the app and its data.  

Let's divide our investigation into two parts:  
- **Flutter (Frontend):** While Flutter supports all platforms, we'll focus on Android.  
- **Parse (Backend):** Examining its implications on security and architecture.  


# Flutter - Android  

Let's start with the basics: reversing the app. We'll extract the package using `apktool`, then ask and answer some questions along the way.  

### How do you know if an app is made with Flutter?  

While analyzing the extracted files, I came across several cues. One indicator is the presence of certain package names in the manifest, such as `flutter_image_picker_file_paths`.  

However, a more reliable way to confirm is by checking the `libflutter.so` file inside `app/lib/arm64-v8a/`. Unlike manifest entries, which depend on the libraries the developer used, the `.so` files remain the same across all Flutter APKs.  

### What are `.so` files in Flutter?  

Flutter uses **Ahead-of-Time (AOT) compilation** to generate native code on almost all environments—except for the web, where it performs transpilation using `dart2js`.  

When navigating to the `arm64-v8a` directory (`cd app/lib/arm64-v8a/`), you'll find two `.so` files:  

- **`libapp.so`** – Contains the compiled Dart code, including everything we wrote in our app.  
- **`libflutter.so`** – Contains the Flutter engine, which includes the Dart runtime, UI rendering, and runtime management.  

This means that a Flutter APK includes both the **app logic** (our Dart code) and an **environment to run it** (a lightweight Dart VM).  


Using the `file` command on `libapp.so`, we can inspect its properties:  

```console
file libapp.so    
libapp.so: ELF 64-bit LSB shared object, ARM aarch64, version 1 (SYSV), dynamically linked, BuildID[md5/uuid]=369f5a6f3ecd546b4822a5e27e51fd78, stripped
```
From this output, we can see that the app is stripped (a release version), meaning it contains no symbols. This makes reverse engineering a Flutter app more difficult than a typical Android app.

If we want to hook a function, it will require additional effort since we don't have easy-to-read function names available.

### Intercepting Traffic Between Flutter and Parse  

Our main interest is understanding the communication between **Flutter and Parse**, so I'll attempt to intercept the network traffic.  

Even though I have access to the **source code**—which allows me to manipulate traffic or log requests—I'm more interested in what an **attacker** would actually see.  

### Traditional Approach: Using BurpSuite  

Normally, intercepting traffic on Android is straightforward using **BurpSuite** with a proxy set in the WiFi settings. However, **Flutter behaves differently**, as its proxy settings are managed within the Flutter engine (`libflutter.so`).  

### Investigating Flutter's Network Behavior  

Looking into the Flutter engine's source code, particularly the **socket implementation**, we can find how Flutter establishes connections. In **[socket.cc](https://blog.weghos.com/flutter/engine/third_party/dart/runtime/bin/socket.cc.html)**, there's a function named `Socket_CreateConnect`:  

```c++
void FUNCTION_NAME(Socket_CreateConnect)(Dart_NativeArguments args) {
  RawAddr addr;
  SocketAddress::GetSockAddr(Dart_GetNativeArgument(args, 1), &addr); // <--- address
  Dart_Handle port_arg = Dart_GetNativeArgument(args, 2);
  int64_t port = DartUtils::GetInt64ValueCheckRange(port_arg, 0, 65535); 
  SocketAddress::SetAddrPort(&addr, static_cast<intptr_t>(port)); // <--- port
}
```
This function handles creating and connecting sockets, extracting the destination address and port from the Dart arguments. Understanding this function helps us determine how Flutter manages network connections, which is crucial for bypassing proxy settings and intercepting traffic.

### Manipulating the Address and Port for Proxy Interception  

To intercept traffic, we need to **redirect network requests** to our Burp proxy by manipulating the **address and port** used by Flutter.  

I tried several pre-built tools, but none provided reliable results—until I came across **[frida-flutterproxy](https://github.com/hackcatml/frida-flutterproxy.git)**. This tool implements a **universal solution** for both **iOS and Android** using a **Frida script**.  

### Hooking the App with Frida  

Once I hooked the app using `frida-flutterproxy`, the communication between the client and server started appearing in **cleartext**.  

> ⚠️ **Note:** You need a **rooted device** to use this method. I previously wrote about achieving **silent root through an N-day vulnerability** [here](/posts/2024-07-07-rooting-through-n-day.md).  

![Interception](/assets/img/parse-burp.png)  
*Network communication intercepted using BurpSuite.

### Implications of Traffic Manipulation  

Now that we can **alter and modify** communication between the client and server, this opens the door to **various attack vectors**, including:  
- **Man-in-the-Middle (MitM) attacks**  
- **Request/Response tampering**  
- **Session hijacking**  

### Next: Understanding Parse Security Mechanisms  

Now, let's dive deeper into **Parse security** and explore how it protects against these threats.  


## Parse  

When building a Parse-powered app, you start with **zero backend code**, which makes development incredibly fast. However, by default, this also means **your app accepts everything** since all **CRUD operations** happen on the **client side**.  

Parse provides multiple layers of **security** to help protect your app, including:  
- **Access Control Lists (ACLs)**  
- **Class-Level Permissions (CLPs)**  
- **Cloud Functions**  

Let's briefly explore each one.  

---

### **Access Control List (ACL)**  

ACLs define who can **read** and **write** specific objects. When creating an item, you can restrict access to specific users.  

#### Example: Setting ACL in Flutter  
```shell
#flutter
Future<void> createFileWithACL(String userId) async {
  // Get the user object
  final userQuery = QueryBuilder<ParseUser>(ParseUser.forQuery())
    ..whereEqualTo("objectId", userId);
  final userResult = await userQuery.query();

  if (userResult.success && userResult.results!.isNotEmpty) {
    final user = userResult.results!.first as ParseUser;

    // Define ACL
    ParseACL acl = ParseACL();
    acl.setReadAccess(user, true);  // Grant read access to the user
    acl.setWriteAccess(user, false); // Deny write access to the user

    // Create object
    final fileObject = ParseObject("Files")
      ..set("name", "example.txt")
      ..setACL(acl); // Apply ACL

    final response = await fileObject.save();
    if (response.success) {
      print("File created with ACL");
    } else {
      print("Error: ${response.error?.message}");
    }
  } else {
    print("User not found");
  }
}
```
Here, we're **restricting access** to the created file, ensuring that only the **specified user** can **read** it but **cannot modify** it.  

---

## **Class-Level Permissions (CLP)**  

Class-Level Permissions (**CLPs**) define **access controls at the table level** in the database. These rules apply to the **entire class** rather than individual objects.  

### **How to Configure CLPs in Parse**  
1. **Go to**: **Parse Dashboard** → **Class** → **Security** → **Advanced**  
2. **Define access**:  
   - **Public** access  
   - **Restricted to authenticated users**  
   - **Limited to predefined users/roles**  

### **Best Practice: Lock Everything First**  

A great **security principle** when using Parse is:  

> _"The default permission should be **no access at all**. Lock down every table, then grant access only as needed."_  

By default, Parse **allows full access**, but as a developer, you should **hide everything first** and **gradually grant permissions** based on feature requirements.  

---

## **Cloud Functions**  

Cloud Functions in Parse are similar to **API endpoints**. They allow you to enforce **business logic** on the backend to ensure security.  

### **Example: Enforcing Authorization in a Cloud Function**  
```javascript
Parse.Cloud.beforeSave("Post", async (request) => {
    const user = request.user;  // Get the logged-in user
    const post = request.object; // Get the post being saved

    if (!user) {
        throw new Parse.Error(403, "User must be logged in.");
    }

    const userName = user.get("name");  // Get the user's name from ParseUser
    const creatorName = post.get("creatorName"); // Get the creator's name from the post

    if (userName !== creatorName) {
        throw new Parse.Error(403, "Creator name does not match the authenticated user's name.");
    }
    
    // If names match, allow post creation
});
```
This function ensures that **only the logged-in user** can create posts under their name. If an attacker **intercepts a request** and **modifies the creator name**, the backend will **reject the request**.  

---

## **Final Thoughts**  

This was just a **glimpse** into Parse's security mechanisms. While many **low-level security details** are handled automatically, having a **basic understanding** of these layers **significantly helps** in securing your app.  

By leveraging **ACLs, CLPs, and Cloud Functions**, you can ensure your **Parse backend is secure** and **resistant to common attacks**.  
