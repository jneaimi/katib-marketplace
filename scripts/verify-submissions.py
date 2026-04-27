#!/usr/bin/env python3
"""Verify changed `.katib-pack` submissions in a PR.

Reads paths from the CHANGED_FILES env var (newline-separated, set by the
GitHub Action). For each `submissions/**/*.katib-pack`, runs `katib verify`
against it and prints a summary on stdout (the workflow renders this as a
sticky PR comment).

Exits non-zero if any pack fails verification — fails the PR check.

When no packs changed (e.g. a docs- or workflow-only PR landed in this
file's path filter), the script exits 0 with a no-op message.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml


def changed_packs() -> list[Path]:
    raw = os.environ.get("CHANGED_FILES", "").strip()
    if not raw:
        return []
    return [
        Path(line)
        for line in raw.splitlines()
        if line.startswith("submissions/") and line.endswith(".katib-pack")
    ]


def extract_pack_metadata(pack_path: Path) -> dict:
    """Read pack.yaml from the pack tarball without fully extracting."""
    import tarfile

    with tarfile.open(pack_path, "r:gz") as tf:
        member = next((m for m in tf.getmembers() if m.name.endswith("pack.yaml")), None)
        if member is None:
            return {"error": "pack.yaml not found"}
        f = tf.extractfile(member)
        if f is None:
            return {"error": "pack.yaml unreadable"}
        try:
            return yaml.safe_load(f.read())
        except yaml.YAMLError as e:
            return {"error": f"pack.yaml invalid: {e}"}


def verify_one(pack_path: Path) -> tuple[bool, str]:
    """Run `katib verify` against the pack. Returns (passed, output)."""
    result = subprocess.run(
        ["uv", "run", "--with", "katib", "katib", "pack", "verify", str(pack_path)],
        capture_output=True,
        text=True,
    )
    output = (result.stdout + "\n" + result.stderr).strip()
    return (result.returncode == 0, output)


def main() -> int:
    packs = changed_packs()
    if not packs:
        print("No `.katib-pack` files changed in this PR.")
        return 0

    print(f"## Verification — {len(packs)} pack(s)\n")
    overall_pass = True

    for pack in packs:
        print(f"### `{pack}`\n")
        if not pack.exists():
            print(f"- ❌ File not found at `{pack}` (was it deleted?)")
            overall_pass = False
            continue

        meta = extract_pack_metadata(pack)
        if "error" in meta:
            print(f"- ❌ {meta['error']}")
            overall_pass = False
            continue

        print(f"- name: `{meta.get('name', '?')}`")
        print(f"- version: `{meta.get('version', '?')}`")
        print(f"- pack_format: `{meta.get('pack_format', '?')}`")
        if "description" in meta:
            print(f"- description: {meta['description']!r}")

        passed, output = verify_one(pack)
        if passed:
            print("- ✅ `katib verify` passed\n")
        else:
            print("- ❌ `katib verify` failed:")
            print("```")
            print(output[:2000])
            print("```\n")
            overall_pass = False

    print("---")
    print(f"**Overall:** {'✅ all packs verified' if overall_pass else '❌ one or more packs failed'}")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
