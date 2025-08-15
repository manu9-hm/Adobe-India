# Adobe Hackathon Project

This project processes and evaluates multilingual PDFs for document intelligence and heading extraction. It supports both English and Indic languages (Hindi, Marathi) and provides a robust evaluation pipeline.

---

## 📁 Directory & File Structure

```
Adobe_Hackathon/
├── input_1A/                    # Multilingual PDFs for Round 1A (heading extraction)
├── output_1A/                   # JSON outputs from Round 1A
├── input_1B/                    # Research PDFs for Round 1B (document intelligence)
├── output_1B/                   # JSON outputs from Round 1B
├── multilingual_model/          # Sentence transformer model files (offline, no API key needed)
├── ground_truth/                # Manual ground truth annotations for evaluation (create with script)
├── r1a_outline_extractor.py     # Extracts titles/headings from PDFs (Round 1A)
├── r1b_document_intelligence.py # Persona-based document intelligence (Round 1B)
├── evaluate_accuracy.py         # Main evaluation script (precision, recall, F1, etc.)
├── validate_multilingual.py     # Checks for garbled Unicode/multilingual correctness
├── create_ground_truth.py       # Creates ground truth templates for manual annotation
├── run_evaluation.py            # Orchestrates the full evaluation pipeline
├── requirements.txt             # Python dependencies
├── download_model.py            # Script to download the model (if needed)
├── dockerfile                   # Docker setup (optional)
├── EVALUATION_README.md         # Detailed evaluation pipeline documentation
└── README.md                    # (This file)
```

---

## 📝 File Descriptions

- **r1a_outline_extractor.py**
  - Extracts document title and hierarchical headings (H1, H2, H3) from multilingual PDFs in `input_1A/`.
  - Outputs JSON to `output_1A/`.

- **r1b_document_intelligence.py**
  - Given a persona and job description, extracts and ranks relevant sections from PDFs in `input_1B/`.
  - Outputs JSON to `output_1B/`.
  - **Note**: Has dependency issues with sentence transformers.

- **r1b_document_intelligence_simple.py**
  - Simplified version of R1B that works without sentence transformers.
  - Uses keyword-based relevance scoring instead of semantic similarity.
  - Outputs JSON to `output_1B/r1b_output_simple.json`.

- **evaluate_accuracy.py**
  - Evaluates outputs against ground truth (if available).
  - Computes precision, recall, F1, multilingual correctness, and semantic relevance.

- **validate_multilingual.py**
  - Checks all output JSONs for garbled Unicode, mixed scripts, and multilingual text issues.

- **create_ground_truth.py**
  - Generates ground truth templates for manual annotation based on current outputs.

- **run_evaluation.py**
  - Runs the full pipeline: extraction, validation, evaluation, and reporting.

- **requirements.txt**
  - Lists all required Python packages.

- **download_model.py**
  - Downloads the sentence transformer model (if not already present).

- **dockerfile**
  - Docker setup for reproducible environment (optional).

---

## 🚀 Commands to Run

### 1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Run Extraction Scripts**
```bash
# Extract headings/titles (Round 1A)
python r1a_outline_extractor.py

# Extract persona-based relevant sections (Round 1B) - Simplified version
python r1b_document_intelligence_simple.py

# Original R1B (has dependency issues)
# python r1b_document_intelligence.py
```

### 3. **Validate Multilingual Output**
```bash
# Check for garbled Unicode and multilingual issues in output_1A
python validate_multilingual.py --input_dir output_1A --detailed

# Check for garbled Unicode and multilingual issues in output_1B
python validate_multilingual.py --input_dir output_1B --detailed
```

### 4. **Evaluate Accuracy**
```bash
# Evaluate Round 1A (heading detection)
python evaluate_accuracy.py --mode r1a --detailed

# Evaluate Round 1B (document intelligence)
python evaluate_accuracy.py --mode r1b --detailed

# Evaluate both rounds
python evaluate_accuracy.py --mode both --detailed
```

### 5. **Create Ground Truth Templates**
```bash
python create_ground_truth.py --mode both
```
- Edit the files in `ground_truth/` to manually mark correct/incorrect headings and expected relevant sections.

### 6. **Run the Complete Evaluation Pipeline**
```bash
python run_evaluation.py --mode both
```
- This will run extraction, validation, evaluation, and generate a summary report.

---

## 📋 Notes
- All scripts are designed to work offline (no API keys required).
- Outputs are always written to `output_1A/` and `output_1B/`.
- For best results, create and annotate ground truth files in `ground_truth/`.
- The evaluation pipeline will flag any PDF with garbled Unicode or missing/incorrect headings.

---

## 📞 Support
If you encounter issues:
- Check the detailed error messages in the terminal.
- Review the `EVALUATION_README.md` for troubleshooting and recommendations.
- Ensure all input files are in the correct format and the model is present in `multilingual_model/`.

---

**Last updated:** 2025-07-26