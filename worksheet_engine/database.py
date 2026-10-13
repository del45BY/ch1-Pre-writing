"""Reads the Excel database and provides the {PLACEHOLDER} engine."""
import re
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd
from .config import UNCOUNTABLE_EN

REQUIRED = ["ID", "Category", "Object_EN", "Object_ID", "Relation_EN", "Relation_ID", "Image_Prompt"]
OPTIONAL = ["Countable", "Templates", "Status"]   # optional extra columns


def safe_name(text: str) -> str:
    """Folder-safe name: 'Animals & Their Products' -> 'Animals_and_Their_Products'."""
    t = text.strip().replace("&", "and")
    t = re.sub(r"[^\w\s-]", "", t, flags=re.UNICODE)
    return re.sub(r"[\s-]+", "_", t).strip("_")


def slug(text: str) -> str:
    return safe_name(text).lower()


def _article(word: str, countable: bool) -> str:
    if not countable:
        return word.lower()
    return ("an " if word[:1].lower() in "aeiou" else "a ") + word.lower()


@dataclass
class Row:
    id: str
    category: str
    obj_en: str
    obj_id: str
    rel_en: str
    rel_id: str
    prompt: str
    countable: str = ""          # "", "Y" or "N"  (blank = auto)
    templates: str = ""          # e.g. "A,B,C" (blank = default set)
    status: str = ""
    extra: dict = field(default_factory=dict)

    # ---- helpers
    def is_countable(self, en: str) -> bool:
        if self.countable.upper() == "N":
            return False
        if self.countable.upper() == "Y":
            return True
        return en.lower() not in UNCOUNTABLE_EN

    @property
    def folder(self):
        return Path(safe_name(self.category)) / safe_name(self.obj_en)

    def tokens(self) -> dict:
        t = {
            "ID": self.id, "CATEGORY": self.category,
            "OBJECT_EN": self.obj_en, "OBJECT_ID": self.obj_id,
            "RELATION_EN": self.rel_en, "RELATION_ID": self.rel_id,
        }
        for k in ("OBJECT_EN", "OBJECT_ID", "RELATION_EN", "RELATION_ID"):
            t[k + "_LOWER"] = t[k].lower()
            t[k + "_UPPER"] = t[k].upper()
        t["A_OBJECT_EN"] = _article(self.obj_en, self.is_countable(self.obj_en))
        t["A_RELATION_EN"] = _article(self.rel_en, self.is_countable(self.rel_en))
        return t

    def fmt(self, text: str) -> str:
        """Replace {OBJECT_EN} style placeholders. Unknown placeholder -> KeyError (caught by QC)."""
        toks = self.tokens()
        return re.sub(r"\{([A-Z_]+)\}", lambda m: toks[m.group(1)], text)


def _norm_header(h: str) -> str:
    return re.sub(r"[\s]+", "_", str(h).strip()).lower()


def load_rows(path) -> list:
    df = pd.read_excel(path, dtype=str, sheet_name=0).fillna("")
    cols = {_norm_header(c): c for c in df.columns}
    missing = [c for c in REQUIRED if c.lower() not in cols]
    if missing:
        raise ValueError(f"Excel is missing columns: {missing}")
    rows = []
    for _, r in df.iterrows():
        get = lambda name: str(r[cols[name.lower()]]).strip() if name.lower() in cols else ""
        rid = get("ID")
        if not rid and not get("Object_EN"):
            continue                                  # blank line
        if rid.isdigit():
            rid = rid.zfill(3)                        # Excel turns 001 into 1
        rows.append(Row(
            id=rid, category=get("Category"),
            obj_en=get("Object_EN").title(), obj_id=get("Object_ID").title(),
            rel_en=get("Relation_EN").title(), rel_id=get("Relation_ID").title(),
            prompt=get("Image_Prompt"),
            countable=get("Countable"), templates=get("Templates"), status=get("Status"),
        ))
    return rows
