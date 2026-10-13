"""
CLI:  python -m worksheet_engine.main --db data/worksheet_database.xlsx --out PRODUCTS
      options: --templates A,B,C  --only 001,003  --force  --strict  --workers 4  --export-prompts
"""
import argparse
import csv
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from .config import STYLE_NEGATIVE, STYLE_SUFFIX
from .database import load_rows
from .qc import check_rows, row_status, write_report
from .render import build_pool, build_product
from .templates import TEMPLATES


def _job(args):
    row, pool, out, templates, force = args
    return build_product(row, pool, out, templates, force)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", required=True); ap.add_argument("--out", default="PRODUCTS")
    ap.add_argument("--templates", help="override, e.g. A,B,C,D,E,F")
    ap.add_argument("--only", help="comma list of IDs")
    ap.add_argument("--force", action="store_true", help="rebuild even if unchanged")
    ap.add_argument("--strict", action="store_true", help="treat QC warnings as failures")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--export-prompts", action="store_true", help="write image_prompts.csv for AI artwork")
    a = ap.parse_args(argv)

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rows = load_rows(a.db)
    print(f"Loaded {len(rows)} rows from {a.db}")

    # 1. QC
    issues = check_rows(rows)
    status = row_status(rows, issues)
    write_report(issues, out / "qc_report.csv")
    for r in rows:
        print(f"  [{status[r.id]:4}] {r.id} {r.obj_en} / {r.rel_en}")
    for i in issues:
        print(f"         {i.level} {i.row_id} ({i.check}): {i.message}")

    if a.export_prompts:
        with open(out / "image_prompts.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["ID", "Item", "Prompt", "Negative", "Filename"])
            for r in rows:
                for item, fn in ((r.obj_en, r.obj_en), (r.rel_en, r.rel_en)):
                    w.writerow([r.id, item, f"{r.prompt}, {STYLE_SUFFIX}" if item == r.obj_en else
                                f"cute {item.lower()}, {STYLE_SUFFIX}", STYLE_NEGATIVE, f"{fn.lower()}.png"])

    # 2. Build
    ok = {"PASS"} if a.strict else {"PASS", "WARN"}
    only = set(a.only.split(",")) if a.only else None
    templates = [t.strip().upper() for t in a.templates.split(",")] if a.templates else None
    if templates and any(t not in TEMPLATES for t in templates):
        sys.exit(f"Unknown template in {templates}")
    pool = build_pool(rows)
    jobs = [(r, pool, out, templates, a.force) for r in rows
            if status[r.id] in ok and (not only or r.id in only)]
    results = []
    if a.workers > 1:
        with ProcessPoolExecutor(a.workers) as ex:
            for f in as_completed([ex.submit(_job, j) for j in jobs]):
                results.append(f.result())
    else:
        results = [_job(j) for j in jobs]

    # 3. Manifest (feed to your shop/upload scripts)
    results.sort(key=lambda r: r["id"])
    with open(out / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["ID", "Folder", "Rebuilt", "Pages", "QC"])
        for r in results:
            w.writerow([r["id"], r["folder"], r["built"], r["pages"], status[r["id"]]])
    built = sum(r["built"] for r in results)
    print(f"\nDone: {built} built, {len(results) - built} unchanged, "
          f"{len(rows) - len(jobs)} skipped (QC fail / filtered).  Output: {out.resolve()}")


if __name__ == "__main__":
    main()
