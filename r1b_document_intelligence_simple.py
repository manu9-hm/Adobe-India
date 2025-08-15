#!/usr/bin/env python3
"""
Simplified Round 1B Document Intelligence
Extracts relevant sections without using sentence transformers to avoid dependency issues
"""

import os
import json
import time
import fitz
import pdfplumber
from langdetect import detect
import numpy as np
from r1a_outline_extractor import extract_document_info

def text_has_invalid_characters(text, lang):
    if lang in ['hi', 'mr']:
        return not any('\u0900' <= c <= '\u097F' for c in text)
    return False

def detect_language(text):
    try:
        lang = detect(text)
        if lang in ['hi', 'mr', 'en']:
            return lang
    except Exception:
        pass
    return 'en'

def extract_page_text(page, pdf_path, page_num):
    text = page.get_text("text", flags=11)
    lang = detect_language(text)
    if text_has_invalid_characters(text, lang):
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = pdf.pages[page_num].extract_text() or ""
                lang = detect_language(text)
        except Exception:
            text = ""
    return text, lang

def is_relevant_section(text, keywords):
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)

def calculate_simple_relevance_score(text, persona_keywords, job_keywords):
    """Calculate a simple relevance score based on keyword matching"""
    text_lower = text.lower()
    score = 0.0
    
    # Check persona keywords
    for keyword in persona_keywords:
        if keyword.lower() in text_lower:
            score += 1.0
    
    # Check job keywords
    for keyword in job_keywords:
        if keyword.lower() in text_lower:
            score += 2.0  # Job keywords get higher weight
    
    # Normalize by text length
    if len(text) > 0:
        score = score / (len(text.split()) + 1)
    
    return score

def main_r1b():
    input_dir = "input_1B"
    output_dir = "output_1B"
    os.makedirs(output_dir, exist_ok=True)
    r1b_pdf_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]

    persona_path = os.path.join(input_dir, 'persona.txt')
    job_path = os.path.join(input_dir, 'job.txt')
    persona_definition = "PhD Researcher in Computational Biology"
    job_to_be_done = "Review GNNs for drug discovery"
    if os.path.exists(persona_path):
        with open(persona_path, 'r', encoding='utf-8') as f:
            persona_definition = f.read().strip()
    if os.path.exists(job_path):
        with open(job_path, 'r', encoding='utf-8') as f:
            job_to_be_done = f.read().strip()

    # Define keywords for relevance scoring
    persona_keywords = ["phd", "researcher", "computational", "biology", "research", "scientist"]
    job_keywords = ["gnn", "drug", "discovery", "molecular", "neural", "graph", "network", "machine learning", "ai"]

    keywords = ["gnn", "drug discovery", "molecular", "neural", "biology"]
    ENABLE_KEYWORD_FILTER = False  # Set to True to enable keyword filtering

    all_sections = []
    documents_info = []

    for pdf_path in r1b_pdf_files:
        outline_json = extract_document_info(pdf_path)
        outline = outline_json.get("outline", [])
        print(f"\n[DEBUG] Outline for {pdf_path}: {outline}")
        if not outline:
            print(f"[WARNING] No outline/headings found in {pdf_path}!")
        doc = fitz.open(pdf_path)
        page_texts = []
        page_langs = []
        for i, page in enumerate(doc):
            text, lang = extract_page_text(page, pdf_path, i)
            print(f"[DEBUG] Page {i+1} ({lang}): {text[:200]}")
            page_texts.append(text)
            page_langs.append(lang)
        
        for entry in outline:
            page_num = entry["page"]
            section_title = entry["text"]
            section_title_dict = {}
            refined_text_dict = {}
            
            # Handle multilingual section_title (dict) or single language (str)
            if isinstance(section_title, dict):
                # Multilingual format
                for lang_code, title_text in section_title.items():
                    page_text = page_texts[page_num-1] if page_num-1 < len(page_texts) else ""
                    if not page_text:
                        continue
                    if detect_language(page_text) == lang_code or lang_code == 'en':
                        idx = page_text.find(title_text)
                        if idx == -1:
                            idx = 0
                        para = page_text[idx:idx+200].strip()
                        if para:
                            section_title_dict[lang_code] = title_text
                            refined_text_dict[lang_code] = para
            else:
                # Single language format (string)
                page_text = page_texts[page_num-1] if page_num-1 < len(page_texts) else ""
                if page_text:
                    lang_code = detect_language(page_text)
                    if lang_code in ['en', 'hi', 'mr']:
                        idx = page_text.find(str(section_title))
                        if idx == -1:
                            idx = 0
                        para = page_text[idx:idx+200].strip()
                        if para:
                            section_title_dict[lang_code] = str(section_title)
                            refined_text_dict[lang_code] = para
            
            print(f"[DEBUG] Section title: {section_title_dict}, Refined: {refined_text_dict}")
            if ENABLE_KEYWORD_FILTER and not is_relevant_section(" ".join(refined_text_dict.values()), keywords):
                print(f"[DEBUG] Section filtered out by keywords: {section_title_dict}")
                continue
            if not refined_text_dict:
                print(f"[WARNING] No refined text found for section: {section_title_dict}")
                continue
            all_sections.append({
                "document": os.path.basename(pdf_path),
                "page_number": page_num,
                "section_title": section_title_dict,
                "refined_text": refined_text_dict
            })
        documents_info.append({"path": pdf_path, "r1a_outline": outline_json})

    if not all_sections:
        print("[WARNING] No sections found after extraction and filtering!")

    # Score sections using simple keyword matching
    scored_sections = []
    for section in all_sections:
        section_texts = []
        for lang in section["section_title"]:
            section_texts.append(section["section_title"][lang])
        for lang in section["refined_text"]:
            section_texts.append(section["refined_text"][lang])
        section_text = " ".join(section_texts)
        
        # Calculate simple relevance score
        relevance_score = calculate_simple_relevance_score(section_text, persona_keywords, job_keywords)
        
        scored_sections.append({
            **section,
            "relevance_score": relevance_score
        })
    
    ranked_sections = sorted(scored_sections, key=lambda x: x['relevance_score'], reverse=True)

    output_sections = []
    sub_section_analysis = []
    for i, section in enumerate(ranked_sections):
        output_sections.append({
            "document": section["document"],
            "page_number": section["page_number"],
            "section_title": section["section_title"],
            "importance_rank": i + 1
        })
        sub_section_analysis.append({
            "document": section["document"],
            "page_number": section["page_number"],
            "refined_text": section["refined_text"]
        })

    result = {
        "metadata": {
            "input_documents": [os.path.basename(d['path']) for d in documents_info],
            "persona": persona_definition,
            "job_to_be_done": job_to_be_done,
            "processing_timestamp": time.strftime('%Y-%m-%dT%H:%M:%S'),
            "note": "Simplified version without sentence transformers"
        },
        "extracted_sections": output_sections,
        "sub_section_analysis": sub_section_analysis
    }
    output_path = os.path.join(output_dir, "r1b_output_simple.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Generated simplified R1B output: {output_path}")

if __name__ == "__main__":
    main_r1b() 