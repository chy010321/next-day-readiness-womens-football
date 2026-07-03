#!/usr/bin/env python3
"""Verify the tested fingerprint of the official SoccerMon subjective.zip archive."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXPECTED_MD5 = "a3e86aeca611f77c9331a535eae00bf7"
EXPECTED_SHA256 = "338e9878fbed1f941cfc37b3f012cb356f97cc0f726e80a79aa5c8e67cc2a87c"


def digest(path: Path, name: str) -> str:
    hasher = hashlib.new(name)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-zip", required=True, type=Path)
    args = parser.parse_args()
    path = args.data_zip.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Source archive not found: {path}")
    observed_md5 = digest(path, "md5")
    observed_sha256 = digest(path, "sha256")
    print(f"MD5:    {observed_md5}")
    print(f"SHA256: {observed_sha256}")
    if observed_md5 != EXPECTED_MD5 or observed_sha256 != EXPECTED_SHA256:
        raise SystemExit("Source archive fingerprint does not match the archive validated for v1.1.1.")
    print("PASS: source archive fingerprint matches the v1.1.1 validation archive.")


if __name__ == "__main__":
    main()
