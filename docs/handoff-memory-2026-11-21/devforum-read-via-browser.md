---
name: devforum-read-via-browser
description: How to read the Roblox DevForum when web-fetch returns an empty 202
metadata:
  node_type: memory
  type: reference
  originSessionId: eaaae633-0702-42c2-a27c-a0661820655a
  modified: 2026-11-21T21:27:07.324Z
---

The web-fetch agent gets HTTP 202 with an empty body from devforum.roblox.com. The built-in browser works: open any
DevForum page, then use fetch() in javascript_tool against Discourse's JSON endpoints (same origin):
- `/c/updates/announcements/36.json?page=N`: the announcement list (title, id, date, likes)
- `/t/<id>.json`: a topic; `post_stream.posts[0].cooked` is the first post's HTML
- `/top.json?period=monthly`: the month's top topics
Pause ~0.5 s between calls (it rate-limits).
