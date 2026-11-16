# 2026-11-13 - Agent workflow clarifications

The owner approved clarifying completion with known failures, the parameter reference path,
the authority of `START.md`, and approval of exact changes recorded as owner decisions.
The owner chose a focused structure test and both diff checks for `AGENTS.md` or `START.md`
changes. Changes to the known-failures list require the full wrapper and comparison with its
output; code, data, test and gate changes also require the full wrapper.
The owner also specified that a recorded decision counts as prior approval only when recorded
before the task started, and that the full wrapper supplements the focused test.
The owner's explicit instruction in the current session also approves the exact change it names;
plant data changes require the full wrapper.

The focused test covers the enforced entry-file budgets. Checking the failure list against the
full run avoids treating an unverified list as an acceptance baseline. Neither a matching test
ID nor the wrapper alone proves that a failure has the same root cause.
