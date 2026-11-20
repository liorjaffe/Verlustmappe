# 2026-11-19 - Observer: owner-written project summary row

Extends `2026-11-18-static-project-overview-scope.md` and
`2026-11-18-observer-status-fields-and-live-view.md`; both remain valid. Expansion of the
observer per `CONTRACT.md` §12 ("any other expansion requires a separate owner decision").

## Owner approval

1. The observer shows one row at the top of the header with three owner-written sentences:
   "My goal", "What I have to do", "Where I am at".
2. The sentences live in `tools/project_observer/summary.toml` (keys `goal`, `todo`,
   `status`) and are shown verbatim. The owner edits them there; the observer never derives,
   shortens or rewrites them.
3. Initial wording is taken from the owner's status slide (19 Nov 2026).

## Rules

- Display only: the sentences are orientation, not evidence, not project truth for values
  and not a model input. They do not change the meaning of any other observer view.
- A missing file shows no row. A read error or unknown key is shown in the header, not
  skipped (same rule as for other observer inputs).

## Rationale

The owner wants the project's goal, plan and current state readable at a glance in the
observer, in the same plain words used for status reporting.
