import os
import sys
import json
from r1a_outline_extractor import extract_document_info
from r1b_document_intelligence import run_persona_driven_analysis

def execute_r1a_logic(input_dir, output_dir):
    """Executes Round 1A logic: Extracts outline and tables for all PDFs."""
    print("Executing Round 1A: Outline Extraction...")
    os.makedirs(output_dir, exist_ok=True)
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)
            output_filename = filename.replace(".pdf", ".json")
            output_path = os.path.join(output_dir, output_filename)
            try:
                result = extract_document_info(pdf_path)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"R1A: Generated {output_path}")
            except Exception as e:
                print(f"R1A Error processing {pdf_path}: {e}")

def read_text_file_if_exists(path, default_value):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return default_value

def execute_r1b_logic(input_dir, output_dir):
    """Executes Round 1B logic: Persona-based document intelligence using semantic search."""
    print("Executing Round 1B: Persona-Driven Document Intelligence...")
    os.makedirs(output_dir, exist_ok=True)
    persona_path = os.path.join(input_dir, 'persona.txt')
    job_path = os.path.join(input_dir, 'job.txt')
    persona_definition = read_text_file_if_exists(persona_path, "PhD Researcher in Computational Biology")
    job_to_be_done = read_text_file_if_exists(job_path, "Prepare a comprehensive literature review focusing on methodologies, datasets, and performance benchmarks")
    r1b_pdf_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
    for pdf_file in r1b_pdf_files:
        r1a_json_path = os.path.join(output_dir, os.path.basename(pdf_file).replace('.pdf', '.json'))
        if os.path.exists(r1a_json_path):
            with open(r1a_json_path, 'r', encoding='utf-8') as f:
                r1a_result = json.load(f)
            print(f"R1B: Loaded cached R1A outline for {pdf_file}")
        else:
            r1a_result = extract_document_info(pdf_file)
            with open(r1a_json_path, 'w', encoding='utf-8') as f:
                json.dump(r1a_result, f, ensure_ascii=False, indent=2)
            print(f"R1B: Extracted and cached R1A outline for {pdf_file}")
        documents_info = [{"path": pdf_file, "r1a_outline": r1a_result}]
        r1b_result = run_persona_driven_analysis(documents_info, persona_definition, job_to_be_done)
        # Output file: r1_<filename>.json
        output_path_r1b = os.path.join(output_dir, f"r1_{os.path.basename(pdf_file).replace('.pdf', '.json')}")
        with open(output_path_r1b, 'w', encoding='utf-8') as f:
            json.dump(r1b_result, f, ensure_ascii=False, indent=2)
        print(f"R1B: Generated output at {output_path_r1b}")

if __name__ == "__main__":
    # The Docker run command specifies /app/input and /app/output
    input_directory = os.environ.get("INPUT_DIR", "input")
    output_directory = os.environ.get("OUTPUT_DIR", "output")
    # Determine which round to run (via argument), or run both by default
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--round" and sys.argv[2].upper() == "R1A":
        execute_r1a_logic(input_directory, output_directory)
    elif len(sys.argv) > 1 and sys.argv[1].lower() == "--round" and sys.argv[2].upper() == "R1B":
        execute_r1b_logic(input_directory, output_directory)
    else:
        # Default: run R1B, which also covers R1A needs
        print("No specific round specified. Attempting to run R1B logic which incorporates R1A functionality.")
        execute_r1b_logic(input_directory, output_directory)
