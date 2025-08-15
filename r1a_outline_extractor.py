import fitz
import pdfplumber
import json
import os
import re
from collections import Counter
from langdetect import detect
import wordninja

try:
    from indicnlp.tokenize import sentence_tokenize, indic_tokenize
    INDICNLP_AVAILABLE = True
except ImportError:
    INDICNLP_AVAILABLE = False
    print('[INFO] IndicNLP not available, using basic whitespace heuristics for Indian languages.')

DEBUG = False

# --- Language helpers ---
def detect_language(text):
    try:
        lang = detect(text)
        if lang in ['hi', 'mr', 'en']:
            return lang
    except Exception:
        pass
    return 'en'

def clean_english(text):
    # Use wordninja to split stuck-together English words
    if not text or ' ' in text:
        return text.strip()
    return ' '.join(wordninja.split(text)).strip()

def clean_indic(text, lang):
    # Use IndicNLP for Hindi/Marathi word segmentation if available
    if INDICNLP_AVAILABLE and lang in ['hi', 'mr']:
        return ' '.join(indic_tokenize.trivial_tokenize(text, lang=lang)).replace(' ।', '।').strip()
    # Fallback: insert space before capital letters or numbers, and after punctuation
    return re.sub(r'([।,.!?])', r'\1 ', text).replace('  ', ' ').strip()

def text_has_invalid_devanagari(text):
    return not any('\u0900' <= c <= '\u097F' for c in text)

def is_bold(span):
    return "bold" in span['font'].lower() or "bld" in span['font'].lower()

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def is_all_caps(text):
    return text.isupper() and len(text) > 2 and any(c.isalpha() for c in text)

def detect_junk_candidates(all_text_spans, num_pages):
    page_texts = {}
    for span in all_text_spans:
        page = span['page']
        page_texts.setdefault(page, []).append(clean_text(span['text']))
    freq = Counter()
    for page, texts in page_texts.items():
        for t in set(texts):
            freq[t] += 1
    threshold = max(2, int(num_pages * 0.6))
    junk = set([t for t, c in freq.items() if c >= threshold and len(t) > 0 and len(t) < 80])
    return junk

def extract_tables(pdf_path):
    tables = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_tables = page.extract_tables()
                for table in page_tables:
                    if table and len(table) > 0 and len(table[0]) > 1:
                        columns = [clean_text(col) for col in table[0] if col]
                        lang = detect_language(' '.join(columns))
                        # Clean columns
                        if lang == 'en':
                            columns = [clean_english(col) for col in columns]
                        else:
                            columns = [clean_indic(col, lang) for col in columns]
                        data = [row for row in table[1:] if any(row)]
                        if columns:
                            tables.append({
                                "page": i + 1,
                                "headers": {lang: columns},
                                "data": data
                            })
    except Exception as e:
        print(f"[WARN] pdfplumber table extraction failed: {e}")
    return tables

