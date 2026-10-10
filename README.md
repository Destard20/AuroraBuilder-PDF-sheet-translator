# Aurora Builder PDF Sheet Translator

A specialized tool and CLI application to translate D&D 5th Edition character sheets generated with [Aurora Builder](https://aurorabuilder.com/) from **English** into multiple languages (default: **Italian**), strictly preserving:
- Original visual layout, borders, and grid alignment
- Fillable interactive AcroForm fields
- Official D&D 5e compendium terminology for attributes, abilities, skills, combat actions, damage types, weapons, armor, spells, feats, and class features.

---

## Features

1. **Multi-Language Architecture**:
   - Organized by language code directories inside `dnd_translator/data/{LANG}/` (e.g., `IT`, `ES`, `FR`).
   - Dynamic target language selection via the `-l` / `--lang` command-line flag.
   - Fallback neural machine translation automatically routes to the chosen target language code.

2. **Official Compendium Terminology (Italian - IT)**:
   - Integrated with over 2,380 official D&D 5e Italian translations sourced directly from SRD compendiums (`spells`, `items`, `classfeatures`, `races`, `classes`, etc.).
   - Curated mappings for core characteristics (Forza, Destrezza, Costituzione, Intelligenza, Saggezza, Carisma), skills, saving throws, senses, and combat terminology.
   - Dynamic pattern matching for tags like `Invisibility (Always Prepared)` -> `Invisibilità (Sempre Preparato)` and `1d8 + 3 (+2) Piercing` -> `1d8 + 3 (+2) Perforante`.

3. **Precision Layout & Vector Preservation**:
   - Pre-scans interactive AcroForm fields and text blocks prior to widget updating to prevent text duplication.
   - Multi-label horizontal rows (e.g., `PLAYER NAME / ALIGNMENT / DEITY`, `SPEED / FLY / CLIMB / SWIM`, `MAXIMUM / HIT DICE / TEMPORARY`) are detected and partitioned horizontally at the line level, ensuring optimal font size and zero layout collisions.
   - Vector graphics and grid lines are preserved via non-destructive text redaction (`graphics=0`).

4. **Fallback Translation & Smart Caching**:
   - Neural machine translation with smart chunking handles free-form text such as custom backstories, notes, and detailed ability mechanics.
   - Per-language persistent disk cache (`dnd_translator/data/{LANG}/translations_cache.json`) eliminates redundant API requests and is excluded from git tracking.

---

## Installation

Ensure Python 3.10+ is installed.

```bash
# Optional: create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

### 1. Translate all sheets using default language (Italian - `IT`)
```bash
python translate.py
```
Output files will be saved in `translated_charactersheets/` with the `_ita.pdf` suffix.

### 2. Specify target language
```bash
python translate.py -l IT
```
You can pass any language code that has a corresponding folder in `dnd_translator/data/` (e.g. `IT`, `ES`, `FR`, `DE`).

### 3. Translate a specific PDF file
```bash
python translate.py "charactersheets/barbarian totembear lv4 halforc.pdf" -o "my_barbarian_ita.pdf" -l IT
```

### 4. Translate all PDFs in a custom directory
```bash
python translate.py /path/to/my_sheets -o /path/to/output_folder -l IT
```

---

## Adding a New Language

To add support for a new language (e.g., Spanish `ES`, German `DE`):
1. Create a directory: `dnd_translator/data/{LANG}/` (e.g., `dnd_translator/data/ES/`).
2. Add compendium glossaries and curated terms:
   - `compendium_glossary.json`: JSON key-value map of English terms to target language terms.
   - `curated_terms.json`: Specific sheet UI terms, abbreviations, and field labels.
   - `compendium_descriptions.json`: (Optional) Descriptions for abilities, spells, and items.
3. Run `python translate.py -l {LANG}`.

---

## Project Structure

```text
AuroraBuilder-PDF-sheet-translator/
├── translate.py                    # Main executable CLI script
├── requirements.txt                # Python dependencies
├── GEMINI.MD                       # Architecture & developer context for AI
└── dnd_translator/                 # Core translator package
    ├── __init__.py
    ├── glossary.py                 # Multi-language glossary matching & normalization
    ├── translator.py               # Machine translation with smart chunking & per-language cache
    ├── pdf_engine.py               # PDF layout, AcroForm & line-level replacement engine
    └── data/
        └── IT/                     # Italian language compendiums & terms
            ├── compendium_glossary.json       # Official D&D SRD compendium terms (2000+)
            ├── compendium_descriptions.json   # Official D&D descriptions
            ├── curated_terms.json             # Curated terminology, stats, & UI labels
            └── translations_cache.json        # Local persistent translation cache (gitignored)
```
