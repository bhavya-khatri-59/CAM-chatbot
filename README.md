# 🤖 CAM Chatbot (LLM‑RAG for Credit Appraisal)

A Retrieval-Augmented Generation (RAG) chatbot built to assist credit teams in querying Credit Appraisal Memoranda (CAM) documents. The system intelligently retrieves relevant chunks from internal PDFs and uses **Gemini 2.5 Pro** to generate grounded, structured answers.

---

## 📌 Overview

This chatbot serves as an AI assistant for internal credit analysts. Given a query, it:

1. Identifies relevant companies using an LLM (Gemini).
2. Filters and performs a hybrid search (semantic + vector) on preprocessed CAM documents.
3. Passes context back to Gemini 2.5 Pro for response generation.
4. Returns structured, citation-grounded answers.

---

## 🧠 System Architecture (Mermaid.js)

```mermaid
flowchart TD
  A[User enters query] --> B[Gemini 2.5 Pro<br/>identifies relevant companies]
  B --> C[Trigger Hybrid Search<br/>(Azure Cognitive Search)]
  C --> D1[Semantic Search (BM25)]
  C --> D2[Vector Search (HNSW using SentenceTransformer)]
  D1 --> E[Relevant chunks retrieved]
  D2 --> E
  E --> F[Assemble context]
  F --> G[Gemini 2.5 Pro<br/>generates grounded response]
  G --> H[Return answer to React Frontend]

🛠 Tech Stack
| Layer               | Technology                                      |
| ------------------- | ----------------------------------------------- |
| Backend API         | FastAPI                                         |
| LLM                 | Gemini 2.5 Pro (1M token context)               |
| Embedding Model     | SentenceTransformer (all-MiniLM-L6-v2)          |
| Search Engine       | Azure Cognitive Search (Hybrid: BM25 + HNSW)    |
| Document Processing | LangChain (PDF chunking + metadata)             |
| Frontend            | React                                           |
| Deployment Ready    | Azure AD, Microsoft Teams integration (planned) |

⚙️ RAG Pipeline Details
🔍 Step 1: Query Understanding via LLM
Gemini 2.5 Pro is prompted with the user's query.

Identifies 1 or more relevant companies from a list of ~10,000 known entities.

🔎 Step 2: Hybrid Search on Azure Cognitive Search
Semantic Search using BM25 (keyword-based relevance).

Vector Search using HNSW (approx. nearest neighbor search on dense vectors).

Both scores are fused to retrieve the most relevant document chunks.

🧩 Step 3: Document Ingestion & Indexing
PDFs chunked using LangChain, preserving semantic structure.

Each chunk is embedded via all-MiniLM-L6-v2.

Indexed in Azure with metadata:

companyName

source

sector

pageNumber

🧠 Step 4: Context Assembly & Prompting
Retrieved chunks are dynamically selected based on:

Number of companies identified

Query length and specificity

Context is constructed with citations and metadata.

🗣 Step 5: Response Generation via Gemini
Gemini receives a carefully designed prompt with retrieved context.

Generates a structured and grounded answer.

No hallucination: responses strictly cite indexed chunks.

🧪 Performance Optimizations
Chunk Retrieval Tuning: Trade-off between context quality and latency.

Dynamic Context Scaling: Adjusts number of chunks based on query complexity.

Prompt Engineering: Designed to enforce factuality, avoid hallucinations.

Company Matching: Gemini performs fuzzy entity matching internally.

🌐 Frontend Overview

Built with React.

Provides a minimal, clean chatbot interface.

Sends user queries to the FastAPI backend.

Displays LLM-generated responses along with any relevant citations.

🔒 Security & Deployment Plans

Integrate with Azure Active Directory (AAD) for access control.

Embed in Microsoft Teams as a chatbot tool.

Potential expansion to role-based filtering on document access.