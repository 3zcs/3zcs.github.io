#!/usr/bin/env python3
"""Write the pages that send every old 3zcs.github.io URL to https://tech.3zcs.me.

GitHub Pages can't send real 301 redirects, so each old URL gets a small HTML page with
a canonical link, an instant meta refresh, a JavaScript location.replace and a visible
link, all to the same new URL. 404.html catches everything else (other letter case,
missing trailing slash, unknown pages), feed.xml lists the posts at their new URLs, and
sw.min.js (hand-written, not generated) removes the old theme's caching service worker.

Run from anywhere:
    python3 tools/build_redirects.py           # rewrite the pages
    python3 tools/build_redirects.py --check   # fail if the committed pages differ
"""
import html
import json
import sys
import tempfile
import xml.dom.minidom
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME = "https://tech.3zcs.me/en/"
OLD_SITE = "https://3zcs.github.io"
MOVED_ON = "2026-11-27T12:00:00+00:00"  # date of the "blog moved" entry in feed.xml

# Old path (exactly as it was live), new URL, title, published, updated (from the old feed).
POSTS = [
    ("/posts/does-the-engine-matter/", "https://tech.3zcs.me/en/does-the-engine-matter/",
     "Does the engine matter for local LLM speed on a Mac?",
     "2026-11-27T13:45:00+00:00", "2026-11-27T13:51:20+00:00"),
    ("/posts/flutter-parse-stack-under-security-lens/",
     "https://tech.3zcs.me/en/flutter-parse-stack-under-security-lens/",
     "Flutter-parse stack under security lens",
     "2025-02-10T12:55:00+00:00", "2025-02-14T05:32:40+00:00"),
    ("/posts/The-one-month-social-app/", "https://tech.3zcs.me/en/the-one-month-social-app/",
     "The one-month social app",
     "2025-02-10T12:55:00+00:00", "2025-02-13T16:24:25+00:00"),
    ("/posts/Build-sqlite-for-Android/", "https://tech.3zcs.me/en/build-sqlite-for-android/",
     "Build Sqlite for Android",
     "2024-09-09T12:55:00+00:00", "2024-09-09T12:55:00+00:00"),
    ("/posts/obtaining-my-driving-data/", "https://tech.3zcs.me/en/obtaining-my-driving-data/",
     "Obtaining my driving data",
     "2024-08-09T12:55:00+00:00", "2024-08-09T12:55:00+00:00"),
    ("/posts/rooting-through-n-day/", "https://tech.3zcs.me/en/rooting-through-n-day/",
     "Android Hidden Root through N-day",
     "2024-07-07T12:55:00+00:00", "2024-07-07T12:55:00+00:00"),
]

# Other pages the old site had (from its sitemap), all sent to the new blog's home.
OTHER_PAGES = ["/", "/about/", "/categories/", "/tags/",
               "/categories/blogging/", "/categories/ai/"] + [
    f"/tags/{t}/" for t in ["android", "pentest", "data-analysis", "software-development",
                            "llm", "local-llm", "mlx", "ollama", "lm-studio", "mac", "benchmark"]]

# Links elsewhere that use a post slug without /posts/ (blog.3zcs.me's driving_time post).
EXTRA_POST_PATHS = {"/obtaining-my-driving-data/": "https://tech.3zcs.me/en/obtaining-my-driving-data/"}

STYLE = ("body{font:18px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,"
         "Arial,sans-serif;max-width:40rem;margin:4rem auto;padding:0 1rem;color:#222;"
         "background:#fff}a{color:#0b63c4;overflow-wrap:anywhere}"
         "@media (prefers-color-scheme:dark){body{color:#ddd;background:#1b1b1e}a{color:#6cb4ff}}")


def redirect_page(target, title, heading, sentence):
    t = html.escape(target)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
