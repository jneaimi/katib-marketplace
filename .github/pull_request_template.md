<!-- Pack submission PR template -->

## Pack details

- **Pack:** `<author>/<name>`
- **Version:** `x.y.z`
- **Type:** [ ] Recipe  [ ] Component  [ ] Brand  [ ] Bundle
- **Languages:** [ ] EN  [ ] AR  [ ] Bilingual

## What changed

<!-- For new packs: 1-2 sentences on what this pack is for and who it's for. -->
<!-- For new versions: changelog entry — what fixed / added / breaking. -->

## Local verification

```
$ uv run scripts/pack.py verify <pack-file>
<paste output>
```

## Smoke test (optional but encouraged)

<!-- Render the pack into a sandbox install and confirm the PDF builds clean. -->

```
$ HOME=/tmp/sandbox uv run scripts/pack.py import <pack-file>
$ HOME=/tmp/sandbox uv run scripts/build.py <recipe>
```

## Checklist

- [ ] Pack file added at `submissions/<author>/<name>/<version>.katib-pack`
- [ ] No existing version overwritten (versions are immutable)
- [ ] `katib verify` passes locally
- [ ] PR title is `<author>/<name>@<version> — <one-line summary>`
