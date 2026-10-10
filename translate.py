#!/usr/bin/env python3
"""
Aurora Builder PDF Character Sheet Translator

Translates D&D 5e character sheets generated with Aurora Builder to various languages,
preserving layout, form fields, and official compendium terminology.
"""

import os
import sys
import argparse
import glob

# Ensure dependencies are available; automatically switch to .venv if running from system python
try:
    import pymupdf
except ImportError:
    project_root = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(project_root, ".venv")
    venv_python = os.path.join(venv_dir, "bin", "python")
    if os.path.exists(venv_python) and sys.prefix != venv_dir:
        os.execv(venv_python, [venv_python] + sys.argv)
    else:
        sys.stderr.write(
            "Error: 'pymupdf' is not installed in the current Python environment.\n\n"
            "To fix this, please activate the virtual environment:\n"
            "    source .venv/bin/activate\n\n"
            "Or install the requirements:\n"
            "    pip install -r requirements.txt\n"
        )
        sys.exit(1)

from dnd_translator import DndGlossary, DndTranslator, DndPdfEngine


def main():
    parser = argparse.ArgumentParser(
        description="Translate D&D Character Sheets (Aurora Builder) into multiple languages."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="charactersheets",
        help="Input PDF file or directory containing PDF sheets (default: charactersheets)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="translated_charactersheets",
        help="Output directory or output file path (default: translated_charactersheets)",
    )
    parser.add_argument(
        "-l",
        "--lang",
        default="IT",
        help="Target language code corresponding to folder in dnd_translator/data/ (default: IT)",
    )

    args = parser.parse_args()

    # Validate target language directory
    base_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dnd_translator", "data")
    available_langs = [d for d in os.listdir(base_data_dir) if os.path.isdir(os.path.join(base_data_dir, d))]

    target_lang = None
    for d in available_langs:
        if d.upper() == args.lang.upper():
            target_lang = d
            break

    if not target_lang:
        print(f"Error: Language '{args.lang}' data directory not found in dnd_translator/data/.")
        print(f"Available languages: {', '.join(sorted(available_langs)) if available_langs else 'None'}")
        sys.exit(1)

    lang_suffix = "_ita" if target_lang.upper() == "IT" else f"_{target_lang.lower()}"

    # Determine files to process
    if os.path.isfile(args.input):
        files_to_process = [(args.input, args.output if args.output.endswith(".pdf") else os.path.join(args.output, os.path.basename(args.input)))]
    elif os.path.isdir(args.input):
        pdf_files = sorted(glob.glob(os.path.join(args.input, "*.pdf")))
        if not pdf_files:
            print(f"No PDF files found in directory: {args.input}")
            sys.exit(1)
        files_to_process = []
        for pdf_path in pdf_files:
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            out_path = os.path.join(args.output, f"{base_name}{lang_suffix}.pdf")
            files_to_process.append((pdf_path, out_path))
    else:
        print(f"Error: Input path '{args.input}' does not exist.")
        sys.exit(1)

    print("=" * 60)
    print(f"AURORA BUILDER PDF SHEET TRANSLATOR -> {target_lang}")
    print("=" * 60)
    print(f"Target language : {target_lang}")
    print(f"Found {len(files_to_process)} sheet(s) to translate.\n")

    print(f"Initializing official D&D 5e {target_lang} glossary and translator...")
    glossary = DndGlossary(lang=target_lang)
    translator = DndTranslator(glossary=glossary, lang=target_lang)
    engine = DndPdfEngine(glossary=glossary, translator=translator, lang=target_lang)
    print(f"Loaded {len(glossary.terms)} official glossary terms.\n")

    for idx, (in_file, out_file) in enumerate(files_to_process, 1):
        print(f"[{idx}/{len(files_to_process)}] Translating '{os.path.basename(in_file)}'...")
        try:
            engine.translate_pdf(in_file, out_file)
            print(f" -> Saved to: {out_file}\n")
        except Exception as e:
            print(f" -> Error translating {in_file}: {e}\n", file=sys.stderr)

    print("=" * 60)
    print("Translation completed successfully!")
    print(f"All files saved in: {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