def extract_document_info(pdf_path):
    print(f"Reading PDF from: {pdf_path}")
    title = {}
    outline = []
    tables = []
    try:
        document = fitz.open(pdf_path)
    except Exception as e:
        print(f"[ERROR] Could not open PDF: {e}")
        return {"title": {}, "outline": [], "tables": []}
    num_pages = len(document)
    all_text_spans = []
    body_font_sizes = []
    page_spans = {}
    fallback_needed = False
    for page_num, page in enumerate(document):
        try:
            blocks = page.get_text("dict", flags=11)["blocks"]
        except Exception as e:
            print(f"[WARN] Could not extract text from page {page_num+1}: {e}")
            continue
        for b in blocks:
            if b['type'] == 0:
                for line in b['lines']:
                    for span in line['spans']:
                        text = clean_text(span['text'])
                        if not text:
                            continue
                        if text_has_invalid_devanagari(text):
                            fallback_needed = True
                        span_info = {
                            "text": text,
                            "size": span['size'],
                            "font": span['font'],
                            "is_bold": is_bold(span),
                            "origin": span['origin'],
                            "bbox": span['bbox'],
                            "page": page_num + 1,
                            "is_heading_candidate": False
                        }
                        all_text_spans.append(span_info)
                        page_spans.setdefault(page_num + 1, []).append(span_info)
                        if 8 <= span['size'] <= 14:
                            body_font_sizes.append(span['size'])
    # Fallback to pdfplumber if needed (same as before)
    # ... (keep your fallback code here) ...

    if body_font_sizes:
        median_body_font_size = sorted(body_font_sizes)[len(body_font_sizes) // 2]
    else:
        median_body_font_size = 12
    junk_candidates = detect_junk_candidates(all_text_spans, num_pages)
    # Title: largest text on page 1, not junk
    page_0_spans = [s for s in all_text_spans if s['page'] == 1 and s['text'] not in junk_candidates]
    largest_font_size = 0
    title_candidates = []
    for span in page_0_spans:
        if span['size'] > largest_font_size:
            largest_font_size = span['size']
            title_candidates = [span['text']]
        elif span['size'] == largest_font_size:
            title_candidates.append(span['text'])
    if title_candidates:
        for t in set(title_candidates):
            lang = detect_language(t)
            if lang == 'en':
                title[lang] = clean_english(t)
            else:
                title[lang] = clean_indic(t, lang)
    # Heading detection (loosened, multilingual):
    heading_outline = []
    for page_num in range(1, num_pages + 1):
        spans = page_spans.get(page_num, [])
        for i, span_info in enumerate(spans):
            text = span_info['text']
            font_size = span_info['size']
            is_bold_text = span_info['is_bold']
            if text in junk_candidates or len(text) < 2:
                continue
            is_heading = False
            if is_bold_text and font_size > median_body_font_size * 1.1:
                is_heading = True
            elif font_size > median_body_font_size * 1.2 and i == 0:
                is_heading = True
            elif is_all_caps(text) and font_size >= median_body_font_size:
                is_heading = True
            if not is_heading and i + 1 < len(spans):
                next_text = spans[i + 1]['text']
                if re.match(r'^[\u2022\u2023\u25E6\u2043\u2219\-\*\d]', next_text.strip()):
                    is_heading = True
            if is_heading:
                lang = detect_language(text)
                if lang == 'en':
                    clean_txt = clean_english(text)
                else:
                    clean_txt = clean_indic(text, lang)
                heading_outline.append({"level": None, "text": {lang: clean_txt}, "page": page_num, "size": font_size})
    # Assign H1/H2/H3 based on font size
    if heading_outline:
        sizes = sorted({h['size'] for h in heading_outline}, reverse=True)
        for h in heading_outline:
            if h['size'] >= sizes[0] * 0.95:
                h['level'] = "H1"
            elif len(sizes) > 1 and h['size'] >= sizes[1] * 0.95:
                h['level'] = "H2"
            else:
                h['level'] = "H3"
    # Remove duplicates and clean up
    final_outline = []
    seen = set()
    for h in heading_outline:
        key = (h['level'], tuple(h['text'].items()), h['page'])
        if key not in seen:
            final_outline.append({"level": h['level'], "text": h['text'], "page": h['page']})
            seen.add(key)
    tables = extract_tables(pdf_path)
    return {"title": title, "outline": final_outline, "tables": tables}

def main_r1a():
    input_dir = "input_1A"
    output_dir = "output_1A"
    os.makedirs(output_dir, exist_ok=True)
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)
            output_filename = filename.replace(".pdf", ".json")
            output_path = os.path.join(output_dir, output_filename)
            print(f"Processing {pdf_path} for R1A...")
            try:
                result = extract_document_info(pdf_path)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"Generated R1A output: {output_path}")
            except Exception as e:
                print(f"Error processing {pdf_path}: {e}")

if __name__ == "__main__":
    main_r1a()