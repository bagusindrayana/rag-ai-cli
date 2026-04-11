# Context API - REST API Documentation

REST API untuk context retrieval dari embedded dokumen yang didownload dari Google Drive menggunakan FAISS vector database.

## Table of Contents
- [Quick Start](#quick-start)
- [Endpoints](#endpoints)
- [Configuration](#configuration)
- [Examples](#examples)
- [Error Handling](#error-handling)

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
Buat file `.env` di root project:
```env
GOOGLE_API_KEY=your_google_api_key_here
FAISS_INDEX_PATH=./faiss_db
FAISS_INDEX_PATH_MISTRAL=./faiss_db_mistral
API_HOST=0.0.0.0
API_PORT=5000
```

### 3. Build Vector Stores (jika belum ada)
```bash
# Build Gemini FAISS index
python rag-ai.py "test query"

# atau untuk Mistral
python rag-ai-mistral.py "test query"
```

### 4. Start API Server
```bash
python context-api.py
```

Server akan berjalan di `http://localhost:5000`

---

## Endpoints

### 1. Health Check
**GET** `/health`

Check status API dan vector stores yang tersedia.

**Response:**
```json
{
  "status": "healthy",
  "vector_stores": {
    "gemini": "loaded",
    "mistral": "not_loaded"
  }
}
```

---

### 2. Get Vector Store Information
**GET** `/api/context/info`

Dapatkan informasi tentang available vector stores.

**Response:**
```json
{
  "status": "success",
  "vector_stores": [
    {
      "name": "Gemini",
      "path": "./faiss_db",
      "status": "loaded"
    },
    {
      "name": "Mistral",
      "path": "./faiss_db_mistral",
      "status": "not_found"
    }
  ]
}
```

---

### 3. Retrieve Context Documents
**POST** `/api/context/retrieve`

Retrieve dokumen relevan dari FAISS database tanpa LLM processing.

**Request Body:**
```json
{
  "query": "Apa itu machine learning?",
  "k": 5,
  "use_mistral": false
}
```

**Parameters:**
- `query` (string, required): Pertanyaan atau search query
- `k` (integer, optional): Jumlah dokumen yang diambil (default: 5)
- `use_mistral` (boolean, optional): Gunakan Mistral DB atau Gemini DB (default: false)

**Response:**
```json
{
  "status": "success",
  "query": "Apa itu machine learning?",
  "answer": null,
  "references": [
    {
      "id": 1,
      "source": "temp_drive_files/document.pdf",
      "page": 0,
      "content": "Machine learning adalah cabang dari artificial intelligence..."
    },
    {
      "id": 2,
      "source": "temp_drive_files/guide.docx",
      "page": 1,
      "content": "ML adalah teknik yang memungkinkan komputer belajar..."
    }
  ],
  "reference_count": 2,
  "use_llm": false,
  "model": "gemini"
}
```

---

### 4. Query dengan LLM Answer
**POST** `/api/context/query`

Query dokumen dan dapatkan jawaban dari LLM.

**Request Body:**
```json
{
  "query": "Bagaimana cara membuat model machine learning yang baik?",
  "k": 5,
  "use_mistral": false
}
```

**Parameters:**
- `query` (string, required): Pertanyaan
- `k` (integer, optional): Jumlah dokumen untuk context (default: 5)
- `use_mistral` (boolean, optional): Gunakan Mistral DB (default: false)

**Response:**
```json
{
  "status": "success",
  "query": "Bagaimana cara membuat model machine learning yang baik?",
  "answer": "Untuk membuat model machine learning yang baik, ada beberapa langkah penting:\n\n1. Persiapan Data yang Baik\n2. Feature Engineering...",
  "references": [
    {
      "id": 1,
      "source": "temp_drive_files/ml-guide.pdf",
      "page": 5,
      "content": "Langkah pertama dalam ML adalah mempersiapkan dataset..."
    }
  ],
  "reference_count": 1,
  "use_llm": true,
  "model": "gemini"
}
```

---

### 5. Search Documents dengan Similarity Score
**POST** `/api/context/search`

Search dokumen dengan similarity score untuk setiap hasil.

**Request Body:**
```json
{
  "query": "deep learning",
  "k": 5,
  "use_mistral": false
}
```

**Parameters:**
- `query` (string, required): Search term
- `k` (integer, optional): Jumlah hasil (default: 5)
- `use_mistral` (boolean, optional): Gunakan Mistral DB (default: false)

**Response:**
```json
{
  "status": "success",
  "query": "deep learning",
  "results": [
    {
      "id": 1,
      "score": 0.42,
      "source": "temp_drive_files/ai-fundamentals.pdf",
      "page": 12,
      "content": "Deep learning adalah subset dari machine learning yang menggunakan neural networks..."
    },
    {
      "id": 2,
      "score": 0.38,
      "source": "temp_drive_files/neural-networks.docx",
      "page": 3,
      "content": "Deep learning telah merevolusi bidang computer vision dan NLP..."
    }
  ],
  "result_count": 2,
  "model": "gemini"
}
```

---

### 6. Batch Query - Multiple Questions
**POST** `/api/context/batch`

Query multiple questions sekaligus.

**Request Body:**
```json
{
  "queries": [
    "Apa itu neural network?",
    "Apa perbedaan supervised dan unsupervised learning?",
    "Bagaimana cara training model?"
  ],
  "k": 3,
  "use_mistral": false
}
```

**Parameters:**
- `queries` (array of strings, required): List pertanyaan
- `k` (integer, optional): Dokumen per query (default: 5)
- `use_mistral` (boolean, optional): Gunakan Mistral DB (default: false)

**Response:**
```json
{
  "status": "success",
  "batch_size": 3,
  "results": [
    {
      "query": "Apa itu neural network?",
      "context": "Neural network adalah model komputasi yang terinspirasi...",
      "references": [
        {
          "id": 1,
          "source": "temp_drive_files/nn-intro.pdf",
          "page": 0,
          "content": "..."
        }
      ],
      "reference_count": 1
    },
    {
      "query": "Apa perbedaan supervised dan unsupervised learning?",
      "context": "Supervised learning adalah...",
      "references": [...],
      "reference_count": 2
    }
  ],
  "model": "gemini"
}
```

---

## Configuration

### Environment Variables (.env)

```env
# Google API Configuration
GOOGLE_API_KEY=your_google_api_key

# FAISS Database Paths
FAISS_INDEX_PATH=./faiss_db           # Gemini embeddings index
FAISS_INDEX_PATH_MISTRAL=./faiss_db_mistral  # Mistral embeddings index

# API Server Configuration
API_HOST=0.0.0.0                      # Host untuk binding (default: 0.0.0.0)
API_PORT=5000                         # Port API (default: 5000)
```

---

## Examples

### Using cURL

#### 1. Health Check
```bash
curl -X GET http://localhost:5000/health
```

#### 2. Retrieve Context
```bash
curl -X POST http://localhost:5000/api/context/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Apa itu artificial intelligence?",
    "k": 5
  }'
```

#### 3. Query dengan LLM
```bash
curl -X POST http://localhost:5000/api/context/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Jelaskan konsep neural network",
    "k": 3,
    "use_mistral": false
  }'
```

#### 4. Search dengan Scores
```bash
curl -X POST http://localhost:5000/api/context/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning applications",
    "k": 5
  }'
```

#### 5. Batch Query
```bash
curl -X POST http://localhost:5000/api/context/batch \
  -H "Content-Type: application/json" \
  -d '{
    "queries": [
      "Apa itu AI?",
      "Bagaimana cara train model?",
      "Apa itu deep learning?"
    ],
    "k": 2
  }'
```

### Using Python Requests

```python
import requests
import json

BASE_URL = "http://localhost:5000"

# 1. Health Check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# 2. Retrieve Context
payload = {
    "query": "Apa itu machine learning?",
    "k": 5
}
response = requests.post(
    f"{BASE_URL}/api/context/retrieve",
    json=payload
)
print(json.dumps(response.json(), indent=2, ensure_ascii=False))

# 3. Query dengan LLM
payload = {
    "query": "Jelaskan perbedaan AI dan machine learning",
    "k": 3
}
response = requests.post(
    f"{BASE_URL}/api/context/query",
    json=payload
)
data = response.json()
print(f"Answer: {data['answer']}")
print(f"References: {len(data['references'])} documents")

# 4. Batch Query
payload = {
    "queries": [
        "Apa itu supervised learning?",
        "Apa itu unsupervised learning?"
    ],
    "k": 2
}
response = requests.post(
    f"{BASE_URL}/api/context/batch",
    json=payload
)
results = response.json()['results']
for result in results:
    print(f"Q: {result['query']}")
    print(f"References: {result['reference_count']}\n")
```

### Using JavaScript/Node.js

```javascript
const BASE_URL = "http://localhost:5000";

// Helper function
async function apiCall(endpoint, method = "GET", data = null) {
  const options = {
    method,
    headers: { "Content-Type": "application/json" }
  };
  
  if (data) options.body = JSON.stringify(data);
  
  const response = await fetch(`${BASE_URL}${endpoint}`, options);
  return await response.json();
}

// 1. Health Check
const health = await apiCall("/health");
console.log(health);

// 2. Retrieve Context
const contextData = await apiCall("/api/context/retrieve", "POST", {
  query: "Apa itu machine learning?",
  k: 5
});
console.log(contextData);

// 3. Query dengan LLM
const queryData = await apiCall("/api/context/query", "POST", {
  query: "Jelaskan konsep deep learning",
  k: 3
});
console.log(`Answer: ${queryData.answer}`);
console.log(`References: ${queryData.references.length}`);

// 4. Batch Query
const batchData = await apiCall("/api/context/batch", "POST", {
  queries: ["Apa itu AI?", "Bagaimana cara training model?"],
  k: 2
});
console.log(batchData);
```

---

## Error Handling

API akan mengembalikan error response dengan status code yang sesuai:

### 400 - Bad Request
```json
{
  "status": "error",
  "message": "Missing 'query' field in request body"
}
```

### 404 - Not Found
```json
{
  "status": "error",
  "message": "Gemini vector store not found. Please build the index first."
}
```

### 500 - Server Error
```json
{
  "status": "error",
  "message": "Context retrieval error: [error details]"
}
```

---

## Common Issues & Solutions

### 1. Vector Store Not Found
**Problem:** Error "vector store not found"

**Solution:**
- Pastikan sudah menjalankan `rag-ai.py` atau `rag-ai-mistral.py` terlebih dahulu
- Cek path FAISS_INDEX_PATH di .env file
- Verify bahwa directory FAISS index sudah ada

### 2. Google API Key Error
**Problem:** Error "Missing Google API Key"

**Solution:**
- Set GOOGLE_API_KEY di .env file
- Atau input key saat API startup

### 3. CORS Error (Cross-Origin)
**Problem:** Request dari frontend blocked

**Solution:**
- CORS sudah enabled di API
- Pastikan frontend request dari domain yang benar

### 4. Timeout pada Large Documents
**Problem:** Response lambat atau timeout

**Solution:**
- Kurangi nilai `k` parameter (jumlah dokumen)
- Optimalkan chunk size saat building FAISS index

---

## Performance Tips

1. **Caching**: API automatically caches vector stores setelah first load
2. **Batch Processing**: Gunakan `/api/context/batch` untuk multiple queries lebih efisien
3. **Parameter Tuning**: 
   - Reduce `k` untuk response lebih cepat
   - Use appropriate chunk sizes saat building index
4. **Database Selection**: Gunakan Mistral DB jika prefer Mistral embeddings

---

## Support

Untuk lebih lanjut atau troubleshooting, check:
- Main README.md
- rag-ai.py source code
- Vector store dokumentasi (FAISS)
