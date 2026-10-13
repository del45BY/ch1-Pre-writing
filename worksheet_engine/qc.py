"""
Pre-generation quality check.  Levels: FAIL (row skipped) | WARN (built, needs human review) | PASS.
Vocabulary + translation are verified against data/approved_vocab.csv (human-curated glossary).
"""
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from reportlab.pdfbase.pdfmetrics import stringWidth
from .art import has_art
from .config import DATA, FONT_BOLD, QC
from .database import slug

TEMPLATE_PLACEHOLDER_OK = True


@dataclass
class Issue:
    row_id: str
    level: str      # FAIL | WARN
    check: str
    message: str


def load_glossary(path=DATA / "approved_vocab.csv") -> dict:
    g = {}
    if Path(path).exists():
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                g.setdefault(r["EN"].strip().lower(), set()).add(r["ID"].strip().lower())
    return g


def _system_words():
    p = Path("/usr/share/dict/words")
    return {w.strip().lower() for w in p.open(encoding="utf-8", errors="ignore")} if p.exists() else set()


def check_rows(rows, glossary=None) -> list:
    glossary = glossary if glossary is not None else load_glossary()
    sysdict = _system_words()
    issues, seen_ids, seen_pairs = [], set(), set()

    def add(r, lvl, chk, msg):
        issues.append(Issue(r.id, lvl, chk, msg))

    for r in rows:
        # --- structure
        for fld, val in [("ID", r.id), ("Category", r.category), ("Object_EN", r.obj_en), ("Object_ID", r.obj_id),
                         ("Relation_EN", r.rel_en), ("Relation_ID", r.rel_id), ("Image_Prompt", r.prompt)]:
            if not val:
                add(r, "FAIL", "required", f"{fld} is empty")
        if r.id in seen_ids:
            add(r, "FAIL", "duplicate", f"duplicate ID {r.id}")
        seen_ids.add(r.id)
        key = (r.category.lower(), r.obj_en.lower())
        if key in seen_pairs:
            add(r, "FAIL", "duplicate", f"duplicate object '{r.obj_en}' in category (output folder would collide)")
        seen_pairs.add(key)

        # --- vocabulary, spelling, translation, per word
        for en, id_, role in [(r.obj_en, r.obj_id, "Object"), (r.rel_en, r.rel_id, "Relation")]:
            if not en or not id_:
                continue
            low = en.lower()
            if not re.fullmatch(r"[A-Za-z]+(?:[ '-][A-Za-z]+)*", en):
                add(r, "FAIL", "spelling", f"{role}_EN '{en}' contains invalid characters")
            if len(en.split()) > QC["max_words"] or len(en) > QC["max_word_len"]:
                add(r, "WARN", "age-level", f"'{en}' is long ({len(en)} chars) - check it suits ages 3-5")
            if low in glossary:
                if id_.lower() not in glossary[low]:
                    add(r, "FAIL", "translation",
                        f"'{en}' -> '{id_}' differs from verified glossary: {sorted(glossary[low])}")
            else:
                add(r, "WARN", "vocabulary",
                    f"'{en}' not in approved glossary - verify age level, spelling & '{id_}' manually")
                if sysdict and low not in sysdict:
                    add(r, "WARN", "spelling", f"'{en}' not found in English dictionary")
            # printable layout: can the word stay large on the vocabulary card?
            if stringWidth(en, FONT_BOLD, QC["min_vocab_font_pt"]) > 300 or \
               stringWidth(id_, FONT_BOLD, QC["min_vocab_font_pt"] - 4) > 300:
                add(r, "WARN", "layout", f"'{en}'/'{id_}' too wide for large vocabulary text")
            # image availability
            if not has_art(en):
                add(r, "WARN", "image", f"no artwork for '{en}': add assets/images/{slug(en)}.png (generic badge used)")

        # --- image prompt relevance & style safety
        pl = r.prompt.lower()
        if r.obj_en and r.obj_en.lower() not in pl:
            add(r, "WARN", "image-match", f"Image_Prompt does not mention '{r.obj_en}'")
        for bad in QC["banned_prompt_words"]:
            if bad in pl:
                add(r, "FAIL", "image-style", f"Image_Prompt contains banned word '{bad}'")

        # --- placeholder leakage test
        try:
            r.fmt("{OBJECT_EN}{OBJECT_ID}{RELATION_EN}{RELATION_ID}{A_OBJECT_EN}")
        except KeyError as e:
            add(r, "FAIL", "placeholder", f"unknown placeholder {e}")
    return issues


def row_status(rows, issues) -> dict:
    out = {r.id: "PASS" for r in rows}
    for i in issues:
        if i.level == "FAIL":
            out[i.row_id] = "FAIL"
        elif out.get(i.row_id) != "FAIL":
            out[i.row_id] = "WARN"
    return out


def write_report(issues, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["ID", "Level", "Check", "Message"])
        for i in issues:
            w.writerow([i.row_id, i.level, i.check, i.message])
