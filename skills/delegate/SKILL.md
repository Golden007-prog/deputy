---
name: delegate
description: Hand well-specified, token-heavy coding work to the Deputy sub-agent (DeepSeek V4.1 Flash) and verify the result yourself. Use for multi-file edits, refactors, tests, boilerplate, migrations, scripts and lint/type fixes, or when the user says "deputy", "delegate" or "/deputy:delegate".
argument-hint: "<task>"
---

# Delegate to Deputy

You are the lead. Deputy is a cheaper model with its own tools (read, edit, run commands) in
this workspace. Use it to save your context and the user's money, never to skip judgment.

## How to delegate well

1. **Decide early.** Delegate before you read lots of source yourself. Use a quick file listing
   to find the area, not a deep read.
2. **Write a complete brief** in `task`:
   - the goal, in one or two sentences;
   - the files or folders in scope;
   - constraints (style, APIs to keep, what not to touch);
   - acceptance criteria, ideally a command to run (tests, build, linter).
3. **Put facts Deputy cannot discover** into `context`: decisions already made, the error
   message, conventions from CLAUDE.md, summaries of docs you looked up. Never put secrets there.
4. Use `thinking: "max"` only for hard tasks; `high` is the default.
5. **Verify.** Read the changed files listed in the result, check the diff (`git diff`), and run
   the tests. Fix small problems yourself; for bigger misses, delegate again with precise
   feedback. After two poor results in a row, stop delegating and do the work yourself.

## Keep for yourself

Architecture and design decisions, ambiguous root-cause analysis, security-sensitive changes,
tiny edits (delegation overhead is not worth it), and anything the user asked you to do.

## If the user typed a task after the command

Delegate this task now, with a brief built as described above: $ARGUMENTS
