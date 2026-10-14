# Bilingual Preschool Worksheet Engine (EN / ID, ages 3-5)

One Excel row in -> a complete product folder out (PDF + preview + cover + thumbnail).
Same visual identity for every worksheet; only the learning content changes.

```
pip install -r requirements.txt
python create_sample_database.py                       # makes data/worksheet_database.xlsx (5 rows)
python -m worksheet_engine.main --db data/worksheet_database.xlsx --out PRODUCTS
```

---------------------------------------------------------------------
## 1. Worksheet template design

### Page grid (A4 portrait, 595 x 842 pt)
```
+--------------------------------------------------+  <- 12pt brand colour stripe
| [AGES 3-5 / USIA 3-5]          Name / Nama: ____ |
| Chicken & Egg            (38pt, English)         |  HEADER MODULE (178pt)
| Ayam & Telur             (21pt, Indonesian)      |
| * I can ... / Saya bisa ...   (objective strip)  |
+--------------------------------------------------+
| (A) Instruction bar  EN 18pt / ID 13pt           |
|                                                  |  CONTENT AREA (~576pt)
|   Image module  +  Activity module               |  36pt side margins,
|   +  Vocabulary module (EN above ID)             |  large objects, lots of white space
+--------------------------------------------------+
| Brand            Page 1 / 5        (c) 2026 Brand|  FOOTER MODULE (70pt)
|        licence text EN / ID                      |
+--------------------------------------------------+
```

### Modules (all in `components.py`)
| Module | Function | Content |
|---|---|---|
| Header | `header()` | age pill, name line, title EN/ID, learning objective EN/ID |
| Instruction | `instruction()` | lettered badge + bilingual instruction |
| Image | `art.draw_object()` | main + related illustration (colour / outline / shadow mode) |
| Activity | in `templates.py` | matching, tracing, colouring, cut & paste, circle, shadow match |
| Vocabulary | `word_pair()`, `vocab_card()` | English word over Indonesian word, dotted tracing |
| Footer | `footer()` | brand, page n / total, copyright, licence |

### Visual style
* Cartoon vector, 3.4 pt dark-navy outlines (`#2B2B3A`), flat fills, round shapes, smiling faces, no backgrounds.
* Palette: coral `#FF7A6B`, sky `#4FB3E8`, sun `#FFC83D`, mint `#4CC9A0`, grape `#9B7BE0` + 12% tints. One accent colour per template, all share the same stripe/header/footer.
* Type: Fredoka/Baloo if present in `assets/fonts/` (recommended), else DejaVu Sans Bold. Words 24-42 pt, instructions 13-18 pt.

### Templates (v2.0: 10 pre-writing worksheets, all follow "from {OBJECT} to {RELATION}")
| Key | Name (EN / ID) | What the child does | Layout |
|---|---|---|---|
| A | Vertical Lines / Garis Tegak | trace straight lines top to bottom | 4 tall columns (big dots, dashes, road, free draw) |
| B | Horizontal Lines / Garis Datar | trace straight lines left to right | 5 rows, easy to hard |
| C | Diagonal Lines / Garis Miring | trace slanted lines (up and down) | 2x2 panels, partner in the opposite corner |
| D | Zigzag Lines / Garis Zigzag | trace zigzags | 5 rows |
| E | Curved Lines / Garis Lengkung | trace hills, valleys, S-curves | 5 rows |
| F | Wavy Lines / Garis Gelombang | trace waves of 2, 3, 4 cycles | 5 rows |
| G | Circles & Spirals / Lingkaran & Spiral | go round circles and spirals around the picture | 2x3 panels |
| H | Mixed Patterns / Pola Campuran | trace steps, scallops, loops, zigzag+wave, square wave | 5 rows |
| I | Path Tracing / Mengikuti Jalur | follow a road; two forks: pick the road to the partner | 3 wide panels |
| J | Shape Tracing / Menebalkan Bentuk Dasar | trace circle, square, triangle, rectangle, oval, diamond | 2x3 panels |

Every line has 5 difficulty styles, easy to hard: big dots, dashes, small dots, a road to stay inside, and free draw.
Default product = A-J (10 pages). Use `--templates A,B,C` or the `Templates` column for per-row overrides.

**Legacy templates (v1.x)** are still available as `LA`..`LI`: LA Animal Matching, LB Vocabulary, LC Find and Circle,
LD Cut and Paste, LE Coloring, LF Shadow Matching, LG Counting, LH Horizontal Lines, LI Diagonal Lines.
Example: `--templates LA,LB,LC,LD,LE` rebuilds the old 5-page product, pixel-identical to v1.x.

---------------------------------------------------------------------
## 2. Database mapping rules

| Excel column | Used for | Rules |
|---|---|---|
| `ID` | unique key, random seed | text; `1` is auto-padded to `001`; duplicates = FAIL |
| `Category` | output folder | `&` -> `and`, spaces -> `_` ("Animals & Their Products" -> `Animals_and_Their_Products`) |
| `Object_EN` / `Object_ID` | main picture, title, vocabulary card #1 | auto Title Case; EN verified against glossary |
| `Relation_EN` / `Relation_ID` | related picture, vocabulary card #2 | same |
| `Image_Prompt` | AI artwork prompt (`--export-prompts`) and QC | must mention Object_EN; no banned style words |
| `Countable` (optional) | "a chicken" vs "honey" | Y / N / blank = auto (uncountable list in `config.py`) |
| `Templates` (optional) | per-row template set | e.g. `A,C,E` |

