Riii, [23-07-2025 14:52]
# Adobe India Hackathon - Connecting the Dots: Round 1B Approach Explanation

## Project Name: Persona-Driven Document Intelligence

This document outlines the methodology for the Round 1B challenge: "Persona-Driven Document Intelligence." The objective is to identify and rank the most relevant sections and sub-sections from a collection of PDFs based on a defined persona and a "job-to-be-done."

## Methodology

Our approach combines the structural understanding gained from Round 1A with semantic analysis to determine content relevance.

1.  Document Pre-processing (Leveraging Round 1A):
    * For each PDF in the collection, we first leverage the outline extraction capabilities developed in Round 1A. This provides a structured view of the document's headings (H1, H2, H3) and their page numbers.
    * The full text of each PDF is also extracted. We then associate segments of this text with the identified headings to form coherent "sections." A "section" is defined as the content following a heading until the next heading of an equal or higher level.

2.  Semantic Understanding through Embeddings:
    * Low-Footprint Semantic Model: To adhere to the strict CPU-only, offline, and model size <= 1GB constraints, we utilize a pre-trained, compact Sentence Transformer model (e.g., all-MiniLM-L6-v2). This model is downloaded offline and included within the Docker image. It is chosen for its balance of semantic understanding capability and small footprint.
    * Embedding Generation:
        * The persona_definition (e.g., "PhD Researcher in Computational Biology") is converted into a numerical vector embedding.
        * The job_to_be_done (e.g., "Prepare a comprehensive literature review focusing on methodologies...") is also converted into an embedding.
        * Each identified document section_title and its associated refined_text (content) is also converted into an embedding.
    * Combined Query Embedding: The persona and job-to-be-done embeddings are combined (e.g., by simple addition or concatenation followed by a linear layer) to form a single "query embedding" that represents the user's information need.

3.  Relevance Scoring and Ranking:
    * Cosine Similarity: For each document section, we calculate the cosine similarity between its embedding and the combined query embedding. Cosine similarity measures the angle between two vectors, with values closer to 1 indicating higher semantic similarity.
    * Importance Ranking: Sections are then ranked in descending order based on their cosine similarity scores. The section with the highest score receives importance_rank 1, the next highest rank 2, and so on.

4.  Sub-section Analysis and Refined Text:
    * For the sub_section_analysis, we retrieve the content of the most relevant sections identified.
    * The refined_text for sub-sections is derived from the most semantically pertinent portions of the extracted sections. This could involve either returning the entire relevant section's content or using an extractive summarization technique (e.g., selecting the top N most relevant sentences within that section based on their individual similarity to the query). Given the time and model size constraints, a simple extraction of the most relevant paragraphs/sentences is preferred over complex generative summarization.

5.  Output Generation:
    The final output is formatted into a JSON structure containing:
    * metadata: Information about input documents, persona, job-to-be-done, and processing timestamp.
    * extracted_sections: A ranked list of the most important sections, including document name, page number, section title, and importance rank.
    * sub_section_analysis: Detailed analysis of sub-sections, including document name, page number, and the refined_text content.

## Constraints Adherence

Riii, [23-07-2025 14:52]
* CPU-Only: All NLP processing is configured to run exclusively on CPU.
* Model Size ($\le 1$GB): A small Sentence Transformer model is selected and packaged, ensuring its total size, including dependencies, remains under 1GB.
* Offline Execution: The solution performs no external API calls or network requests during runtime. All models and resources are bundled within the Docker image.
* Processing Time ($\le 60$ seconds for 3-5 documents): The chosen lightweight NLP model and efficient text processing techniques are intended to meet this performance requirement. Benchmarking will be crucial.

## Future Enhancements

* More sophisticated document layout analysis for improved sectioning.
* Integration of named entity recognition (NER) to better understand persona and job context.
* Fine-tuning the chosen semantic model on domain-specific data if allowed and feasible within constraints.