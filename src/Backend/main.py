from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import re
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# Load env variables
load_dotenv("keys.env")
AZURE_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_KEY = os.getenv("AZURE_KEY")
GEMINI_KEY = os.getenv("GEMINI_KEY")
AZURE_INDEX = "docs-index"
FILE_DIR = r"C:\\Users\\bhavy\\RAG Prototype 3\\rag-app-3\\src\\Backend\\files"

# Init services
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
search_client = SearchClient(endpoint=AZURE_ENDPOINT, index_name=AZURE_INDEX, credential=AzureKeyCredential(AZURE_KEY))

# Load known sources
known_sources = [f for f in os.listdir(FILE_DIR) if f.endswith(".pdf")]

# Define query model
class QueryRequest(BaseModel):
    query: str

def get_relevant_sources_from_llm(query, known_sources):
    joined_sources = "\n".join(known_sources)
    prompt = f"""
Given the following document titles:

{joined_sources}

Which ones are relevant to the question:
"{query}"

Return exact matches from the list above (case-sensitive).
If all are relevant, return "ALL".
If none are relevant, return "NONE".
"""
    try:
        response = model.generate_content(prompt)
        answer = response.text.strip().splitlines()
        if any("ALL" in line.upper() for line in answer):
            return known_sources
        if any("NONE" in line.upper() for line in answer):
            return []
        return [line.strip() for line in answer if line.strip() in known_sources]
    except Exception as e:
        print("LLM Routing Failed:", e)
        return []

# FastAPI setup
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ask")
def ask_query(payload: QueryRequest):
    query = payload.query
    matched_sources = get_relevant_sources_from_llm(query, known_sources)
    print("Matched sources:", matched_sources)

    if matched_sources:
        azure_filter = " or ".join([f"(source eq '{s}')" for s in matched_sources])
    else:
        azure_filter = None

    print("Azure filter:", azure_filter)

    # Scale top_k by document count
    num_docs = len(matched_sources) if matched_sources else len(known_sources)
    top_k = min(200, max(40, num_docs * 5))

    # Text search
    text_results = search_client.search(
        search_text=query,
        top=top_k,
        query_type="semantic",
        semantic_configuration_name="semantic-config",
        filter=azure_filter
    )

    # Vector search
    embedding = embedder.encode(query).tolist()
    vector_results = search_client.search(
        search_text=None,
        vector_queries=[
            VectorizedQuery(
                vector=embedding,
                k_nearest_neighbors=top_k,
                fields="contentVector"
            )
        ],
        top=top_k,
        filter=azure_filter
    )

    context_chunks = []
    for r in list(text_results) + list(vector_results):
        d = dict(r)
        context_chunks.append(
            f"SOURCE: {d.get('source', 'Unknown')} (Page {d.get('page', 'N/A')})\n{d.get('content', '')}"
        )

    context = "\n\n".join(context_chunks)[:120000]

    prompt = f"""You are an AI credit appraisal assistant working for Samunnati Financial Intermediation & Services Pvt. Ltd.. You MUST answer ONLY based on the following context.

Context:
{context}

Question: {query}

Instructions:
- If the answer is not in the context, respond with \"The information is not available in the provided documents.\"
- Do not make up any information.
- Respond in clear and structured bullet points or paragraphs.

Answer:
"""

    gemini_response = model.generate_content(prompt)
    answer = gemini_response.text.strip()
    return {"answer": answer}
