---
name: studio-sharing-and-slot2
description: How sessions share NH Combat Test Studio and protect save slot 2
metadata:
  node_type: memory
  type: feedback
  originSessionId: eaaae633-0702-42c2-a27c-a0661820655a
  modified: 2026-11-21T21:40:59.929Z
---

One session or agent drives NH Combat Test Studio at a time. Hand it over with "Studio released (<who>)" after reaching
Edit mode with slot 2 restored, and wait for "Studio released" back. Tell the holder the place has unsaved owner work:
never save, close, reload or revert the place unless the owner says so.
Slot 2 only (slot 1 is the owner's): take a FRESH snapshot at the start of each Play round and restore only from it;
record CineState/Seen/Origin before and after (an agent once overwrote the snapshot mid-session with test marks).
The Edit DataModel is unavailable while Studio is in Play, so read-only audits must wait for Edit.

**Why:** parallel sessions (Bell Tower, phase6) collided over Studio; a polluted snapshot nearly leaked test state.
**How to apply:** every Studio-using brief carries these rules; queue non-urgent Studio work behind the owner's
priority (see [[owner-priorities]]).
