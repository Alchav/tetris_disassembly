#!/usr/bin/env python3
"""
Compare tetris_orig.gb vs tetris.gb and emit patch chunks as tuples:
(address, "System Bus", [int, int, ...])

Each tuple is one consecutive run of differing bytes.
"""

from __future__ import annotations

import argparse
import os
from typing import List, Tuple


DOMAIN = "ROM"


def build_patch(orig: bytes, mod: bytes) -> List[Tuple[int, str, List[int]]]:
    patch: List[Tuple[int, str, List[int]]] = []

    min_len = min(len(orig), len(mod))
    i = 0

    # Differences within overlapping portion
    while i < min_len:
        if orig[i] == mod[i]:
            i += 1
            continue

        start = i
        i += 1
        while i < min_len and orig[i] != mod[i]:
            i += 1

        patch.append((start, DOMAIN, list(mod[start:i])))

    # Handle appended bytes (modified longer than original)
    if len(mod) > len(orig):
        patch.append((len(orig), DOMAIN, list(mod[len(orig):])))
    elif len(orig) > len(mod):
        raise ValueError(
            f"Original is longer than modified ({len(orig)} > {len(mod)}). "
            "This patch format cannot represent truncation/deletion."
        )

    return patch


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate consecutive diff chunks to patch orig ROM into modified ROM."
    )
    parser.add_argument("--orig", default="tetris_orig.gb", help="Original ROM")
    parser.add_argument("--mod", default="tetris.gb", help="Modified ROM")
    parser.add_argument("--out", default="/home/alchav/PycharmProjects/Archipelago/worlds/tetris_gb/patch.py", help="Output Python file")
    args = parser.parse_args()

    for path in (args.orig, args.mod):
        if not os.path.exists(path):
            raise FileNotFoundError(path)

    with open(args.orig, "rb") as f:
        orig = f.read()
    with open(args.mod, "rb") as f:
        mod = f.read()

    patch = build_patch(orig, mod)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("# Auto-generated patch data\n")
        f.write(f"# orig: {os.path.basename(args.orig)} ({len(orig)} bytes)\n")
        f.write(f"# mod : {os.path.basename(args.mod)} ({len(mod)} bytes)\n\n")
        f.write("PATCH = [\n")
        for address, domain, values in patch:
            f.write(f"    (0x{address:x}, {values}, {domain!r}),\n")
        f.write("]\n")

    print(f"Wrote {len(patch)} patch chunk(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
