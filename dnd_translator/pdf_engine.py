import os
import re
from typing import Optional, List
import pymupdf
import unicodedata
from .glossary import DndGlossary
from .translator import DndTranslator

class DndPdfEngine:
    def __init__(self, glossary: Optional[DndGlossary] = None, translator: Optional[DndTranslator] = None, lang: str = "IT"):
        self.lang = lang
        self.glossary = glossary or DndGlossary(lang=lang)
        self.translator = translator or DndTranslator(self.glossary, lang=lang)

    def translate_pdf(self, input_path: str, output_path: str) -> None:
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"File not found: {input_path}")

        print(f"Processing: {input_path} -> {output_path}")
        doc = pymupdf.open(input_path)

        for p_no in range(len(doc)):
            page = doc[p_no]
            self._translate_page(page, p_no + 1)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        doc.save(output_path)
        print(f"Successfully saved: {output_path}")

    def _translate_page(self, page: pymupdf.Page, page_num: int) -> None:
        # Step 1: Gather original widget values and rects
        widget_values = set()
        widget_rects = []
        for w in page.widgets():
            val = str(w.field_value or '').strip()
            if not val:
                continue
            widget_values.add(val)
            widget_rects.append(w.rect)

        # Step 2: Extract text dict BEFORE updating widgets
        d = page.get_text('dict')
        
        # Step 3: Update widgets (translates form fields)
        for w in page.widgets():
            val = str(w.field_value or '').strip()
            if not val:
                continue
            if val in ['Yes', 'No', 'Off', 'Ja']:
                continue
            if re.match(r'^[+\-]?[0-9]+(\.[0-9]+)?$', val):
                continue
            trans_val = self.translator.translate(val)
            if trans_val != val:
                w.field_value = trans_val
                w.update()

        # Step 4: Collect static text blocks & multi-label rows
        replacements = []
        multi_label_items = []

        for b in d.get('blocks', []):
            if 'lines' not in b:
                continue
            b_rect = pymupdf.Rect(b['bbox'])

            lines_text = [unicodedata.normalize('NFKD', ''.join(s['text'] for s in l['spans'])).strip() for l in b['lines']]
            lines_text = [t for t in lines_text if t and not re.match(r'^[+\-]?[0-9]+(\.[0-9]+)?$', t)]
            if not lines_text:
                continue

            # Protect widgets
            if any(t in widget_values for t in lines_text):
                continue

            is_w = False
            for wr in widget_rects:
                inter = b_rect & wr
                if not inter.is_empty and (inter.get_area() / b_rect.get_area()) > 0.4:
                    is_w = True
                    break
            if is_w:
                continue

            line_items = []
            for l in b['lines']:
                l_txt = unicodedata.normalize('NFKD', ''.join(s['text'] for s in l['spans'])).strip()
                if l_txt and not re.match(r'^[+\-]?[0-9]+(\.[0-9]+)?$', l_txt):
                    line_items.append((l, l_txt))

            if not line_items:
                continue

            # Check if this block is a multi-label row (multiple labels on the same row/block)
            y_diff = (max(l['bbox'][1] for l, _ in line_items) - min(l['bbox'][1] for l, _ in line_items)) if len(line_items) > 1 else 0
            labels_in_block = [(l, txt, self.glossary.lookup(txt)) for l, txt in line_items if self.glossary.lookup(txt) != txt]

            is_multi_label_row = len(labels_in_block) > 1 and (len(labels_in_block) == len(line_items) or y_diff < 8.0)

            if is_multi_label_row:
                sorted_items = sorted(labels_in_block, key=lambda x: x[0]['bbox'][0])
                for i, (l, orig_txt, trans_txt) in enumerate(sorted_items):
                    l_bbox = l['bbox']
                    y0 = l_bbox[1]
                    y1 = l_bbox[3]

                    if i == 0:
                        left_lim = max(b_rect.x0 - 5, l_bbox[0] - 15)
                    else:
                        left_lim = (sorted_items[i-1][0]['bbox'][2] + l_bbox[0]) / 2

                    if i == len(sorted_items) - 1:
                        right_lim = min(b_rect.x1 + 5, l_bbox[2] + 15)
                    else:
                        right_lim = (l_bbox[2] + sorted_items[i+1][0]['bbox'][0]) / 2

                    ins_rect = pymupdf.Rect(left_lim, y0 - 1.5, right_lim, max(y1 + 1.5, y0 + 9.0))
                    redact_rect = pymupdf.Rect(l_bbox[0] - 0.5, l_bbox[1] - 0.5, l_bbox[2] + 0.5, l_bbox[3] + 0.5)
                    multi_label_items.append((redact_rect, ins_rect, orig_txt, trans_txt))
                continue

            # Regular block handling
            txt = unicodedata.normalize('NFKD', '\n'.join(t for _, t in line_items)).strip()

            if 'generated by' in txt.lower():
                footer_msg = 'Questa scheda del personaggio è stata generata da Aurora Builder.' if self.lang.upper() == 'IT' else self.translator.translate(txt)
                replacements.append(('footer', b_rect, b_rect, txt, footer_msg))
                continue

            m = re.match(r'^([A-Z][A-Za-z0-9\s’\',\-–—\(\)/]+?)\.\s+(.*)$', txt, re.DOTALL)
            if m and len(m.group(1)) <= 50 and '\n' not in m.group(1):
                title, desc = m.group(1).strip(), m.group(2).strip()
                trans_title = self.glossary.lookup(title)
                if trans_title != title:
                    trans_desc = self.translator.translate(desc)
                    replacements.append(('feature', b_rect, b_rect, trans_title, trans_desc))
                    continue

            single_trans = self.glossary.lookup(txt)
            if single_trans != txt:
                ins_rect = pymupdf.Rect(b_rect.x0 - 3, b_rect.y0 - 1, b_rect.x1 + 3, b_rect.y1 + 1)
                replacements.append(('label', b_rect, ins_rect, txt, single_trans))
                continue

            if len(txt) > 25:
                trans_desc = self.translator.translate(txt)
                if trans_desc != txt:
                    replacements.append(('desc', b_rect, b_rect, txt, trans_desc))
                    continue

        # Step 5: Add and apply redactions (no fill, and preserve vector graphics/lines)
        for r_rect, ins_rect, orig, trans in multi_label_items:
            page.add_redact_annot(r_rect)

        for item in replacements:
            page.add_redact_annot(item[1])

        page.apply_redactions(graphics=0)

        # Step 6: Insert new translated text
        for r_rect, ins_rect, orig_txt, trans_txt in multi_label_items:
            align = 'center'
            weight = 'bold' if orig_txt.isupper() else 'normal'
            fs = '6.5pt'
            if len(trans_txt) > 22:
                fs = '5.0pt'
            elif ins_rect.height < 8:
                fs = '5.8pt'
            html = f'<div style="font-family: sans-serif; font-size: {fs}; text-align: {align}; font-weight: {weight}; line-height: 1.0; color: black;">{trans_txt}</div>'
            page.insert_htmlbox(ins_rect, html, scale_low=0)

        for item in replacements:
            kind, b_rect, ins_rect = item[0], item[1], item[2]
            if kind == 'label':
                orig_txt, trans_txt = item[3], item[4]
                align = 'center' if (orig_txt.isupper() or ins_rect.width < 90) else 'left'
                weight = 'bold' if orig_txt.isupper() else 'normal'
                fs = '6.5pt' if ins_rect.height < 10 else ('8.0pt' if ins_rect.height > 15 else '7.0pt')
                html_txt = trans_txt.replace('\n', '<br>')
                html = f'<div style="font-family: sans-serif; font-size: {fs}; text-align: {align}; font-weight: {weight}; line-height: 1.05; color: black;">{html_txt}</div>'
                page.insert_htmlbox(ins_rect, html, scale_low=0)
            elif kind == 'feature':
                title, desc = item[3], item[4]
                html = f'<div style="font-family: sans-serif; font-size: 7.0pt; line-height: 1.15; color: black;"><b><i>{title}.</i></b> {desc}</div>'
                page.insert_htmlbox(ins_rect, html, scale_low=0)
            elif kind == 'desc':
                trans_desc = item[4]
                html_txt = trans_desc.replace('\n', '<br>')
                html = f'<div style="font-family: sans-serif; font-size: 6.8pt; line-height: 1.15; color: black;">{html_txt}</div>'
                page.insert_htmlbox(ins_rect, html, scale_low=0)
            elif kind == 'footer':
                html = f'<div style="font-family: sans-serif; font-size: 5.5pt; text-align: center; color: #555555;">{item[4]}</div>'
                page.insert_htmlbox(ins_rect, html, scale_low=0)
