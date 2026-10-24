---
name: investigate
description: Send a reading-heavy question to Deputy (read-only) and get file:line leads, instead of reading many files yourself. Use for "where is X handled", "how does this flow work", large log scans, or when the user says "/deputy:investigate".
argument-hint: "<question>"
---

# Investigate with Deputy

Deputy can list, read and search files but cannot change anything.

1. Ask one clear question; name the folders to focus on if you know them.
2. Treat the answer as leads. Read the cited lines yourself before acting on them.

## If the user typed a question after the command

Investigate this now: $ARGUMENTS
