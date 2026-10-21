# Rules log

This log records why repository-level working rules exist. It is not a substitute for
the binding rules in `AGENTS.md`.

| Rule | Reason |
|---|---|
| Unknown values remain `BACKLOG`; agents must not invent limits or assumptions. | Prevent plausible-looking but unsupported values from entering the model. |
| Registry value changes require written owner approval. | Keep the parameter source of truth under human control. |
| External numbers include location, quote, and transferability. | Make it possible to audit whether published or datasheet values apply to this plant. |
| Tests use independent expected values and cannot be weakened silently. | Avoid self-confirming tests and preserve regression evidence. |
| Balances do not book unexplained residuals as physical losses. | Prevent unrelated errors from being hidden in a plug term. |
| Changes are restricted to task Write-Scope and reports include evidence. | Keep delegated work reviewable and reproducible. |
| Physical units are explicit at module boundaries; README demo numbers are generated. | Reduce unit ambiguity and documentation drift. |

These rules were transcribed from the project owner's supplied `AGENTS.md` on 2026-10-21.
