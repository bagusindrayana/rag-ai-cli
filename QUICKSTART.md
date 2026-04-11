# Context API - Quick Start Guide

## 📋 Prerequisites

- Python 3.8+
- pip atau conda
- Google API Key (untuk Generative AI)
- Google Drive documents untuk RAG (optional)

## 🚀 Quick Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Buat file `.env` di project root:

```bash
# Copy dari template
cp .env.example .env
```

Edit `.env` dan tambahkan:
```env
GOOGLE_API_KEY=your_api_key_here
FAISS_INDEX_PATH=./faiss_db
FAISS_INDEX_PATH_MISTRAL=./faiss_db_mistral
API_HOST=0.0.0.0
API_PORT=5000
```

### Step 3: Build FAISS Index (First Time)
```bash
# Build menggunakan Gemini embeddings
python rag-ai.py "test query"

# atau gunakan Mistral embeddings
python rag-ai-mistral.py "test query"
```

Index akan tersimpan di folder `faiss_db/` atau `faiss_db_mistral/`

### Step 4: Start API Server
```bash
python context-api.py
```

Output:
```
Starting Context API Server on 0.0.0.0:5000...
Gemini FAISS DB: ./faiss_db
Mistral FAISS DB: ./faiss_db_mistral

Available endpoints:
  GET  /health - Health check
  GET  /api/context/info - Get available vector stores
  POST /api/context/retrieve - Retrieve context documents
  POST /api/context/query - Query with LLM answer
  POST /api/context/search - Search documents with similarity scores
  POST /api/context/batch - Batch query multiple questions
```

API sekarang berjalan di: `http://localhost:5000`

## 🧪 Test API

### Option 1: Using cURL
```bash
# Health check
curl -X GET http://localhost:5000/health

# Query dengan context retrieval
curl -X POST http://localhost:5000/api/context/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "Apa itu machine learning?", "k": 3}'
```

### Option 2: Using Python Client
```bash
# Run dengan auto examples
python context-api-client.py

# Interactive mode
python context-api-client.py -i
```

### Option 3: Using Python Requests
```python
import requests

response = requests.post(
    "http://localhost:5000/api/context/query",
    json={
        "query": "Apa itu neural network?",
        "k": 3
    }
)
print(response.json())
```

## 📚 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Check API health |
| GET | `/api/context/info` | Get vector store info |
| POST | `/api/context/retrieve` | Get context documents |
| POST | `/api/context/query` | Get answes with context |
| POST | `/api/context/search` | Search with scores |
| POST | `/api/context/batch` | Batch process queries |

Lihat `API_DOCUMENTATION.md` untuk detail lengkap.

## 🔍 Project Structure

```
rag-ai-cli/
├── context-api.py              # Main REST API server
├── context-api-client.py       # Client examples & interactive CLI
├── rag-ai.py                   # Gemini embeddings RAG
├── rag-ai-mistral.py           # Mistral embeddings RAG
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
├── API_DOCUMENTATION.md       # Detailed API docs
├── QUICKSTART.md             # This file
├── faiss_db/                  # Gemini FAISS index (generated)
├── faiss_db_mistral/          # Mistral FAISS index (generated)
└── temp_drive_files/          # Downloaded documents (generated)
```

## 💡 Common Use Cases

### 1. Simple Document Retrieval
```python
import requests

response = requests.post(
    "http://localhost:5000/api/context/retrieve",
    json={"query": "Your question", "k": 5}
)
for ref in response.json()["references"]:
    print(f"{ref['source']}: {ref['content'][:100]}")
```

### 2. Get LLM-Generated Answer
```python
response = requests.post(
    "http://localhost:5000/api/context/query",
    json={"query": "Your question"}
)
data = response.json()
print(data["answer"])  # LLM-generated answer
```

### 3. Batch Processing
```python
response = requests.post(
    "http://localhost:5000/api/context/batch",
    json={
        "queries": ["Q1", "Q2", "Q3"],
        "k": 3
    }
)
for result in response.json()["results"]:
    print(f"Q: {result['query']}, Refs: {result['reference_count']}")
```

### 4. Document Search with Similarity Scores
```python
response = requests.post(
    "http://localhost:5000/api/context/search",
    json={"query": "search term", "k": 5}
)
for result in response.json()["results"]:
    print(f"Score: {result['score']:.2f} - {result['source']}")
```

## ⚙️ Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | - | Required: Google Generative AI key |
| `FAISS_INDEX_PATH` | `./faiss_db` | Gemini FAISS index path |
| `FAISS_INDEX_PATH_MISTRAL` | `./faiss_db_mistral` | Mistral FAISS index path |
| `API_HOST` | `0.0.0.0` | API bind address |
| `API_PORT` | `5000` | API port |

### Query Parameters

Setiap endpoint menerima:
- `query` (required): Search/query text
- `k` (optional, default: 5): Number of documents
- `use_mistral` (optional, default: false): Use Mistral DB

## 🐛 Troubleshooting

### "Vector store not found"
- Jalankan `rag-ai.py` untuk build index terlebih dahulu
- Pastikan path di `.env` benar

### "Cannot connect to API"
- Pastikan API server sudah start
- Check port tidak digunakan aplikasi lain

### "Google API Key error"
- Set GOOGLE_API_KEY di `.env`
- atau input saat startup

### Response timeout
- Reduce `k` parameter
- Check dokumen size

## 📖 More Documentation

- **Full API Documentation**: See `API_DOCUMENTATION.md`
- **Examples**: Run `python context-api-client.py`
- **Interactive CLI**: Run `python context-api-client.py -i`

## 🔐 Security Notes

- Jangan share `GOOGLE_API_KEY` public
- Store credentials di `.env` (tidak di git)
- API running di localhost by default untuk development
- Production: implementasi authentication

## 📝 Next Steps

1. ✅ Setup environment & install dependencies
2. ✅ Build FAISS index dari documents
3. ✅ Start API server
4. ✅ Test endpoints dengan client
5. ✅ Integrate ke aplikasi Anda

Selamat! API Anda sudah siap 🎉
