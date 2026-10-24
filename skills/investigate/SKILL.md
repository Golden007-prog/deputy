---
name: investigate
description: Send a reading-heavy question to Deputy (read-only) and get a compact answer with file:line evidence, instead of reading many files yourself. Use for "where is X handled", "how does this flow work", large log or data scans, or when the user says "/deputy:investigate".
argument-hint: "<question>"
---

# Investigate with Deputy

Deputy can list, read and search files but cannot change anything. Use it when answering would
mean reading many files, so your own context stays free for the decisions.

1. Ask one clear question, and name the folders to focus on when you know them.
2. Read Deputy's answer, then open only the few files it cites that matter for your next step.
3. Treat its conclusions as leads: confirm the important ones in the code before acting on them.

## If the user typed a question after the command

Investigate this now: $ARGUMENTS
