#!/usr/bin/env python3
"""
Multilingual Text Validation Tool
Validates Devanagari text correctness and detects garbled Unicode
"""

import json
import os
import argparse
import re
import unicodedata
from typing import Dict, List, Tuple, Any
from collections import defaultdict

class MultilingualValidator:
    def __init__(self):
        # Devanagari Unicode range
        self.devangari_range = range(0x0900, 0x097F + 1)
        # Common Devanagari characters
        self.common_devangari = {
            'अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ऋ', 'ए', 'ऐ', 'ओ', 'औ',
            'क', 'ख', 'ग', 'घ', 'ङ', 'च', 'छ', 'ज', 'झ', 'ञ',
            'ट', 'ठ', 'ड', 'ढ', 'ण', 'त', 'थ', 'द', 'ध', 'न',
            'प', 'फ', 'ब', 'भ', 'म', 'य', 'र', 'ल', 'व', 'श', 'ष', 'स', 'ह',
            'ा', 'ि', 'ी', 'ु', 'ू', 'ृ', 'े', 'ै', 'ो', 'ौ',
            'ं', 'ः', '्', '।', '॥'
        }
        
    def is_valid_devangari(self, text: str) -> bool:
        """Check if text contains valid Devanagari characters"""
        if not text:
            return True
        
        # Check for Devanagari characters
        has_devangari = any(ord(c) in self.devangari_range for c in text)
        if not has_devangari:
            return True  # No Devanagari, so no issue
        
        # Check for common garbled patterns
        garbled_patterns = [
            r'[^\u0900-\u097F\s\.,!?;:()\[\]{}"\'-]',  # Non-Devanagari chars mixed
            r'[A-Za-z0-9]+[\u0900-\u097F]+',  # Latin + Devanagari mixed
            r'[\u0900-\u097F]+[A-Za-z0-9]+',  # Devanagari + Latin mixed
        ]
        
        for pattern in garbled_patterns:
            if re.search(pattern, text):
                return False
        
        return True
    
    def detect_garbled_text(self, text: str) -> Dict[str, Any]:
        """Detect specific types of garbled text"""
        issues = []
        
        if not text:
            return {"is_garbled": False, "issues": []}
        
        # Check for mixed scripts
        devangari_chars = [c for c in text if ord(c) in self.devangari_range]
        latin_chars = [c for c in text if c.isalpha() and ord(c) < 128]
        
        if devangari_chars and latin_chars:
            issues.append({
                "type": "mixed_scripts",
                "description": "Devanagari and Latin characters mixed",
                "devangari_count": len(devangari_chars),
                "latin_count": len(latin_chars)
            })
        
        # Check for invalid Unicode sequences
        try:
            text.encode('utf-8').decode('utf-8')
        except UnicodeError:
            issues.append({
                "type": "unicode_error",
                "description": "Invalid Unicode sequence"
            })
        
        # Check for repeated characters (common in garbled text)
        repeated_chars = re.findall(r'(.)\1{2,}', text)
        if repeated_chars:
            issues.append({
                "type": "repeated_characters",
                "description": "Repeated characters detected",
                "repeated_chars": list(set(repeated_chars))
            })
        
        # Check for unusual character combinations
        unusual_patterns = [
            r'[^\u0900-\u097F\s\.,!?;:()\[\]{}"\'-]',  # Non-standard chars
            r'[A-Z]{3,}',  # All caps words
            r'[0-9]+[A-Za-z]+',  # Numbers followed by letters
        ]
        
        for pattern in unusual_patterns:
            matches = re.findall(pattern, text)
            if matches:
                issues.append({
                    "type": "unusual_patterns",
                    "description": "Unusual character patterns",
                    "patterns": matches[:5]  # Limit to first 5
                })
        
        return {
            "is_garbled": len(issues) > 0,
            "issues": issues,
            "text_length": len(text),
            "devangari_chars": len(devangari_chars),
            "latin_chars": len(latin_chars)
        }
    
    def validate_json_file(self, file_path: str) -> Dict[str, Any]:
        """Validate a JSON file for multilingual correctness"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            return {"error": str(e)}
        
        validation_results = {
            "file": file_path,
            "total_texts": 0,
            "valid_texts": 0,
            "garbled_texts": 0,
            "issues": []
        }
        
        def validate_text_field(text, field_path):
            if isinstance(text, dict):
                for lang, content in text.items():
                    validate_text_field(content, f"{field_path}.{lang}")
            elif isinstance(text, str):
                validation_results["total_texts"] += 1
                
                if self.is_valid_devangari(text):
                    validation_results["valid_texts"] += 1
                else:
                    validation_results["garbled_texts"] += 1
                    garbled_info = self.detect_garbled_text(text)
                    validation_results["issues"].append({
                        "field": field_path,
                        "text": text[:100] + "..." if len(text) > 100 else text,
                        "garbled_info": garbled_info
                    })
        
        # Validate title
        if "title" in data:
            validate_text_field(data["title"], "title")
        
        # Validate outline headings
        if "outline" in data:
            for i, heading in enumerate(data["outline"]):
                if "text" in heading:
                    validate_text_field(heading["text"], f"outline[{i}].text")
        
        # Validate section titles (for R1B)
        if "extracted_sections" in data:
            for i, section in enumerate(data["extracted_sections"]):
                if "section_title" in section:
                    validate_text_field(section["section_title"], f"extracted_sections[{i}].section_title")
        
        # Calculate accuracy
        if validation_results["total_texts"] > 0:
            validation_results["accuracy"] = validation_results["valid_texts"] / validation_results["total_texts"]
        else:
            validation_results["accuracy"] = 0.0
        
        return validation_results

def main():
    parser = argparse.ArgumentParser(description="Validate multilingual text correctness")
    parser.add_argument("--input_dir", type=str, default="output_1A",
                       help="Directory containing JSON files to validate")
    parser.add_argument("--output_file", type=str, default="multilingual_validation_report.json",
                       help="Output file for validation report")
    parser.add_argument("--detailed", action="store_true",
                       help="Show detailed validation results")
    
    args = parser.parse_args()
    
    validator = MultilingualValidator()
    
    print("🔍 Multilingual Text Validation")
    print("=" * 40)
    
    all_results = []
    total_files = 0
    total_issues = 0
    
    if os.path.exists(args.input_dir):
        for filename in os.listdir(args.input_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(args.input_dir, filename)
                print(f"\n📄 Validating: {filename}")
                
                result = validator.validate_json_file(file_path)
                all_results.append(result)
                total_files += 1
                
                if "error" in result:
                    print(f"❌ Error: {result['error']}")
                    continue
                
                print(f"  📊 Results:")
                print(f"    - Total texts: {result['total_texts']}")
                print(f"    - Valid texts: {result['valid_texts']}")
                print(f"    - Garbled texts: {result['garbled_texts']}")
                print(f"    - Accuracy: {result.get('accuracy', 0):.3f}")
                
                if result['issues']:
                    total_issues += len(result['issues'])
                    print(f"    - Issues found: {len(result['issues'])}")
                    
                    if args.detailed:
                        for issue in result['issues'][:3]:  # Show first 3 issues
                            print(f"      * {issue['field']}: {issue['text']}")
                            for garbled_issue in issue['garbled_info']['issues'][:2]:
                                print(f"        - {garbled_issue['type']}: {garbled_issue['description']}")
    
    # Generate summary report
    summary = {
        "total_files_processed": total_files,
        "total_issues_found": total_issues,
        "files_with_issues": len([r for r in all_results if r.get('garbled_texts', 0) > 0]),
        "overall_accuracy": sum(r.get('accuracy', 0) for r in all_results) / len(all_results) if all_results else 0,
        "detailed_results": all_results
    }
    
    # Save detailed report
    with open(args.output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 Summary:")
    print(f"  - Files processed: {total_files}")
    print(f"  - Files with issues: {summary['files_with_issues']}")
    print(f"  - Total issues found: {total_issues}")
    print(f"  - Overall accuracy: {summary['overall_accuracy']:.3f}")
    print(f"  - Detailed report saved to: {args.output_file}")
    
    # Flag problematic files
    if summary['files_with_issues'] > 0:
        print(f"\n⚠️  Files with multilingual issues:")
        for result in all_results:
            if result.get('garbled_texts', 0) > 0:
                print(f"  - {os.path.basename(result['file'])}: {result['garbled_texts']} issues")

if __name__ == "__main__":
    main() 