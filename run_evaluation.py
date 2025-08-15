#!/usr/bin/env python3
"""
Main Evaluation Runner for Adobe Hackathon
Orchestrates the complete evaluation pipeline for Round 1A and Round 1B
"""

import os
import sys
import subprocess
import json
import argparse
from datetime import datetime

def run_command(command: str, description: str) -> bool:
    """Run a command and return success status"""
    print(f"\n🔄 {description}")
    print(f"Command: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Success")
            if result.stdout:
                print("Output:", result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
            return True
        else:
            print("❌ Failed")
            if result.stderr:
                print("Error:", result.stderr)
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking Dependencies")
    print("=" * 30)
    
    required_files = [
        "r1a_outline_extractor.py",
        "r1b_document_intelligence.py",
        "evaluate_accuracy.py",
        "validate_multilingual.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files found")
    return True

def run_r1a_evaluation():
    """Run Round 1A evaluation"""
    print("\n📊 Round 1A Evaluation")
    print("=" * 30)
    
    # Step 1: Run R1A extraction
    if not run_command("python r1a_outline_extractor.py", "Running R1A outline extraction"):
        return False
    
    # Step 2: Validate multilingual correctness
    if not run_command("python validate_multilingual.py --input_dir output_1A --detailed", 
                      "Validating multilingual text correctness"):
        return False
    
    # Step 3: Run accuracy evaluation
    if not run_command("python evaluate_accuracy.py --mode r1a --detailed", 
                      "Evaluating R1A accuracy"):
        return False
    
    return True

def run_r1b_evaluation():
    """Run Round 1B evaluation"""
    print("\n📊 Round 1B Evaluation")
    print("=" * 30)
    
    # Step 1: Run R1B extraction
    if not run_command("python r1b_document_intelligence.py", "Running R1B document intelligence"):
        return False
    
    # Step 2: Validate multilingual correctness
    if not run_command("python validate_multilingual.py --input_dir output_1B --detailed", 
                      "Validating multilingual text correctness"):
        return False
    
    # Step 3: Run accuracy evaluation
    if not run_command("python evaluate_accuracy.py --mode r1b --detailed", 
                      "Evaluating R1B accuracy"):
        return False
    
    return True

def generate_evaluation_report():
    """Generate a comprehensive evaluation report"""
    print("\n📋 Generating Evaluation Report")
    print("=" * 30)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "evaluation_summary": {},
        "r1a_results": {},
        "r1b_results": {},
        "multilingual_validation": {},
        "recommendations": []
    }
    
    # Collect R1A results
    r1a_files = [f for f in os.listdir("output_1A") if f.endswith('.json')]
    report["r1a_results"]["files_processed"] = len(r1a_files)
    
    # Check for empty or problematic files
    problematic_files = []
    for file in r1a_files:
        file_path = os.path.join("output_1A", file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not data.get("outline") or len(data["outline"]) == 0:
                    problematic_files.append(f"{file}: No headings detected")
                if not data.get("title") or len(data["title"]) == 0:
                    problematic_files.append(f"{file}: No title detected")
        except Exception as e:
            problematic_files.append(f"{file}: Error reading file - {e}")
    
    report["r1a_results"]["problematic_files"] = problematic_files
    
    # Collect R1B results
    r1b_files = [f for f in os.listdir("output_1B") if f.endswith('.json')]
    report["r1b_results"]["files_processed"] = len(r1b_files)
    
    # Generate recommendations
    recommendations = []
    
    if problematic_files:
        recommendations.append("Fix heading detection in problematic R1A files")
    
    if len(r1a_files) == 0:
        recommendations.append("No R1A output files found - check input_1A directory")
    
    if len(r1b_files) == 0:
        recommendations.append("No R1B output files found - check input_1B directory")
    
    # Check for multilingual issues
    try:
        with open("multilingual_validation_report.json", 'r', encoding='utf-8') as f:
            validation_data = json.load(f)
            if validation_data.get("files_with_issues", 0) > 0:
                recommendations.append("Fix multilingual text encoding issues")
    except FileNotFoundError:
        recommendations.append("Run multilingual validation to check for encoding issues")
    
    report["recommendations"] = recommendations
    
    # Save report
    with open("evaluation_report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("✅ Evaluation report saved to: evaluation_report.json")
    
    # Print summary
    print(f"\n📊 Evaluation Summary:")
    print(f"  - R1A files processed: {report['r1a_results']['files_processed']}")
    print(f"  - R1B files processed: {report['r1b_results']['files_processed']}")
    print(f"  - Problematic files: {len(problematic_files)}")
    print(f"  - Recommendations: {len(recommendations)}")
    
    if recommendations:
        print(f"\n💡 Recommendations:")
        for rec in recommendations:
            print(f"  - {rec}")

def main():
    parser = argparse.ArgumentParser(description="Run complete evaluation pipeline")
    parser.add_argument("--mode", choices=["r1a", "r1b", "both"], default="both",
                       help="Evaluation mode")
    parser.add_argument("--create-ground-truth", action="store_true",
                       help="Create ground truth templates")
    parser.add_argument("--skip-extraction", action="store_true",
                       help="Skip PDF extraction, only run evaluation")
    
    args = parser.parse_args()
    
    print("🚀 Adobe Hackathon Evaluation Pipeline")
    print("=" * 50)
    print(f"Mode: {args.mode}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependencies check failed. Exiting.")
        sys.exit(1)
    
    # Create ground truth templates if requested
    if args.create_ground_truth:
        print("\n📝 Creating Ground Truth Templates")
        run_command("python create_ground_truth.py --mode both", "Creating ground truth templates")
    
    # Run evaluations
    success = True
    
    if args.mode in ["r1a", "both"] and not args.skip_extraction:
        success &= run_r1a_evaluation()
    
    if args.mode in ["r1b", "both"] and not args.skip_extraction:
        success &= run_r1b_evaluation()
    
    # Generate final report
    generate_evaluation_report()
    
    if success:
        print("\n✅ Evaluation pipeline completed successfully!")
    else:
        print("\n❌ Evaluation pipeline completed with errors!")
        sys.exit(1)

if __name__ == "__main__":
    main() 