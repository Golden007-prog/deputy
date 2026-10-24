---
name: consult
description: Get a cheap second opinion from Deputy (DeepSeek V4.1 Flash) with ideas, risks and alternatives, then make the final call yourself. Use before committing to an approach on a non-trivial task, when stuck on a recurring problem, before declaring a task done, or when the user says "consult" or "/deputy:consult".
argument-hint: "<question or plan>"
---

# Consult Deputy

A second model thinks differently from you, so it can surface ideas and risks you missed. It is
also weaker than you. Use it for breadth, then apply your own judgment.

## How to consult well

1. **Ask a sharp question.** State what you are deciding and include your current plan, so
   Deputy can challenge it instead of starting from zero.
2. **Use lenses for diversity.** Pass 2-3 `lenses` to get independent passes in parallel, for
   example:
   - "simplest approach that could work"
   - "edge cases and failure modes"
   - "performance and scalability"
   - "security and data handling"
   - "how this could break existing behavior"
3. **Give context** Deputy cannot discover: constraints, what you ruled out and why.
4. **Weigh the answers below your own analysis.** Treat every idea as an unverified hint. Check it
   against the code before adopting it. Discard ideas that are generic or wrong. Tell the user
   which ideas you adopted and why, briefly.

Consulting is cheap but not free, and it adds latency. Skip it for routine work.

## If the user typed a question after the command

Consult Deputy on this now, following the steps above: $ARGUMENTS
