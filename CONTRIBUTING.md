# Contributing a pack

> **Phase 6** accepts submissions only from `jneaimi/*` while the pipeline
> hardens. Community submissions open in Phase 7 with auth + signing.

## Submitting a pack

1. **Build the pack** from your Katib install:
   ```bash
   uv run scripts/pack.py export --recipe my-recipe        # or --component / --brand / --bundle
   # writes ./my-recipe-1.0.0.katib-pack
   ```

2. **Verify locally** before submitting:
   ```bash
   uv run scripts/pack.py verify ./my-recipe-1.0.0.katib-pack
   ```
   All five refusal classes must pass: schema, hash, format version, component
   audit, recipe references.

3. **Open a PR against this repo** that adds the pack file at:
   ```
   submissions/<author>/<name>/<version>.katib-pack
   ```
   For example: `submissions/jneaimi/financial-invoice/1.0.0.katib-pack`

4. **CI runs `katib verify`** on the new file. Failure = PR can't merge until
   fixed. The bot posts a comment summarising what was found in `pack.yaml`.

5. **Reviewer (Jasem) merges.** On merge:
   - The pack is uploaded to `https://packs.jneaimi.com/<author>/<name>/<version>.katib-pack`
   - Metadata is posted to the registry API
   - The pack appears on `https://jneaimi.com/katib` within 5 minutes (ISR
     revalidate window) — no website redeploy needed

## What makes a good pack

- **A real document need.** Packs are templates someone other than the author
  will use.
- **Bilingual where it makes sense.** Most domains (legal, business, formal)
  benefit from EN + AR; tutorial / portfolio packs may be EN-only.
- **A clear `description`.** One sentence in the pack's primary language.
  This is what shows up in the marketplace card.
- **Tags that match real searches.** `invoice` not `invoicing-system-template`.
- **MIT or compatible license.** No paid packs in Phase 6.

## Versioning

Pack versions follow semver. To publish a new version:

1. Bump the version in your local `pack.yaml`
2. Re-run `uv run scripts/pack.py export ...`
3. PR adds `submissions/<author>/<name>/<new-version>.katib-pack` (don't
   modify the existing one — versions are immutable once published)

The registry tracks all versions; the latest non-deprecated one is what
`katib pack install <author>/<name>` resolves to by default.

## Deprecating a pack version

To mark a version deprecated, open a PR that touches the version's row in
the future `deprecation-list.yaml` (TBD — file format will land with the
first deprecation). The pack file stays in place; the registry stops
recommending it.

## Questions

Open an issue. The repo owner is
[@jneaimi](https://github.com/jneaimi).
