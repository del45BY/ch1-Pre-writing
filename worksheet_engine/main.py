"""
CLI:  python -m worksheet_engine.main --db data/worksheet_database.xlsx --out PRODUCTS
      options: --templates A,B,C  --only 001,003  --force  --strict  --workers 4  --export-prompts

BUNDLE MODE (every page can use a DIFFERENT animal/pair; builds only bundles, not single products):
  --bundle NAME --ids 001,002,003,004,005        page 1 = row 001, page 2 = row 002 ... (cycles if fewer ids than pages)
  --bundle NAME --pages A=001,B=002,C=003        exact page -> row mapping
  --bundles-sheet [--bundle NAME]                read the 'Bundles' sheet of the Excel file (Bundle | Template | ID)
"""
import argparse
import csv
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from .config import STYLE_NEGATIVE, STYLE_SUFFIX
from .database import load_bundles, load_rows
from .qc import check_rows, row_status, write_report
from .render import build_bundle, build_pool, build_product
from .templates import DEFAULT_SET, TEMPLATES


def _job(args):
    row, pool, out, templates, force = args
    return build_product(row, pool, out, templates, force)


def _bundle_specs(a, tpl_override):
    """-> {bundle_name: [(template_key, row_id), ...]}"""
    specs = {}
    if a.bundles_sheet:
        for name, lines in load_bundles(a.db).items():
            if a.bundle and name != a.bundle:
                continue
            specs[name] = [(t or DEFAULT_SET[i % len(DEFAULT_SET)], rid) for i, (t, rid) in enumerate(lines)]
        if not specs:
            sys.exit("No bundles found (sheet 'Bundles' missing or name not matched).")
    else:
        if not a.bundle:
            sys.exit("Bundle mode needs --bundle NAME")
        if a.pages:
            pairs = [p.split("=") for p in a.pages.split(",")]
            if any(len(p) != 2 for p in pairs):
                sys.exit("--pages format: A=001,B=002,C=003")
            specs[a.bundle] = [(k.strip().upper(), rid.strip().zfill(3) if rid.strip().isdigit() else rid.strip()) for k, rid in pairs]
        elif a.ids:
            ids = [i.strip().zfill(3) if i.strip().isdigit() else i.strip() for i in a.ids.split(",")]
            keys = tpl_override or DEFAULT_SET
            specs[a.bundle] = [(k, ids[i % len(ids)]) for i, k in enumerate(keys)]
        else:
            sys.exit("Bundle mode needs --ids or --pages (or --bundles-sheet)")
    return specs


def run_bundles(a, rows, status, out):
    by_id = {r.id: r for r in rows}
    tpl_override = [t.strip().upper() for t in a.templates.split(",")] if a.templates else None
    pool = build_pool(rows)
    results = []
    for name, spec in _bundle_specs(a, tpl_override).items():
        problems = [f"unknown template '{k}'" for k, _ in spec if k not in TEMPLATES]
        problems += [f"unknown ID '{rid}'" for _, rid in spec if rid not in by_id]
        bad = [rid for _, rid in spec if rid in by_id and status[rid] == "FAIL"
               or (a.strict and rid in by_id and status[rid] == "WARN")]
        problems += [f"row {rid} did not pass QC" for rid in sorted(set(bad))]
        if problems:
            print(f"  [SKIP] bundle '{name}': " + "; ".join(problems))
            continue
        pages = [(k, by_id[rid]) for k, rid in spec]
        res = build_bundle(name, pages, pool, out, a.force)
        results.append((res, [(k, by_id[rid].obj_en + " & " + by_id[rid].rel_en) for k, rid in spec]))
        print(f"  [{'built' if res['built'] else 'same ':5}] {name}: {res['pages']} pages -> {res['folder']}")
        for k, label in results[-1][1]:
            print(f"           page {k}: {label}")
    with open(out / "manifest_bundles.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["Bundle", "Folder", "Rebuilt", "Pages", "Page_Plan"])
        for res, plan in results:
            w.writerow([res["bundle"], res["folder"], res["built"], res["pages"], " | ".join(f"{k}={l}" for k, l in plan)])
    print(f"\nDone: {len(results)} bundle(s). Output: {out.resolve()}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", required=True); ap.add_argument("--out", default="PRODUCTS")
    ap.add_argument("--templates", help="override, e.g. A,B,C,D,E,F")
    ap.add_argument("--only", help="comma list of IDs")
    ap.add_argument("--force", action="store_true", help="rebuild even if unchanged")
    ap.add_argument("--strict", action="store_true", help="treat QC warnings as failures")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--export-prompts", action="store_true", help="write image_prompts.csv for AI artwork")
    ap.add_argument("--bundle", help="bundle name (folder PRODUCTS/Bundles/<name>); with --bundles-sheet = only this bundle")
    ap.add_argument("--ids", help="bundle: row IDs in page order, e.g. 001,002,003")
    ap.add_argument("--pages", help="bundle: exact mapping, e.g. A=001,B=002,C=003")
    ap.add_argument("--bundles-sheet", action="store_true", help="bundle: read sheet 'Bundles' from the Excel file")
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

    # 2a. Bundle mode: each page may use a different row
    if a.bundle or a.ids or a.pages or a.bundles_sheet:
        return run_bundles(a, rows, status, out)

    # 2b. Build single products
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
