import os
import re
import json
import unicodedata

class DndGlossary:
    def __init__(self, data_dir=None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.data_dir = data_dir
        self.terms = {}
        self.norm_terms = {}
        self.descriptions = {}
        self.load_dictionaries()

    def load_dictionaries(self):
        comp_file = os.path.join(self.data_dir, 'compendium_glossary.json')
        if os.path.exists(comp_file):
            with open(comp_file, 'r', encoding='utf-8') as f:
                self.terms.update(json.load(f))

        desc_file = os.path.join(self.data_dir, 'compendium_descriptions.json')
        if os.path.exists(desc_file):
            with open(desc_file, 'r', encoding='utf-8') as f:
                self.descriptions.update(json.load(f))

        curated_file = os.path.join(self.data_dir, 'curated_terms.json')
        if os.path.exists(curated_file):
            with open(curated_file, 'r', encoding='utf-8') as f:
                self.terms.update(json.load(f))

        for k, v in self.terms.items():
            self.norm_terms[k.strip().lower()] = v.strip()

    def lookup(self, term: str) -> str:
        if not term:
            return term
        cleaned = unicodedata.normalize('NFKD', term).strip()
        lower = cleaned.lower()

        if cleaned in self.terms:
            return self.terms[cleaned]

        if lower in self.norm_terms:
            val = self.norm_terms[lower]
            if cleaned.isupper() and len(cleaned) > 1:
                return val.upper()
            if cleaned.islower():
                return val.lower()
            return val

        # Trailing dot handling: Oath of Vengeance. -> Giuramento di Vendetta.
        if cleaned.endswith('.') and len(cleaned) < 50:
            without_dot = cleaned[:-1].strip()
            trans_without = self.lookup(without_dot)
            if trans_without != without_dot:
                return f"{trans_without}."

        if cleaned.startswith('[') and cleaned.endswith(']'):
            inner = cleaned[1:-1].strip()
            trans_inner = self.lookup(inner)
            return f"[{trans_inner}]"

        m = re.match(r'^(.*?)\s*\((Always Prepared)\)$', cleaned, re.IGNORECASE)
        if m:
            base = m.group(1).strip()
            trans_base = self.lookup(base)
            return f"{trans_base} (Sempre Preparato)"

        m = re.match(r'^(.*?)\s*\((Dark Elf)\)$', cleaned, re.IGNORECASE)
        if m:
            base = m.group(1).strip()
            trans_base = self.lookup(base)
            return f"{trans_base} (Elfo Oscuro)"

        m = re.match(r'^(.*?)\s*\((Action|Bonus Action|Reaction)[—\-](.*?)\)$', cleaned, re.IGNORECASE)
        if m:
            base, act_type, sub = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
            trans_base = self.lookup(base)
            act_trans = self.lookup(act_type)
            sub_trans = self.lookup(sub)
            return f"{trans_base} ({act_trans}—{sub_trans})"

        m = re.match(r'^(.*?)\s*\((\d+/Long Rest|\d+/Short Rest)\)$', cleaned, re.IGNORECASE)
        if m:
            base, tag = m.group(1).strip(), m.group(2).strip()
            trans_base = self.lookup(base)
            tag_trans = tag.replace('Long Rest', 'Riposo Lungo').replace('Short Rest', 'Riposo Breve')
            return f"{trans_base} ({tag_trans})"

        m = re.match(r'^([\d\+\-\s\(\)dD]+)\s+([A-Za-z]+)(\s*\(Versatile\))?$', cleaned)
        if m:
            dice_part, dmg_type, vers = m.group(1).strip(), m.group(2).strip(), m.group(3)
            trans_dmg = self.lookup(dmg_type)
            if trans_dmg != dmg_type:
                res = f"{dice_part} {trans_dmg}"
                if vers:
                    res += " (Versatile)"
                return res

        m = re.match(r'^(\d+)(st|nd|rd|th)-level\s+([A-Za-z]+)(\s*\(ritual\))?$', cleaned, re.IGNORECASE)
        if m:
            lvl, school, ritual = m.group(1), m.group(3), m.group(4)
            school_trans = self.lookup(school)
            res = f"{school_trans} di {lvl}° livello"
            if ritual:
                res += " (rituale)"
            return res

        m = re.match(r'^([A-Za-z]+)\s+Cantrip$', cleaned, re.IGNORECASE)
        if m:
            school = m.group(1)
            school_trans = self.lookup(school)
            return f"Trucchetto di {school_trans}"

        m = re.match(r'^Level\s+(\d+)\s+([A-Za-z\-\s]+?)\s+([A-Za-z]+),\s+(.+)$', cleaned, re.IGNORECASE)
        if m:
            lvl, race, cls, subclass = m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4).strip()
            race_trans = self.lookup(race)
            cls_trans = self.lookup(cls)
            sub_trans = self.lookup(subclass)
            return f"{cls_trans} {race_trans} di {lvl}° Livello, {sub_trans}"

        m = re.match(r'^Level\s+(\d+)\s+([A-Za-z\-\s]+?)\s+([A-Za-z]+)$', cleaned, re.IGNORECASE)
        if m:
            lvl, race, cls = m.group(1), m.group(2).strip(), m.group(3).strip()
            race_trans = self.lookup(race)
            cls_trans = self.lookup(cls)
            return f"{cls_trans} {race_trans} di {lvl}° Livello"

        # Class, Subclass: Paladin, Oath of Vengeance
        m = re.match(r'^([A-Za-z]+),\s+(.+)$', cleaned)
        if m:
            cls, subclass = m.group(1).strip(), m.group(2).strip()
            cls_trans = self.lookup(cls)
            sub_trans = self.lookup(subclass)
            if cls_trans != cls or sub_trans != subclass:
                return f"{cls_trans}, {sub_trans}"

        return cleaned
