# Specify the base image. Use a lightweight Python image compatible with linux/amd64.
# For example, python:3.9-slim-buster is a good choice.
FROM --platform=linux/amd64 python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the Python scripts into the container
# Assuming your Python files are named main.py, r1a_outline_extractor.py, r1b_document_intelligence.py
# and any shared utility files.
COPY . /app/

# Install Python dependencies.
# You MUST create a requirements.txt file listing all your Python libraries.
# Example requirements.txt content:
# PyMuPDF==1.22.5
# # If using Sentence Transformers (ensure model is downloaded and within size limits)
# # sentence-transformers
# # If using scikit-learn for TF-IDF/cosine similarity
# # scikit-learn
# # numpy
# # scipy
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# If you are using a pre-trained model (e.g., for Sentence Transformers),
# you need to copy its downloaded weights into the image.
# Example: Assuming your model is in ./models/sentence-transformer-mini-lm-l6-v2/
# RUN mkdir -p /app/models/
# COPY models/sentence-transformer-mini-lm-l6-v2 /app/models/sentence-transformer-mini-lm-l6-v2/

# Define the entrypoint command.
# This script should be the one that orchestrates the R1A/R1B logic.
# The hackathon specifies inputs in /app/input and outputs in /app/output.
# Your script should read from /app/input and write to /app/output.
# Let's assume you have a main.py that calls main_r1a() or main_r1b() based on logic.
# For now, let's assume you call r1a_outline_extractor.py for R1A and r1b_document_intelligence.py for R1B
# The example below will call r1b, which internally uses r1a.

CMD ["python", "r1b_document_intelligence.py"] # Or "python", "main.py" if you have an orchestrator