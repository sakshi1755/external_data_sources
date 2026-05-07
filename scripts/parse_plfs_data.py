"""
Parse PLFS unit-level fixed-width .txt files into per-file CSVs.

Inputs come from each release's data dir; outputs go to clean/<release>/.
Layouts are read from clean/<release>/layout/{file_key}_layout.csv (built
by scripts/build_layouts.py).

Usage:
    python3 scripts/parse_plfs_data.py                          # all releases, all files
    python3 scripts/parse_plfs_data.py annual_2023_24           # one release
    python3 scripts/parse_plfs_data.py calendar_2024 --only chhv1
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from releases import RELEASES, ROOT


def load_layout(layout_csv: Path):
    """Return list of (field_name, start_idx, end_idx) — 0-based half-open."""
    out = []
    with layout_csv.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fn = (row["field_name"] or "").strip() or f"col_{row['srl']}"
            bs = int(row["byte_start"])
            be = int(row["byte_end"])
            out.append((fn, bs - 1, be))
    return out


def find_input(data_dir: Path, filename: str) -> Path | None:
    """Locate the .TXT file case-insensitively in data_dir."""
    target = filename.lower()
    for p in data_dir.glob("*"):
        if p.name.lower() == target:
            return p
    # fall back: stem match (e.g. CHHV1.* matches CHHV1.TXT or CHHV1.txt)
    stem = Path(filename).stem.lower()
    for p in data_dir.glob("*"):
        if p.suffix.lower() == ".txt" and p.stem.lower() == stem:
            return p
    return None


def parse_file(release_name, file_cfg):
    cfg = RELEASES[release_name]
    layout_csv = cfg["layout_dir"] / f"{file_cfg['key']}_layout.csv"
    layout = load_layout(layout_csv)

    src = find_input(cfg["data_dir"], file_cfg["data_filename"])
    if src is None:
        print(f"  SKIP {release_name}/{file_cfg['key']}: no input "
              f"{file_cfg['data_filename']} in {cfg['data_dir'].relative_to(ROOT)}")
        return None
    out = cfg["out_dir"] / f"{file_cfg['key']}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)

    expected_len = file_cfg["byte_total"]
    n = 0
    bad_len = 0
    headers = [fn for fn, _, _ in layout]
    with src.open(encoding="latin-1") as fin, out.open("w", newline="", encoding="utf-8") as fout:
        w = csv.writer(fout)
        w.writerow(headers)
        for line in fin:
            line = line.rstrip("\r\n")
            if not line:
                continue
            if len(line) < expected_len:
                bad_len += 1
                line = line.ljust(expected_len)
            row = [line[s:e].strip() for _, s, e in layout]
            w.writerow(row)
            n += 1
    rel_src = src.relative_to(ROOT)
    rel_out = out.relative_to(ROOT)
    short = f" short_lines={bad_len}" if bad_len else ""
    print(f"  {file_cfg['key']:<8} {n:>8,} rows  src={rel_src}  out={rel_out}{short}")
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "releases",
        nargs="*",
        choices=list(RELEASES),
        help="Release(s) to parse; default: all known releases",
    )
    ap.add_argument(
        "--only",
        nargs="*",
        help="If given, parse only these file keys (e.g. hhv1, perv1)",
    )
    args = ap.parse_args()
    targets = args.releases or list(RELEASES)

    grand = 0
    for r in targets:
        cfg = RELEASES[r]
        print(f"\n=== {r} — {cfg['label']} ===")
        for fc in cfg["files"]:
            if args.only and fc["key"] not in args.only:
                continue
            n = parse_file(r, fc)
            if n:
                grand += n
    print(f"\nTotal rows written: {grand:,}")


if __name__ == "__main__":
    main()
