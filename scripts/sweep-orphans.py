#!/usr/bin/env python3
"""Delete a whitelisted set of orphan objects from Cloudflare R2.

Reads `scripts/orphan-keys.yaml` (a YAML array of exact keys) and, for
each key, head_objects then delete_objects it from $R2_BUCKET_NAME. The
script defaults to dry-run; pass `--apply` to actually delete.

The boto3 client setup mirrors `scripts/publish-pack.py` exactly so this
tool talks to the same bucket via the same credentials the publish
workflow uses.

Inputs (env, same as publish-pack.py):
  R2_ACCESS_KEY_ID
  R2_SECRET_ACCESS_KEY
  R2_ACCOUNT_ID
  R2_BUCKET_NAME

Safety:
  * Refuses to run if the whitelist is empty or contains a wildcard
    (`*`, `?`). The script never enumerates the bucket — only keys
    listed verbatim in the whitelist file are touched.
  * Dry-run is the default. `--apply` is required to delete.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import boto3
import yaml
from botocore.config import Config
from botocore.exceptions import ClientError

WHITELIST_PATH = Path(__file__).parent / "orphan-keys.yaml"


def _r2_client():
    account_id = os.environ["R2_ACCOUNT_ID"]
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def load_whitelist(path: Path) -> list[str]:
    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, list) or not raw:
        raise SystemExit(f"refusing to run: {path} is empty or not a list")
    keys: list[str] = []
    for entry in raw:
        if not isinstance(entry, str) or not entry.strip():
            raise SystemExit(f"refusing to run: non-string entry in {path}: {entry!r}")
        if "*" in entry or "?" in entry:
            raise SystemExit(f"refusing to run: wildcard in whitelist entry: {entry!r}")
        keys.append(entry)
    return keys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="actually delete (default is dry-run)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="explicitly request dry-run (the default)",
    )
    args = parser.parse_args()
    apply = args.apply and not args.dry_run

    keys = load_whitelist(WHITELIST_PATH)
    bucket = os.environ["R2_BUCKET_NAME"]
    client = _r2_client()

    mode = "APPLY" if apply else "DRY-RUN"
    print(f"[{mode}] sweeping {len(keys)} orphan key(s) from r2://{bucket}")

    swept = 0
    skipped = 0
    errors = 0
    for key in keys:
        try:
            client.head_object(Bucket=bucket, Key=key)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            status = e.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if code in ("404", "NoSuchKey", "NotFound") or status == 404:
                print(f"  - skip   {key} (already absent)")
                skipped += 1
                continue
            print(f"  ! error  {key}: {e}")
            errors += 1
            continue

        if not apply:
            print(f"  - would  {key}")
            swept += 1
            continue

        try:
            client.delete_object(Bucket=bucket, Key=key)
            print(f"  - sweep  {key}")
            swept += 1
        except ClientError as e:
            print(f"  ! error  {key}: {e}")
            errors += 1

    print(f"summary: {swept} keys swept, {skipped} skipped (not found), {errors} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
