#!/usr/bin/env python3
"""
Comprehensive Evaluation Pipeline for Adobe Hackathon
Evaluates Round 1A (heading detection) and Round 1B (document intelligence) accuracy
"""

import json
import os
import argparse
import re
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import numpy as np
import unicodedata

class MultilingualEvaluator:
    def __init__(self):
        self.devangari_range = range(0x0900, 0x097F + 1)
        self.english_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
        
    def is_valid_devangari(self, text: str) -> bool:
        """Check if text contains valid Devanagari characters"""
        if not text:
            return True
        
        has_devangari = any(ord(c) in self.devangari_range for c in text)
        has_english = any(c in self.english_chars for c in text)
        return has_devangari or has_english
    
    def detect_language_mix(self, text: str) -> Dict[str, bool]:
        """Detect presence of different languages in text"""
        if not text:
            return {"en": False, "hi": False, "mr": False}
        
        devangari_chars = sum(1 for c in text if ord(c) in self.devangari_range)
        english_chars = sum(1 for c in text if c in self.english_chars)
        total_chars = len([c for c in text if c.isalpha()])
        
        return {
            "en": english_chars > 0,
            "hi": devangari_chars > 0,
            "mr": devangari_chars > 0  # Marathi uses Devanagari script
        }

def calculate_metrics(true_positives: int, false_positives: int, false_negatives: int) -> Dict[str, float]:
    """Calculate precision, recall, and F1 score manually"""
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1
    }

