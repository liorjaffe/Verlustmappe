# 2026-11-13 - Approval for governing files

The owner approved rule 12 in the 2026-11-13 task conversation, naming `AGENTS.md` and this
decision file as its write scope. Acceptance: only rule 12 is added to `AGENTS.md`; its
size guard passes; device tests pass; pytest shows only the five known workbook failures;
and staged and unstaged diff checks pass.

Self-referential rules and their enforcement need an explicit approval gate. Existing rule 7
does not cover every change to these files. The task itself is approval when it names the
exact change; routine handoff, decisions and ordinary tests are not covered by this new rule.
