import os
import re
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv("keys.env")
AZURE_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_KEY")

# Azure Search setup
INDEX_NAME = "docs-index"
search_client = SearchClient(endpoint=AZURE_ENDPOINT,
                             index_name=INDEX_NAME,
                             credential=AzureKeyCredential(AZURE_API_KEY))

# File and model setup
folder_path = r"C:\Users\bhavy\RAG Prototype Azure\files"
model = SentenceTransformer("all-MiniLM-L6-v2")

# Text splitting config
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", ", ", " "]
)

# Sanitize ID
def sanitize_id(text):
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', text)

# Upload loop
for filename in os.listdir(folder_path):
    if not filename.endswith(".pdf"):
        continue

    print(f"\nProcessing: {filename}")
    file_path = os.path.join(folder_path, filename)
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    chunks = text_splitter.split_documents(pages)

    base_name = os.path.splitext(filename)[0]

    for i, chunk in enumerate(chunks):
        content = chunk.page_content
        embedding = model.encode(content).tolist()

        safe_id = sanitize_id(f"{filename}_chunk{i}")

        doc = {
            "id": safe_id,
            "content": content,
            "contentVector": embedding,
            "source": filename,
            "companyName": base_name,
            "sector": "unknown"  # can be extracted later from context if needed
        }

        try:
            search_client.upload_documents(documents=[doc])
            print(f"✓ Uploaded: {doc['id']}")
        except Exception as e:
            print(f"✗ Error uploading {doc['id']}: {e}")

print("\n✅ All documents uploaded to Azure Cognitive Search.")
