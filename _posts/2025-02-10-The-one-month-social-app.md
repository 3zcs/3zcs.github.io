---
title: The one-month social app
description: >-
  I decided to build a social app rapidly, and I managed to get the first version up and running in less than a month. Here are some tips and tricks I picked up along the way! 🚀
author: 3zcs
date: 2025-02-10 20:55:00 +0800
categories: [Blogging]
tags: [software development]
pin: true
---

## The one month social app

I've been posting about my short weekend trips on Instagram for the past month, and then I thought—what if I let my friends suggest ideas for my and there weekend adventures? The idea came from the fact that I have a job and a family, but I also want to travel and have fun.

That’s how I came up with the app idea.

Now, I want to build this app, but since it’s a social app, it’s going to take a lot of work and details. So, I sdevelopemnttarted thinking about the easiest way to build it quickly, at least as an MVP. Plus, the idea might not appeal to everyone, so I’m not sure if people will actually contribute.

## Backend 
I started looking for the fastest way to set up a backend and came across Parse, which is a Backend-as-a-Service (BaaS). It turned out to be the perfect solution for quickly building an app.

While exploring it, I decided to speed things up even more by dockerizing everything in one YAML file.

```yaml
services:
  mongo:
    image: mongo:latest
    container_name: my-mongo-instance
    ports:
      - "27018:27017"
    volumes:
      - mongo-data:/data/db

  parse-server:
    image: parseplatform/parse-server:latest
    container_name: my-parse-server
    ports:
      - "1337:1337"
    volumes:
      - config-vol:/parse-server/config
      - mya-pp/parse-server/cloud:/parse-server/cloud
    environment:
      - PARSE_SERVER_APPLICATION_ID=nweeknid
      - PARSE_SERVER_MASTER_KEY=mnweeknkey
      - PARSE_SERVER_DATABASE_URI=mongodb://mongo/nweekn
      - PARSE_SERVER_CLOUD=/parse-server/cloud/main.js
      - PARSE_SERVER_MASTER_KEY_IPS=172.18.0.0/16
    depends_on:
      - mongo

  parse-dashboard:
    image: parseplatform/parse-dashboard:latest
    container_name: parse-dashboard
    user: root
    ports:
      - "4040:4040"
    volumes:
    - ./parse-dashboard-config.json:/Parse-Dashboard/parse-dashboard-config.json
    command: ["--config", "/Parse-Dashboard/parse-dashboard-config.json", "--allowInsecureHTTP", "--dev"]
    depends_on:
      - parse-server

volumes:
  mongo-data:
  config-vol:
```

 With that, I can literally spin up the whole backend (MongoDB and Parse Server) with just one click. I’ll add more improvements later.

This setup lets you start working on your app logic from day one. Plus, since Parse is open-source, you can choose to host it locally or on a server. You also get the flexibility to use a provider like Back4App and even transfer your data between them, which is a nice bonus!

## Frontend 
As a solo dev, I knew it wouldn’t make sense to code separately for each platform, so I went straight for a cross-platform framework—and I chose [Flutter](https://flutter.dev/). It’s been around for a while, is well-tested, and backed by Google.

While working on the app, I noticed that certain processes—like the app intro, registration, login, and user profile—were repetitive. So, I started [committing](https://github.com/3zcs/nweekn/commit/ba3827e957669f028d38271c1c6bde68ae0678b2) these features separately, making them reusable for future projects. This way, I can develop new apps much faster, at least for the MVP stage.

When it came to UI/UX, I’m not an expert, so I went straight to [websites](https://dribbble.com/tags/flutter-ui) that showcase designer ideas and GitHub [repos](https://github.com/olayemii/flutter-ui-kits) where UI creators share their work. I found plenty of [ready-to-use](https://github.com/mitesh77/Best-Flutter-UI-Templates) ideas, and for some, I had to implement them myself.

For icons and images, I found several [websites](https://www.svgrepo.com/) that provide [themed assets](https://www.flaticon.com/stickers-pack/essentials-166), which was super helpful for UI design. The key is knowing what fits your app’s look. Sometimes, you have to try an icon or image, realize it doesn’t match, and keep searching for a better one.

Building an app is an iterative process. You might have a rough idea of how everything should look, but as you work on it, things become clearer. So, don’t overthink it—just start, and as you go, you’ll get a better vision of your project!


## **Landing Page**  

I was looking for a landing page that required minimal editing, and I came across **[Sandoche](https://github.com/sandoche/Mobile-app-landingpage-template)**—a beautiful and simple landing page template.  

While building the page, I encountered a few issues. To make deployment easier, I **forked** the project, **Dockerized** it, and used it. You can find the **Dockerized version** along with instructions on how to build and use it [here](https://github.com/3zcs/Mobile-app-landingpage-template/tree/dockrize).  

---

## **Before You Leave**  

- You can check out the app **[Oweekn](https://oweekn.netlify.app/)**.  
- I also wrote another blog post about the **security aspects of this app**, which you can find [here](_posts/2025-02-13-flutter-parse-stack-under-security-lens.md).  
