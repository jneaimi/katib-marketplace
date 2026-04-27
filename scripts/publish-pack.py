#!/usr/bin/env python3
"""Publish a verified `.katib-pack` to R2 + register it via the API.

Two side effects per pack:
  1. PUT the pack file to s3://<R2_BUCKET_NAME>/<author>/<name>/<version>.katib-pack
  2. POST the manifest to <REGISTRY_API>/admin/packs with bearer auth

Inputs (env):
  CHANGED_FILES        newline-separated paths added in the merge commit
  R2_ACCESS_KEY_ID
  R2_SECRET_ACCESS_KEY
  R2_ACCOUNT_ID
  R2_BUCKET_NAME
  KATIB_CURATION_TOKEN bearer token for the registry admin endpoint
  REGISTRY_API         e.g. https://jneaimi.com/api/katib

The file path encodes <author>/<name>/<version>:
  submissions/jneaimi/financial-invoice/1.0.0.katib-pack
                ^author    ^name        ^version
"""
from __future__ import annotations

import hashlib
import os
import re
import sys
import tarfile
from pathlib import Path

import boto3
import requests
import yaml
from botocore.config import Config

PACK_PATH_RE = re.compile(
    r"^submissions/(?P<author>[a-z][a-z0-9-]*)/(?P<name>[a-z][a-z0-9-]*)/(?P<version>[0-9.]+(?:-[a-z0-9.\-]+)?)\.katib-pack$"
)


def changed_packs() -> list[Path]:
    raw = os.environ.get("CHANGED_FILES", "").strip()
    return [
        Path(line)
        for line in raw.splitlines()
        if line.startswith("submissions/") and line.endswith(".katib-pack")
    ]


def parse_pack_path(p: Path) -> dict | None:
    m = PACK_PATH_RE.match(str(p))
    return m.groupdict() if m else None


def pack_metadata(pack_path: Path) -> dict:
    with tarfile.open(pack_path, "r:gz") as tf:
        member = next(m for m in tf.getmembers() if m.name.endswith("pack.yaml"))
        f = tf.extractfile(member)
        return yaml.safe_load(f.read())  # type: ignore[union-attr]


def upload_to_r2(pack_path: Path, key: str) -> str:
    account_id = os.environ["R2_ACCOUNT_ID"]
    bucket = os.environ["R2_BUCKET_NAME"]

    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )

    s3.upload_file(
        str(pack_path),
        bucket,
        key,
        ExtraArgs={
            "ContentType": "application/gzip",
            "CacheControl": "public, max-age=31536000, immutable",
        },
    )
    return f"https://packs.jneaimi.com/{key}"


def post_to_registry(payload: dict) -> requests.Response:
    api = os.environ["REGISTRY_API"].rstrip("/")
    token = os.environ["KATIB_CURATION_TOKEN"]
    return requests.post(
        f"{api}/admin/packs",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )


def main() -> int:
    packs = changed_packs()
    if not packs:
        print("No `.katib-pack` files in the merge commit.")
        return 0

    failed: list[str] = []
    for pack in packs:
        parsed = parse_pack_path(pack)
        if not parsed:
            print(f"❌ skip — bad path shape: {pack}")
            failed.append(str(pack))
            continue
        if not pack.exists():
            print(f"❌ skip — file missing on disk: {pack}")
            failed.append(str(pack))
            continue

        meta = pack_metadata(pack)
        size = pack.stat().st_size
        sha256 = hashlib.sha256(pack.read_bytes()).hexdigest()

        key = f"{parsed['author']}/{parsed['name']}/{parsed['version']}.katib-pack"
        print(f"📤 uploading {pack} → r2://{key}")
        download_url = upload_to_r2(pack, key)

        payload = {
            "author": parsed["author"],
            "name": parsed["name"],
            "version": parsed["version"],
            "content_hash": meta.get("content_hash") or f"sha256:{sha256}",
            "pack_format": meta.get("pack_format", 1),
            "katib_min": meta.get("requires", {}).get("katib_min", "1.0.0"),
            "bundled_components": meta.get("requires", {}).get("bundled_components", []),
            "tags": meta.get("tags", []),
            "languages": meta.get("languages", []),
            "domain": meta.get("domain"),
            "description": meta.get("description"),
            "license": meta.get("license"),
            "documentation_url": meta.get("marketplace", {}).get("documentation_url"),
            "preview_image_url": meta.get("marketplace", {}).get("preview_image"),
            "download_url": download_url,
            "size_bytes": size,
            # Slice A — discovery metadata. The admin endpoint computes
            # `kind` server-side from this; we never send `kind` directly.
            "contents": meta.get("contents", {}),
        }

        print(f"📡 POST {os.environ.get('REGISTRY_API')}/admin/packs")
        r = post_to_registry(payload)
        if r.status_code in (200, 201):
            print(f"✅ {key} registered")
        elif r.status_code == 409 and "version_exists" in r.text:
            print(f"⚠️  {key} already registered — skipping (versions are immutable)")
        else:
            print(f"❌ registry returned {r.status_code}: {r.text[:500]}")
            failed.append(str(pack))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
