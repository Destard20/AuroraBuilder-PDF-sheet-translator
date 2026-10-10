import os
import json
import re
import html
import time
import unicodedata
from typing import Optional
import requests
from .glossary import DndGlossary

class DndTranslator:
    def __init__(self, glossary: Optional[DndGlossary] = None, cache_file: Optional[str] = None, lang: str = "IT"):
        self.lang = lang
        self.glossary = glossary or DndGlossary(lang=lang)
        if cache_file is None:
            cache_file = os.path.join(os.path.dirname(__file__), 'data', lang, 'translations_cache.json')
        self.cache_file = cache_file
        self.cache = {}
        self.load_cache()

    def load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except Exception as e:
                print(f"Warning: could not load cache: {e}")
                self.cache = {}

    def save_cache(self):
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.cache_file)), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: could not save cache: {e}")

    def translate(self, text: str) -> str:
        if not text or not text.strip():
            return text

        cleaned = unicodedata.normalize('NFKD', text).strip()

        # Check glossary first
        term_trans = self.glossary.lookup(cleaned)
        if term_trans != cleaned:
            return term_trans

        # If it's pure numbers / symbols, don't translate
        if re.match(r'^[\d\+\-\s\./\'"#%]+$', cleaned):
            return cleaned

        # Check cache
        if cleaned in self.cache:
            return self.cache[cleaned]

        # Check if description exists in compendium
        if cleaned in self.glossary.descriptions:
            desc_html = self.glossary.descriptions[cleaned]
            plain = re.sub(r'<[^>]+>', '', desc_html)
            plain = html.unescape(plain).strip()
            if plain:
                self.cache[cleaned] = plain
                self.save_cache()
                return plain

        # Perform translation (with chunking if long)
        if len(cleaned) > 400:
            translated = self._translate_long(cleaned)
        else:
            translated = self._machine_translate(cleaned)

        # Only cache if successful translation
        if translated and translated.strip() != cleaned:
            self.cache[cleaned] = translated
            self.save_cache()
            return translated

        return cleaned

    def _translate_long(self, text: str) -> str:
        parts = re.split(r'(\n\s{2,}|\n\n|\r\n\r\n|\n\s*•\s*)', text)
        result_parts = []
        for part in parts:
            if not part or not part.strip() or part.strip() in ['•']:
                result_parts.append(part)
                continue
            cleaned_part = part.strip()
            if len(cleaned_part) > 350:
                sents = re.split(r'(?<=\.)\s+', cleaned_part)
                buf = []
                curr_len = 0
                for s in sents:
                    if curr_len + len(s) < 350:
                        buf.append(s)
                        curr_len += len(s)
                    else:
                        chunk = ' '.join(buf)
                        result_parts.append(self._machine_translate(chunk))
                        buf = [s]
                        curr_len = len(s)
                if buf:
                    chunk = ' '.join(buf)
                    result_parts.append(self._machine_translate(chunk))
            else:
                result_parts.append(self._machine_translate(cleaned_part))

        return ''.join(result_parts)

    def _machine_translate(self, text: str) -> str:
        if not text or not text.strip():
            return text

        target_lang = self.lang.lower()
        # Use MyMemory with valid user email for 50,000 char daily quota
        for attempt in range(2):
            try:
                url = 'https://api.mymemory.translated.net/get'
                params = {
                    'q': text,
                    'langpair': f'en|{target_lang}',
                    'de': 'aurora_dnd_translator@gmail.com'
                }
                resp = requests.get(url, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    res = data.get('responseData', {}).get('translatedText', '').strip()
                    if res and not res.startswith('MYMEMORY WARNING:'):
                        return res
            except Exception:
                time.sleep(0.5)

        return text