<script>location.replace({json.dumps(target)});</script>
<meta http-equiv="refresh" content="0; url={t}">
<link rel="canonical" href="{t}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="/assets/img/icon.png">
<style>{STYLE}</style>
</head>
<body>
<main>
<h1>{html.escape(heading)}</h1>
<p>{html.escape(sentence)} <a href="{t}">{t}</a></p>
</main>
</body>
</html>
"""


def not_found_page():
    # Lower-case slug -> new URL; the last part of any unknown path is looked up here.
    slugs = {old.rstrip("/").rsplit("/", 1)[1].lower(): new for old, new, *_ in POSTS}
    h = html.escape(HOME)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>3zcs blog moved to tech.3zcs.me</title>
<noscript><meta http-equiv="refresh" content="0; url={h}"></noscript>
<meta name="robots" content="noindex">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="/assets/img/icon.png">
<style>{STYLE}</style>
</head>
<body>
<main>
<h1>This blog moved</h1>
<p>This blog moved to <a id="to" href="{h}">{h}</a></p>
</main>
<script>
(function () {{
  var slugs = {json.dumps(slugs, indent=2)};
  var path = location.pathname.toLowerCase()
    .replace(/\\/index\\.html?$/, "").replace(/\\.html?$/, "").replace(/\\/+$/, "");
  var to = slugs[path.slice(path.lastIndexOf("/") + 1)] || {json.dumps(HOME)};
  var link = document.getElementById("to");
  link.href = to;
  link.textContent = to;
  location.replace(to);
}})();
</script>
</body>
</html>
"""


def feed():
    e = html.escape
    entries = [f"""  <entry>
    <id>tag:3zcs.github.io,2026-11-27:moved-to-tech</id>
    <title>This blog moved to tech.3zcs.me</title>
    <link rel="alternate" type="text/html" href="{HOME}"/>
    <published>{MOVED_ON}</published>
    <updated>{MOVED_ON}</updated>
    <summary>This blog moved to {HOME}. Every post is there now; please follow the new blog for new posts.</summary>
  </entry>"""]
    for old, new, title, published, updated in POSTS:
        entries.append(f"""  <entry>
    <id>{OLD_SITE}{old}</id>
    <title>{e(title)}</title>
    <link rel="alternate" type="text/html" href="{new}"/>
    <published>{published}</published>
    <updated>{updated}</updated>
    <summary>This post moved to {new}</summary>
  </entry>""")
    body = "\n".join(entries)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <id>{OLD_SITE}/</id>
  <title>3zcs blog (moved to tech.3zcs.me)</title>
  <subtitle>This blog moved to {HOME}</subtitle>
  <updated>{MOVED_ON}</updated>
  <author><name>3zcs</name><uri>{HOME}</uri></author>
  <link rel="self" type="application/atom+xml" href="{OLD_SITE}/feed.xml"/>
  <link rel="alternate" type="text/html" href="{HOME}"/>
{body}
</feed>
"""


def pages():
    out = {}
    for old, new, title, *_ in POSTS:
        out[old] = redirect_page(new, f"{title} (moved to tech.3zcs.me)",
                                 "This post moved", "This post moved to")
    for old, new in EXTRA_POST_PATHS.items():
        out[old] = redirect_page(new, "This post moved to tech.3zcs.me",
                                 "This post moved", "This post moved to")
    for old in OTHER_PAGES:
        out[old] = redirect_page(HOME, "3zcs blog moved to tech.3zcs.me",
                                 "This blog moved", "This blog moved to")
    files = {p.strip("/") + "/index.html" if p != "/" else "index.html": text
             for p, text in out.items()}
    files["404.html"] = not_found_page()
    files["feed.xml"] = feed()
    return files


def write(root):
    for rel, text in pages().items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def check():
    xml.dom.minidom.parseString(feed().encode("utf-8"))  # raises if the feed isn't valid XML
    bad = []
    with tempfile.TemporaryDirectory() as tmp:
        write(Path(tmp))
        for rel in pages():
            committed = ROOT / rel
            if not committed.is_file() or committed.read_bytes() != (Path(tmp) / rel).read_bytes():
                bad.append(rel)
    if bad:
        print("Out of date, run python3 tools/build_redirects.py:\n  " + "\n  ".join(bad))
        return 1
    print(f"OK: {len(pages())} files match the redirect map")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        sys.exit(check())
    write(ROOT)
    print(f"Wrote {len(pages())} files")