class R1AEvaluator:
    def __init__(self):
        self.multilingual_eval = MultilingualEvaluator()
    
    def load_ground_truth(self, ground_truth_dir: str) -> Dict[str, Dict]:
        """Load ground truth annotations"""
        ground_truth = {}
        if not os.path.exists(ground_truth_dir):
            print(f"[WARNING] Ground truth directory {ground_truth_dir} not found")
            return ground_truth
            
        for filename in os.listdir(ground_truth_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(ground_truth_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        ground_truth[filename] = json.load(f)
                except Exception as e:
                    print(f"[ERROR] Could not load ground truth {filepath}: {e}")
        return ground_truth
    
    def evaluate_heading_detection(self, output_file: str, ground_truth: Dict = None) -> Dict[str, Any]:
        """Evaluate heading detection accuracy"""
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
        except Exception as e:
            print(f"[ERROR] Could not load output file {output_file}: {e}")
            return {"error": str(e)}
        
        # Extract headings from output
        predicted_headings = []
        for heading in result.get("outline", []):
            if isinstance(heading.get("text"), dict):
                # Multilingual format
                for lang, text in heading["text"].items():
                    predicted_headings.append({
                        "level": heading.get("level", "H1"),
                        "text": text,
                        "page": heading.get("page", 1),
                        "lang": lang
                    })
            else:
                # Single language format
                predicted_headings.append({
                    "level": heading.get("level", "H1"),
                    "text": str(heading.get("text", "")),
                    "page": heading.get("page", 1),
                    "lang": "en"
                })
        
        # Multilingual correctness check
        multilingual_issues = []
        for heading in predicted_headings:
            text = heading["text"]
            if not self.multilingual_eval.is_valid_devangari(text):
                multilingual_issues.append({
                    "heading": heading,
                    "issue": "Invalid Devanagari characters or garbled text"
                })
        
        # Calculate metrics if ground truth available
        metrics = {
            "total_headings": len(predicted_headings),
            "multilingual_issues": len(multilingual_issues),
            "multilingual_issues_details": multilingual_issues,
            "title_detected": bool(result.get("title")),
            "title_languages": list(result.get("title", {}).keys()) if result.get("title") else []
        }
        
        if ground_truth:
            # Compare with ground truth
            gt_headings = ground_truth.get("outline", [])
            true_positives = 0
            false_positives = len(predicted_headings)
            false_negatives = len(gt_headings)
            
            for pred in predicted_headings:
                for gt in gt_headings:
                    if (pred["text"].lower().strip() == gt["text"].lower().strip() and
                        pred["level"] == gt["level"]):
                        true_positives += 1
                        false_positives -= 1
                        false_negatives -= 1
                        break
            
            metrics.update(calculate_metrics(true_positives, false_positives, false_negatives))
            metrics.update({
                "true_positives": true_positives,
                "false_positives": false_positives,
                "false_negatives": false_negatives
            })
        
        return metrics
    
    def evaluate_multilingual_correctness(self, output_file: str) -> Dict[str, Any]:
        """Evaluate multilingual text correctness"""
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
        except Exception as e:
            return {"error": str(e)}
        
        issues = []
        total_texts = 0
        valid_texts = 0
        
        # Check title
        title = result.get("title", {})
        for lang, text in title.items():
            total_texts += 1
            if self.multilingual_eval.is_valid_devangari(text):
                valid_texts += 1
            else:
                issues.append({
                    "type": "title",
                    "lang": lang,
                    "text": text,
                    "issue": "Invalid or garbled text"
                })
        
        # Check headings
        for heading in result.get("outline", []):
            if isinstance(heading.get("text"), dict):
                for lang, text in heading["text"].items():
                    total_texts += 1
                    if self.multilingual_eval.is_valid_devangari(text):
                        valid_texts += 1
                    else:
                        issues.append({
                            "type": "heading",
                            "level": heading.get("level"),
                            "lang": lang,
                            "text": text,
                            "issue": "Invalid or garbled text"
                        })
        
        return {
            "total_texts": total_texts,
            "valid_texts": valid_texts,
            "invalid_texts": len(issues),
            "accuracy": valid_texts / total_texts if total_texts > 0 else 0.0,
            "issues": issues
        }

class R1BEvaluator:
    def __init__(self):
        self.multilingual_eval = MultilingualEvaluator()
    
    def evaluate_semantic_relevance(self, output_file: str, persona: str, job_description: str) -> Dict[str, Any]:
        """Evaluate semantic relevance of extracted sections"""
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
        except Exception as e:
            return {"error": str(e)}
        
        # Extract sections
        sections = result.get("extracted_sections", [])
        sub_sections = result.get("sub_section_analysis", [])
        
        # Check relevance scores
        relevance_scores = []
        multilingual_issues = []
        
        for section in sections:
            section_title = section.get("section_title", {})
            for lang, text in section_title.items():
                if not self.multilingual_eval.is_valid_devangari(text):
                    multilingual_issues.append({
                        "section": section,
                        "lang": lang,
                        "text": text,
                        "issue": "Invalid or garbled text"
                    })
        
        # Check ranking quality
        ranking_quality = {
            "total_sections": len(sections),
            "top_5_relevance": len(sections[:5]),
            "multilingual_issues": len(multilingual_issues),
            "multilingual_issues_details": multilingual_issues
        }
        
        # Check if sections contain relevant keywords
        relevant_keywords = ["gnn", "drug", "discovery", "molecular", "neural", "biology", "computational"]
        keyword_matches = 0
        
        for section in sections:
            section_text = " ".join(section.get("section_title", {}).values()).lower()
            if any(keyword in section_text for keyword in relevant_keywords):
                keyword_matches += 1
        
        ranking_quality["keyword_matches"] = keyword_matches
        ranking_quality["keyword_accuracy"] = keyword_matches / len(sections) if sections else 0.0
        
        return ranking_quality
    
    def evaluate_bilingual_detection(self, output_file: str) -> Dict[str, Any]:
        """Evaluate bilingual text detection and preservation"""
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
        except Exception as e:
            return {"error": str(e)}
        
        sections = result.get("extracted_sections", [])
        sub_sections = result.get("sub_section_analysis", [])
        
        bilingual_sections = 0
        english_only = 0
        devangari_only = 0
        total_sections = len(sections)
        
        for section in sections:
            section_title = section.get("section_title", {})
            languages = self.multilingual_eval.detect_language_mix(" ".join(section_title.values()))
            
            if languages["en"] and (languages["hi"] or languages["mr"]):
                bilingual_sections += 1
            elif languages["en"]:
                english_only += 1
            elif languages["hi"] or languages["mr"]:
                devangari_only += 1
        
        return {
            "total_sections": total_sections,
            "bilingual_sections": bilingual_sections,
            "english_only": english_only,
            "devangari_only": devangari_only,
            "bilingual_percentage": bilingual_sections / total_sections if total_sections > 0 else 0.0
        }

def main():
    parser = argparse.ArgumentParser(description="Evaluate Round 1A and Round 1B accuracy")
    parser.add_argument("--mode", choices=["r1a", "r1b", "both"], default="both", 
                       help="Evaluation mode")
    parser.add_argument("--ground_truth_dir", type=str, default="ground_truth",
                       help="Directory containing ground truth annotations")
    parser.add_argument("--output_1a_dir", type=str, default="output_1A",
                       help="Directory containing R1A outputs")
    parser.add_argument("--output_1b_dir", type=str, default="output_1B",
                       help="Directory containing R1B outputs")
    parser.add_argument("--detailed", action="store_true",
                       help="Show detailed evaluation results")
    
    args = parser.parse_args()
    
    print("🔍 Adobe Hackathon Evaluation Pipeline")
    print("=" * 50)
    
    if args.mode in ["r1a", "both"]:
        print("\n📊 Evaluating Round 1A (Heading Detection)")
        print("-" * 40)
        
        r1a_evaluator = R1AEvaluator()
        ground_truth = r1a_evaluator.load_ground_truth(args.ground_truth_dir)
        
        r1a_outputs = [f for f in os.listdir(args.output_1a_dir) if f.endswith('.json')]
        
        for output_file in r1a_outputs:
            output_path = os.path.join(args.output_1a_dir, output_file)
            print(f"\n📄 Evaluating: {output_file}")
            
            # Get corresponding ground truth
            gt_key = output_file
            gt_data = ground_truth.get(gt_key, {})
            
            # Evaluate heading detection
            heading_metrics = r1a_evaluator.evaluate_heading_detection(output_path, gt_data)
            
            # Evaluate multilingual correctness
            multilingual_metrics = r1a_evaluator.evaluate_multilingual_correctness(output_path)
            
            # Print results
            print(f"  📈 Heading Detection:")
            print(f"    - Total headings: {heading_metrics.get('total_headings', 0)}")
            print(f"    - Title detected: {heading_metrics.get('title_detected', False)}")
            print(f"    - Title languages: {heading_metrics.get('title_languages', [])}")
            
            if 'precision' in heading_metrics:
                print(f"    - Precision: {heading_metrics['precision']:.3f}")
                print(f"    - Recall: {heading_metrics['recall']:.3f}")
                print(f"    - F1 Score: {heading_metrics['f1_score']:.3f}")
            
            print(f"  🌐 Multilingual Correctness:")
            print(f"    - Valid texts: {multilingual_metrics.get('valid_texts', 0)}/{multilingual_metrics.get('total_texts', 0)}")
            print(f"    - Accuracy: {multilingual_metrics.get('accuracy', 0):.3f}")
            
            if multilingual_metrics.get('issues'):
                print(f"    - Issues found: {len(multilingual_metrics['issues'])}")
                if args.detailed:
                    for issue in multilingual_metrics['issues'][:3]:  # Show first 3 issues
                        print(f"      * {issue['type']} ({issue['lang']}): {issue['text'][:50]}...")
    
    if args.mode in ["r1b", "both"]:
        print("\n📊 Evaluating Round 1B (Document Intelligence)")
        print("-" * 40)
        
        r1b_evaluator = R1BEvaluator()
        
        r1b_outputs = [f for f in os.listdir(args.output_1b_dir) if f.endswith('.json')]
        
        for output_file in r1b_outputs:
            output_path = os.path.join(args.output_1b_dir, output_file)
            print(f"\n📄 Evaluating: {output_file}")
            
            # Evaluate semantic relevance
            relevance_metrics = r1b_evaluator.evaluate_semantic_relevance(
                output_path, 
                "PhD Researcher in Computational Biology",
                "Review GNNs for drug discovery"
            )
            
            # Evaluate bilingual detection
            bilingual_metrics = r1b_evaluator.evaluate_bilingual_detection(output_path)
            
            # Print results
            print(f"  🎯 Semantic Relevance:")
            print(f"    - Total sections: {relevance_metrics.get('total_sections', 0)}")
            print(f"    - Keyword matches: {relevance_metrics.get('keyword_matches', 0)}")
            print(f"    - Keyword accuracy: {relevance_metrics.get('keyword_accuracy', 0):.3f}")
            
            print(f"  🌐 Bilingual Detection:")
            print(f"    - Bilingual sections: {bilingual_metrics.get('bilingual_sections', 0)}")
            print(f"    - English only: {bilingual_metrics.get('english_only', 0)}")
            print(f"    - Devanagari only: {bilingual_metrics.get('devangari_only', 0)}")
            print(f"    - Bilingual percentage: {bilingual_metrics.get('bilingual_percentage', 0):.3f}")
            
            if relevance_metrics.get('multilingual_issues'):
                print(f"    - Multilingual issues: {relevance_metrics['multilingual_issues']}")
    
    print("\n✅ Evaluation Complete!")
    print("\n📋 Summary:")
    print("- Check for garbled Unicode in Devanagari text")
    print("- Verify heading detection accuracy")
    print("- Assess semantic relevance for R1B")
    print("- Monitor bilingual content preservation")

if __name__ == "__main__":
    main() 