### Placeholders (any template text can use them)
`{OBJECT_EN} {OBJECT_ID} {RELATION_EN} {RELATION_ID}` plus `_LOWER` / `_UPPER` variants
(`{OBJECT_EN_LOWER}` -> "chicken"), `{A_OBJECT_EN}` -> "a chicken" / "honey", `{A_RELATION_EN}`, `{CATEGORY}`, `{ID}`.
An unknown placeholder never reaches a PDF: QC marks the row FAIL.

Example: Bee / Lebah / Honey / Madu ->
```
Bee      Honey
Lebah    Madu
"This is a bee."  "Ini adalah lebah."   "This is honey."  "Ini adalah madu."
```

### Distractors
Matching / circle / cut-paste pages need extra pictures. They come from the other database rows (+ the built-in art library),
chosen with a seed of `ID + template`, so a rebuild always gives the identical page.
Distractor *pairs* are used in A and D so every extra picture also has a valid partner.

### Artwork lookup (per word)
1. `assets/images/<word>.png` (transparent PNG, AI or designer; optional `<word>_line.png` for colouring)
2. built-in vector drawer in `art.py` (chicken, egg, bee, honey, cow, milk, sheep, wool, tree, apple)
3. generic letter badge (QC warns "needs artwork")

---------------------------------------------------------------------
## 3. Automation workflow

```
 Excel (Database sheet)
        |  database.load_rows()      normalise headers, pad IDs, Title Case
        v
 QC  (qc.check_rows)  ---- qc_report.csv
   FAIL -> row skipped        WARN -> built, flagged for human review      PASS
        v
 (optional) --export-prompts -> image_prompts.csv  (style-locked prompts for Midjourney / DALL-E / etc.)
        v
 for each row (parallel with --workers N, skipped if unchanged hash):
     render_pdf       header + template + footer per page  -> English_Indonesian_Worksheet.pdf
     render_preview   all pages as contact sheet            -> Preview.png
     render_cover     square 2000 px listing image          -> Cover.png
                      600 px thumbnail                      -> Thumbnail.png
        v
 manifest.csv  (ID, folder, rebuilt?, pages, QC)  -> feed to Etsy / TPT / Drive upload scripts
```

### Quality gate (`qc.py`)
| Check | How | Result |
|---|---|---|
| Required fields, duplicate ID/object | structural | FAIL |
| Simple English / age level | <= 2 words, <= 12 letters, letters only; glossary `Age_Min` | WARN |
| Indonesian translation correct | must equal `data/approved_vocab.csv` entry | **FAIL if different**, WARN if word unknown |
| Spelling | glossary, then system dictionary if present | WARN |
| Images match vocabulary | art exists for both words; prompt mentions the object | WARN |
| Style safety | prompt contains realistic / scary / photo ... | FAIL |
| Printable layout | large words must fit the card at >= 30 pt | WARN |

Honest limitation: translation and age-level checks are only as good as the glossary. Words **not** in it are warned, never silently
trusted: have a native Indonesian speaker add them to `approved_vocab.csv` once, then they pass automatically forever.
Use `--strict` to treat warnings as failures for bulk production runs.

### Scaling to thousands
* `--workers 8` parallel rows; hash-based skip means re-running 5,000 rows only rebuilds changed rows (edit text, brand, template version or an image).
* To restyle everything: change `config.py` (brand/palette) and bump `TEMPLATE_VERSION`.
* New template: write `draw_k(c, row, pool, rng, accent)` in `templates.py` (use `tracing.py` for lines), add it to `TEMPLATES`.

---------------------------------------------------------------------
## 4. Python structure
```
worksheet_system/
|- create_sample_database.py   builds the example Excel file
|- requirements.txt
|- data/
|   |- worksheet_database.xlsx   the content database
|   '- approved_vocab.csv        verified EN->ID glossary used by QC
|- assets/
|   |- images/                   optional <word>.png / <word>_line.png
|   '- fonts/                    optional Fredoka-Bold/Regular.ttf
|- worksheet_engine/
|   |- config.py       brand, palette, fonts, page grid, QC thresholds
|   |- database.py     Excel -> Row objects, placeholder engine, folder naming
|   |- qc.py           quality checks + report
|   |- art.py          vector illustration library + PNG loader (color/outline/shadow)
|   |- components.py   header, instruction, footer, dotted tracing, panels
|   |- tracing.py      line/shape engine: geometry (zigzag, wave, spiral...), 5 line styles, markers
|   |- templates.py    the 10 active templates A-J (+ LA..LI registration)
|   |- templates_legacy.py  v1.x templates (matching, vocabulary, colouring, counting...)
|   |- render.py       PDF, preview sheet, cover, thumbnail, change detection
|   '- main.py         CLI
'- PRODUCTS/           output (see below)
```

## 5. Sample output (5 rows)
```
PRODUCTS/
  Animals_and_Their_Products/
    Chicken/  English_Indonesian_Worksheet.pdf  Preview.png  Cover.png  Thumbnail.png
    Bee/ Cow/ Sheep/   (same files)
  Plants_and_Their_Fruits/
    Tree/              (same files)
  qc_report.csv  manifest.csv  image_prompts.csv
```

## Adding a template
See `PANDUAN_TAMBAH_TEMPLATE.md` (Indonesian, step by step, with the Counting template as the worked example).

## Notes / next steps
* The built-in vector art covers the 10 sample words so the system runs offline. For the full catalogue, generate PNGs from
  `image_prompts.csv` (prompts already include the style lock) and drop them in `assets/images/`; no code change is needed.
* Add an answer-key page (template G) for teacher/parent editions if you plan to sell them.
* Use a rounded child-friendly font (Fredoka, Baloo 2) for the best handwriting-practice look; both are free (OFL).
