
"""
Generate a patch list describing how to transform tetris_orig.gb -> tetris.gb.

Output format:
[
  {"address": <int>, "data": <bytes>},
  ...
]

Each entry represents one consecutive run of differing bytes.
"""

from __future__ import annotations

import argparse
import os
from typing import List, Dict, Any


def build_patch(orig: bytes, mod: bytes) -> List[Dict[str, Any]]:
    patch: List[Dict[str, Any]] = []

    min_len = min(len(orig), len(mod))
    i = 0

    # Runs of differences within the overlapping portion
    while i < min_len:
        if orig[i] == mod[i]:
            i += 1
            continue

        start = i
        i += 1
        while i < min_len and orig[i] != mod[i]:
            i += 1

        patch.append({"address": start, "data": mod[start:i]})

    # Handle appended/trimmed tails (same address semantics; you can decide later how to apply)
    if len(mod) > len(orig):
        patch.append({"address": len(orig), "data": mod[len(orig):]})
    elif len(orig) > len(mod):
        # Can't represent deletions with {"address","data"} alone.
        # We surface it as an error so you don't silently produce a wrong patch.
        raise ValueError(
            f"Original is longer than modified ({len(orig)} > {len(mod)}). "
            "This patch format cannot represent truncation/deletion."
        )

    return patch


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare two binary files and emit a patch list of consecutive differing byte runs."
    )
    parser.add_argument("--orig", default="tetris_orig.gb", help="Original file (default: tetris_orig.gb)")
    parser.add_argument("--mod", default="tetris.gb", help="Modified file (default: tetris.gb)")
    parser.add_argument(
        "--out",
        default="patch.py",
        help="Output Python file containing PATCH = [...] (default: patch.py)",
    )
    args = parser.parse_args()

    for path in (args.orig, args.mod):
        if not os.path.exists(path):
            raise FileNotFoundError(path)

    with open(args.orig, "rb") as f:
        orig = f.read()
    with open(args.mod, "rb") as f:
        mod = f.read()

    patch = build_patch(orig, mod)

    # Write as a Python module so bytes stay as bytes literals (no base64 needed)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("# Auto-generated patch data\n")
        f.write(f"# orig: {os.path.basename(args.orig)} ({len(orig)} bytes)\n")
        f.write(f"# mod : {os.path.basename(args.mod)} ({len(mod)} bytes)\n\n")
        f.write("PATCH = [\n")
        for entry in patch:
            addr = entry["address"]
            data = entry["data"]
            f.write(f"    {{'address': {hex(addr)}, 'value': {data!r}, 'domain': 'System Bus'}},\n")
        f.write("]\n")

    print(f"Wrote {len(patch)} patch chunk(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
