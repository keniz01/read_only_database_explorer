---
description: Review the staged Git changes before committing (security, correctness, repo conventions).
agent: code-reviewer
---

Use the code-review skill to review the pending changes before commit. Inspect
`git diff --cached` (and `git status`) to see exactly what is about to be committed,
read the affected files, check against AGENTS.md conventions, and report findings
with a `REVIEW_VERDICT: APPROVE` or `REVIEW_VERDICT: REQUEST_CHANGES` line plus
`REQUIRED_FIXES:` and `SUGGESTED:` blocks. You are read-only; do not modify anything.