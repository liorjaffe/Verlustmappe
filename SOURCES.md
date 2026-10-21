# Sources and transferability

This file is the evidence index for externally sourced numeric inputs. A short source
description in `src/verlustmappe/registry.py` or another document is not a substitute for
the full entry required here.

## Current audit state

The existing registry contains source hints, but this repository does not yet have a
central, complete set of page/table references, short verbatim quotations, and
transferability assessments for every existing external number. Auditing and migrating
those existing entries is `BACKLOG`; do not infer missing citation details. Existing
registry values are not changed by this note.

CI checks that each newly added registry key is named in this file. A key's presence alone
does not establish that its source entry is complete or that the value is transferable.

## Entry format

### `<registry key>`

- **Value and unit:** `<exact registry value and unit>`
- **Source:** `<author/manufacturer, title, edition or publication date, URL/DOI>`
- **Location:** `<page, section, table, or figure>`
- **Verbatim quote:** `"<short exact excerpt supporting the value>"`
- **Source conditions:** `<pressure, temperature, load, drive type, boundary, etc.>`
- **Transferability:** `<same/different from this plant; explain relevant differences>`
- **Registry status and uncertainty:** `<status and uncertainty; explain the basis>`
- **Used by:** `<module/function and effect>`
- **Reviewer/date:** `<human reviewer and date>`

## New externally sourced entries

No new numeric source entries were added as part of the agent-governance setup.
