# LLM-Based Manufacturing Knowledge Assistant

A Retrieval-Augmented Generation (RAG) system designed for knowledge retrieval and question answering from manufacturing Work Instructions (WI) and Standard Operating Procedures (SOP).

The project explores how LLM-based applications can support manufacturing engineers by retrieving relevant procedural information, reconstructing process context, and generating grounded answers from technical documentation.

## Key Features

- Manufacturing WI/SOP document ingestion and preprocessing
- Domain-aware and semantic document chunking
- Sentence Transformer-based embeddings
- Qdrant vector database integration
- Hybrid vector and keyword retrieval
- Query rewriting and routing
- Cross-Encoder reranking
- Context reconstruction for procedural documents
- LLM-based grounded answer generation
- Custom RAG evaluation for retrieval and response quality

## Architecture

```text
Manufacturing WI / SOP
        │
        ▼
Document Parsing & Cleaning
        │
        ▼
Domain-Aware / Semantic Chunking
        │
        ▼
Sentence Transformer Embeddings
        │
        ▼
Qdrant Vector Database
        │
        ▼
Query Rewriting & Routing
        │
        ▼
Hybrid Retrieval
(Vector Search + Keyword Search)
        │
        ▼
Cross-Encoder Reranking
        │
        ▼
Context Reconstruction
        │
        ▼
LLM Generation
        │
        ▼
Grounded Answer + Sources
        │
        ▼
RAG Evaluation
```

## RAG Evaluation

The project includes a custom evaluation module for manufacturing procedural knowledge.

Current evaluation metrics include:

- **Context Recall** — measures whether retrieved contexts cover expected SOP steps
- **Answer Relevancy** — measures semantic similarity between the user question and generated answer
- **Faithfulness** — estimates whether answer statements are semantically supported by retrieved contexts
- **Completeness** — evaluates coverage of expected procedural steps

Semantic evaluation is implemented using Sentence Transformer embeddings and cosine similarity.

> The current context recall and completeness metrics are domain-specific and designed around structured manufacturing SOP workflows.

## Tech Stack

**Language**
- Python

**LLM / RAG**
- Large Language Models
- Retrieval-Augmented Generation (RAG)
- Sentence Transformers
- Cross-Encoder Reranking
- Semantic Retrieval

**Database**
- Qdrant Vector Database

**Backend / Integration**
- FastAPI
- OpenAI-compatible LLM API

**Document Processing**
- Unstructured
- PyPDF
- python-docx

## Project Structure

```text
llm-manufacturing-assistant/
├── core/
│   ├── evaluation/
│   ├── ingest/
│   ├── llm/
│   ├── pipeline/
│   ├── reconstruction/
│   ├── rerank/
│   ├── retrieval/
│   ├── router/
│   └── utils/
├── loaders/
├── templates/
├── tests/
├── app.py
├── ingest.py
├── main.py
├── settings.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd llm-manufacturing-assistant
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a local `.env` file based on your environment configuration.

Example:

```env
LLM_API_KEY=your_api_key
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
```

Do not commit API keys or credentials to the repository.

## Motivation

Manufacturing knowledge is often distributed across large numbers of technical documents, work instructions, and SOPs.

Traditional keyword search may struggle with procedural questions that require information from multiple sections of a document.

This project investigates how RAG, semantic retrieval, reranking, and LLM-based generation can be combined to provide more context-aware access to manufacturing knowledge.

## Future Improvements

- Generalize evaluation metrics across different SOP structures
- Add systematic retrieval benchmark datasets
- Improve automated RAG evaluation
- Expand support for tables and multimodal manufacturing documents
- Explore Vision-Language Models (VLM) for diagrams and visual work instructions
