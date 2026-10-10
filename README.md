# D&D Character Sheet Translator (Aurora Builder -> Italian)

A specialized software and CLI script to translate D&D 5th Edition character sheets generated with [Aurora Builder](https://aurorabuilder.com/) from **English** to **Italian**, strictly preserving:
- Original visual layout and alignment
- Fillable AcroForm interactive fields
- Official D&D 5e Italian terminology for characteristics, abilities, skills, combat actions, damage types, weapons, armor, spells, feats, and class features.

---

## Features

1. **Official Italian Terminology**:
   - Integrated with over 2,380 official D&D 5e Italian translations sourced directly from the Italian SRD and Foundry VTT translation compendiums (`spells`, `items`, `classfeatures`, `races`, `classes`, etc.).
   - Curated mappings for core characteristics (Forza, Destrezza, Costituzione, Intelligenza, Saggezza, Carisma), skills, saving throws, senses, and combat terminology.
   - Handles specific patterns such as `Invisibility (Always Prepared)` -> `Invisibilità (Sempre Preparato)` and `1d8 + 3 (+2) Piercing` -> `1d8 + 3 (+2) Perforante`.

2. **Precision Layout & Position Preservation**:
   - Updates interactive PDF AcroForm fields (Build, attacks, damage, spells, gear, etc.) directly, maintaining native appearance streams.
   - Replaces static page blocks (Racial Traits, Features & Traits, Proficiencies, Spell Cards, Item Descriptions) using targeted white-out redaction followed by HTML-formatted text insertion (`insert_htmlbox` with auto-scaling) to guarantee zero layout overflow.

3. **Fallback Translation & Smart Chunking**:
   - Neural machine translation with smart sentence/paragraph chunking handles free-form text such as custom backstories, notes, and detailed ability mechanics.
   - Persistent disk cache (`dnd_translator/data/translations_cache.json`) eliminates redundant API requests and enables instant re-runs.

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

### 1. Translate all sheets in the default folder (`charactersheets/`)
```bash
python translate.py
```
Output files will be saved in `translated_charactersheets/` with the `_ita.pdf` suffix.

### 2. Translate a specific PDF file
```bash
python translate.py "charactersheets/barbarian totembear lv4 halforc.pdf" -o "my_barbarian_ita.pdf"
```

### 3. Translate all PDFs in a custom directory
```bash
python translate.py /path/to/my_sheets -o /path/to/output_folder
```

---

## Project Structure

```text
DnD-Sheet-Translator/
├── translate.py                    # Main executable CLI script
├── requirements.txt                # Python dependencies
├── charactersheets/                # Original English PDFs
│   ├── barbarian totembear lv4 halforc.pdf
│   ├── druid circleofgrassland lv4 woodelf.pdf
│   ├── paladin vengance lv4 drow.pdf
│   └── rogue thief lv4 human.pdf
├── translated_charactersheets/     # Generated translated Italian PDFs
│   ├── barbarian totembear lv4 halforc_ita.pdf
│   ├── druid circleofgrassland lv4 woodelf_ita.pdf
│   ├── paladin vengance lv4 drow_ita.pdf
│   └── rogue thief lv4 human_ita.pdf
└── dnd_translator/                 # Core translator package
    ├── __init__.py
    ├── glossary.py                 # Terminology matching and normalization
    ├── translator.py               # Machine translation with smart chunking & caching
    ├── pdf_engine.py               # AcroForm & static canvas PDF translation engine
    └── data/
        ├── compendium_glossary.json       # Official D&D SRD compendium terms (2000+)
        ├── compendium_descriptions.json   # Official D&D descriptions
        ├── curated_terms.json             # Curated terminology, stats, & UI labels
        └── translations_cache.json        # Persistent cache of translated phrases
```
