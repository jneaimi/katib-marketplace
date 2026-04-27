# Katib Marketplace

Curated registry for [Katib](https://github.com/jneaimi/katib) packs — recipes,
components, and brand profiles you can install with one CLI command.

```bash
katib pack install jneaimi/financial-invoice
```

Browse the live catalog at <https://jneaimi.com/katib>.

## What's in this repo

This is the **submission + curation pipeline**. Packs land here as PRs, get
reviewed, and on merge are published to:

- **Pack blobs** → Cloudflare R2 (`packs.jneaimi.com`)
- **Registry index + metadata** → Postgres on Coolify, queryable via the
  `https://jneaimi.com/api/katib/registry` endpoint

The Katib engine itself lives at [`jneaimi/katib`](https://github.com/jneaimi/katib).

## Status

**Phase 6 — Read-only marketplace MVP** (per
[ADR R4](https://github.com/jneaimi/katib/blob/main/docs/adr-marketplace.md)).

- ✅ R2 bucket + custom domain
- ✅ Postgres schema
- ⏳ Curation CI pipeline (this repo)
- ⏳ Browse UI at `jneaimi.com/katib`

## Contributing a pack

See [CONTRIBUTING.md](./CONTRIBUTING.md) for the submission flow.

Phase 6 accepts packs **only from Jasem** (`jneaimi/*`) while the pipeline
hardens. Phase 7 (community uploads with auth + signing) is a separate ADR
not yet started.

## Repo layout

```
submissions/
  <author>/<name>/<version>.katib-pack    one file per published version
scripts/
  verify-submissions.py                   runs katib verify on changed packs
  publish-pack.py                         uploads to R2 + POSTs metadata
.github/workflows/
  pr-verify.yml                           PR check
  publish-on-merge.yml                    publish on merge to main
```

## License

MIT — see [LICENSE](./LICENSE).
