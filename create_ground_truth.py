#!/usr/bin/env python3
"""
Ground Truth Creation Tool for Adobe Hackathon Evaluation
Helps create manual annotations for evaluating Round 1A and Round 1B accuracy
"""

import json
import os
import argparse
from typing import Dict, List, Any

def create_ground_truth_template(pdf_name: str, outline: List[Dict]) -> Dict[str, Any]:
    """Create a ground truth template based on extracted outline"""
    template = {
        "pdf_name": pdf_name,
        "title": {
            "en": "MANUAL_TITLE_HERE",
            "hi": "मैनुअल_शीर्षक_यहाँ",
            "mr": "मॅन्युअल_शीर्षक_इथे"
        },
        "outline": []
    }
    
    # Create template entries for each detected heading
    for i, heading in enumerate(outline):
        template["outline"].append({
            "level": heading.get("level", "H1"),
            "text": {
                "en": f"MANUAL_HEADING_{i+1}_ENGLISH",
                "hi": f"मैनुअल_शीर्षक_{i+1}_हिंदी",
                "mr": f"मॅन्युअल_शीर्षक_{i+1}_मराठी"
            },
            "page": heading.get("page", 1),
            "is_correct": True,  # Mark as correct/incorrect
            "notes": "Manual annotation notes here"
        })
    
    return template

def create_r1b_ground_truth_template() -> Dict[str, Any]:
    """Create ground truth template for R1B evaluation"""
    return {
        "persona": "PhD Researcher in Computational Biology",
        "job_description": "Review GNNs for drug discovery",
        "expected_sections": [
            {
                "document": "sample_research_paper.pdf",
                "page_number": 1,
                "section_title": {
                    "en": "Introduction to Graph Neural Networks",
                    "hi": "ग्राफ न्यूरल नेटवर्क का परिचय",
                    "mr": "ग्राफ न्यूरल नेटवर्कचा परिचय"
                },
                "expected_rank": 1,
                "relevance_score": 0.95,
                "keywords_present": ["gnn", "neural", "graph"],
                "notes": "Highly relevant section for the persona"
            }
        ],
        "evaluation_criteria": {
            "semantic_relevance_threshold": 0.7,
            "multilingual_preservation": True,
            "ranking_accuracy": True
        }
    }

def main():
    parser = argparse.ArgumentParser(description="Create ground truth templates for evaluation")
    parser.add_argument("--mode", choices=["r1a", "r1b", "both"], default="both",
                       help="Create templates for which round")
    parser.add_argument("--output_dir", type=str, default="ground_truth",
                       help="Output directory for ground truth files")
    parser.add_argument("--input_1a_dir", type=str, default="output_1A",
                       help="Directory containing R1A outputs to base templates on")
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("📝 Creating Ground Truth Templates")
    print("=" * 40)
    
    if args.mode in ["r1a", "both"]:
        print("\n📊 Creating R1A Ground Truth Templates")
        print("-" * 30)
        
        # Load existing R1A outputs to create templates
        if os.path.exists(args.input_1a_dir):
            for filename in os.listdir(args.input_1a_dir):
                if filename.endswith('.json'):
                    input_path = os.path.join(args.input_1a_dir, filename)
                    try:
                        with open(input_path, 'r', encoding='utf-8') as f:
                            outline_data = json.load(f)
                        
                        # Create ground truth template
                        template = create_ground_truth_template(filename, outline_data.get("outline", []))
                        
                        # Save template
                        output_filename = filename.replace('.json', '_ground_truth.json')
                        output_path = os.path.join(args.output_dir, output_filename)
                        
                        with open(output_path, 'w', encoding='utf-8') as f:
                            json.dump(template, f, ensure_ascii=False, indent=2)
                        
                        print(f"✅ Created: {output_filename}")
                        print(f"   - Headings to annotate: {len(template['outline'])}")
                        
                    except Exception as e:
                        print(f"❌ Error processing {filename}: {e}")
    
    if args.mode in ["r1b", "both"]:
        print("\n📊 Creating R1B Ground Truth Template")
        print("-" * 30)
        
        template = create_r1b_ground_truth_template()
        output_path = os.path.join(args.output_dir, "r1b_ground_truth_template.json")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Created: r1b_ground_truth_template.json")
        print(f"   - Expected sections: {len(template['expected_sections'])}")
    
    print(f"\n📁 Ground truth templates saved to: {args.output_dir}")
    print("\n📋 Next Steps:")
    print("1. Manually annotate the templates with correct titles and headings")
    print("2. Mark which detected headings are correct/incorrect")
    print("3. Add notes about multilingual correctness")
    print("4. Run evaluation with: python evaluate_accuracy.py --ground_truth_dir ground_truth")

if __name__ == "__main__":
    main() 