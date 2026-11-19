# 2026-11-18 - Observer: status fields, device progress and live view

Extends `2026-11-18-static-project-overview-scope.md`; that decision remains valid except
where this one widens it. The rule is in `CONTRACT.md` §12.

## Owner approval

1. **Status fields.** From `plant/*.toml` the observer may read key paths, the `status`,
   `unit` and `source` fields, `[open]` entries, and whether a `value` field is present. It
   never reads `value`, `uncertainty` or other numeric contents.
2. **Device progress.** Per device it may show work progress derived from static facts:
   parameters with a value present, a matching device module, test references, references
   from accounting code, and validation per layer 3. Status labels and UNVERIFIED markers in
   use are shown verbatim next to it.
3. **Live view.** Besides the one-off HTML export, a manually started local process bound to
   `127.0.0.1` may regenerate the page on each request. No hook, watcher, scheduler or other
   automatic mechanism starts it.
4. **UNVERIFIED locator** (owner approval later the same day). The observer counts the word
   UNVERIFIED anywhere in a plant file and lists line numbers and enclosing TOML table names;
   it emits no line text. Restricting the count to the fields in item 1 would show 0 for files
   whose UNVERIFIED notes sit in evidence or notes tables, which would mislead. The observer
   only reads plant files; the markers stay in place for later work.
5. **Topology review.** The owner confirmed order, FC control, auxiliary-supplier marking, the
   water path and the Kaeser drive air in `tools/project_observer/topology.toml`. The four
   Rotex supplied by the Kaeser are shown but deliberately not assessed until the owner
   clarifies them. The water path (rainwater, tank, Marte filter train, BWT RO, permeate to
   the EL) is the owner's description; the Marte unit's role remains open per
   `plant/water.toml`.

## Rationale

The previous code-oriented page did not show where each device stands. The owner works
partly with provisional assumptions by necessity; these must be visible, not hidden, and
must not look confirmed. Separating work progress (facts about files) from evidence status
(verbatim labels) gives a clear overview without turning the page into an assessment.

A generator run takes about 0.2 s, so a live view is cheap. A manually started local server
keeps the page current, including uncommitted work, without hooks or background processes.

## Display rules and why

- Status labels verbatim; absolute counts with named denominators only; no ranking, colour
  grading, shares, scores or completeness percentages. Reason: the status scheme in §8 is
  still [V] and the TOML labels (GUESS, PRELIM, DERIVED, BACKLOG, OWNER_DECISION,
  DATASHEET_SECONDARY, REJECTED) do not match it; colours would imply an unapproved order,
  and DATASHEET does not mean verified (§8). Aggregate shares conflict with §7 and with
  "the weakest input determines the result".
- Unknown labels and read errors are shown, not skipped, so schema changes cannot silently
  produce a misleading page.
- Generation time, commit and uncommitted-change state are always shown, and the page states
  that it is a display, not a review or assessment, so a stale or partial page is
  recognisable.
- Progress columns are static name matches: "referenced from accounting code" does not mean
  correctly booked; "validated" stays empty until layer 3 (D34).

## Open

- A grouping of status labels for colour or ordering is deferred to the owner, together
  with the §8 status scheme.
