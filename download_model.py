from sentence_transformers import SentenceTransformer

# Load and download the model locally
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Save to local folder
model.save('./multilingual_model')

print("✅ Model downloaded and saved to ./multilingual_model") 