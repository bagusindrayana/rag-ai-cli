# RAG AI CLI - Document Context Retrieval API

REST API untuk **Retrieval-Augmented Generation (RAG)** dari embedded dokumen yang didownload dari **Google Drive** menggunakan **FAISS vector database**.

## 📝 Deskripsi Singkat

**RAG AI CLI** adalah sistem yang memungkinkan Anda untuk:
- 📂 **Download dokumen** dari Google Drive secara otomatis
- 🔍 **Embed dokumen** menggunakan Google Generative AI atau Mistral AI
- 💾 **Simpan embeddings** di FAISS vector database untuk pencarian cepat
- 🚀 **Retrieve context** dari dokumen via REST API
- 🤖 **Generate answers** berdasarkan context dari LLM

Sempurna untuk membangun chatbot, Q&A system, atau search engine berbasis dokumen.

## 🎯 Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| **Google Drive Integration** | Auto-sync dokumen PDF, DOCX, PPTX dari folder Google Drive |
| **Multi-LLM Support** | Gemini 2.5 Flash & Mistral AI untuk embeddings & generation |
| **FAISS Vector DB** | Lightning-fast similarity search di millions of documents |
| **REST API** | 6 endpoints untuk context retrieval, search, batch processing |
| **Production Ready** | Gunicorn + Systemd + Nginx untuk deployment enterprise |
| **CLI Tools** | Command-line interface untuk training & testing |

## 🏗️ Arsitektur

```
User Applications
       ↓
REST API (Flask) - /api/context/*
       ↓
Vector Store (FAISS) - Similarity Search
       ↓
Embedded Documents
       ↓
Google Drive (Source)
```

## 📦 Komponen Utama

### 1. **rag-ai.py** - Gemini Embeddings Pipeline
Membangun vector database dengan Google Generative AI embeddings:
```bash
python rag-ai.py "your question"
# Downloads dokumen → Embeds → Builds FAISS index
```

### 2. **rag-ai-mistral.py** - Mistral Embeddings Pipeline
Alternatif dengan Mistral AI embeddings:
```bash
python rag-ai-mistral.py "your question"
```

### 3. **context-api.py** - REST API Server
Production-ready API server untuk context retrieval:
```bash
python context-api.py
# API berjalan di http://localhost:5000
```

### 4. **context-api-client.py** - Python Client
Interactive CLI client & library untuk testing:
```bash
# Interactive mode
python context-api-client.py -i

# Run examples
python context-api-client.py
```

## 🚀 Quick Start (5 Menit)

### 1. Setup Environment
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env dengan GOOGLE_API_KEY Anda
```

### 2. Build Vector Database
```bash
# Build Gemini index
python rag-ai.py "setup test"
```

### 3. Start API Server
```bash
python context-api.py
# Server running at http://localhost:5000
```

### 4. Test API
```bash
# Health check
curl http://localhost:5000/health

# Query dengan LLM answer
curl -X POST http://localhost:5000/api/context/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Your question", "k": 5}'
```

## 📚 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| GET | `/api/context/info` | Available vector stores |
| POST | `/api/context/retrieve` | Get context documents |
| POST | `/api/context/query` | Get LLM answer with context |
| POST | `/api/context/search` | Search with similarity scores |
| POST | `/api/context/batch` | Batch process multiple queries |

Lihat [API_DOCUMENTATION.md](API_DOCUMENTATION.md) untuk detail lengkap.

## 🛠️ Project Structure

```
rag-ai-cli/
├── context-api.py                 # REST API Server
├── context-api-client.py          # Client & Interactive CLI
├── rag-ai.py                      # Gemini embeddings pipeline
├── rag-ai-mistral.py              # Mistral embeddings pipeline
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
│
├── 📚 Documentation
│   ├── README.md                  # This file
│   ├── QUICKSTART.md              # Setup guide
│   ├── API_DOCUMENTATION.md       # REST API reference
│   ├── DEPLOYMENT.md              # Production deployment
│   ├── DEPLOYMENT_GUIDE_ID.md     # Indonesian deployment guide
│   ├── DEPLOYMENT_FILES_SUMMARY.md # Deployment files overview
│   └── QUICK_REFERENCE.md         # One-page cheat sheet
│
├── 🚀 Deployment Scripts
│   ├── deploy.sh                  # Automated deployment
│   ├── troubleshoot.sh            # Diagnostics & fixing
│   └── nginx.conf.example         # Nginx reverse proxy
│
├── 📁 Generated (runtime)
│   ├── faiss_db/                  # Gemini FAISS index
│   ├── faiss_db_mistral/          # Mistral FAISS index
│   └── temp_drive_files/          # Downloaded documents
```

## 📖 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Setup & test dalam 10 menit
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - REST API reference lengkap
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment dengan Gunicorn + Systemd + Nginx
- **[DEPLOYMENT_GUIDE_ID.md](DEPLOYMENT_GUIDE_ID.md)** - Deployment guide Bahasa Indonesia
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - One-page cheat sheet

## 💡 Use Cases

### 1. **Corporate Document Search**
```bash
# Upload corporate documents ke Google Drive
# System akan auto-index dan provide search
# Users bisa query via API
```

### 2. **Customer Support Chatbot**
```bash
# Integrate API dengan chatbot frontend
# Chatbot retrieve context dari knowledge base
# Provide AI-generated answers
```

### 3. **Research Assistant**
```bash
# Index research papers
# Query untuk mendapat relevant papers + AI summary
```

### 4. **Product Documentation Search**
```bash
# Index product docs, API docs, guides
# Users bisa search & get instant answers
```

## 🔧 Technology Stack

| Component | Technology |
|-----------|------------|
| **LLM & Embeddings** | Google Generative AI, Mistral AI |
| **Vector Database** | FAISS (Facebook AI Similarity Search) |
| **Document Processing** | LangChain |
| **Web Framework** | Flask |
| **Application Server** | Gunicorn |
| **Service Manager** | Systemd |
| **Reverse Proxy** | Nginx |
| **Language** | Python 3.8+ |

## 📋 Requirements

- Python 3.8+
- pip atau conda
- Google Generative AI API Key (gratis di makersuite.google.com)
- Google Drive (untuk dokumen)
- Linux server (untuk production deployment)

## 🔐 Environment Variables

```env
# Required
GOOGLE_API_KEY=your_api_key_here

# Paths (optional, defaults provided)
FAISS_INDEX_PATH=./faiss_db
FAISS_INDEX_PATH_MISTRAL=./faiss_db_mistral

# Server (optional for API)
API_HOST=0.0.0.0
API_PORT=5000
```

## 🚢 Production Deployment

Deploy ke Linux server dengan Gunicorn + Systemd:

### Automated (5-10 menit)
```bash
sudo bash deploy.sh
```

### Atau ikuti [DEPLOYMENT_GUIDE_ID.md](DEPLOYMENT_GUIDE_ID.md)

Features:
- ✅ Auto-start on boot
- ✅ Auto-restart on crash
- ✅ SSL/TLS support
- ✅ Rate limiting
- ✅ Health monitoring
- ✅ Centralized logging

## 🧪 Testing

### Development
```bash
python context-api-client.py -i    # Interactive mode
python context-api-client.py       # Run examples
```

### Production
```bash
sudo bash troubleshoot.sh full      # Full diagnostics
curl https://your-domain.com/health # Health check
```

## 🐛 Troubleshooting

### API mau start tapi error?
```bash
# Check logs
sudo journalctl -u contextapi.service -f

# Full diagnostics
sudo bash troubleshoot.sh full
```

### FAISS index tidak ditemukan?
```bash
# Build index
python rag-ai.py "test query"

# Verify
ls -la faiss_db/
```

### Google API Key error?
```bash
# Check environment
cat .env

# Update jika perlu
nano .env
```

Lihat [DEPLOYMENT_GUIDE_ID.md](DEPLOYMENT_GUIDE_ID.md) untuk troubleshooting lengkap.

## 📞 Support & Help

1. **Quick Start**: Baca [QUICKSTART.md](QUICKSTART.md)
2. **API Usage**: Baca [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
3. **Deployment**: Baca [DEPLOYMENT_GUIDE_ID.md](DEPLOYMENT_GUIDE_ID.md)
4. **Issues**: Jalankan `sudo bash troubleshoot.sh full`
5. **Examples**: Jalankan `python context-api-client.py`

## 📈 Performance

- **Query latency**: <500ms untuk dokumen 1000+ dengan FAISS
- **Concurrent requests**: 50+ dengan default Gunicorn config
- **Memory usage**: ~2GB untuk 10K+ documents
- **Storage**: FAISS index ~100MB per 10K documents

## 🔄 Update & Maintenance

```bash
# Update code
git pull

# Update dependencies
pip install -r requirements.txt

# Rebuild FAISS (jika dokumen berubah)
python rag-ai.py "update"

# Restart service
sudo systemctl restart contextapi
```

## 📝 License

Open source - feel free to use dan modify!

## 🎉 Acknowledgments

Terima kasih kepada:
- Google Generative AI untuk LLM & embeddings
- Facebook AI untuk FAISS
- LangChain untuk document processing
- Flask & Gunicorn community

---

**Made with ❤️ for RAG enthusiasts**

**Quick Links**: 
[🚀 Quick Start](QUICKSTART.md) • 
[📚 API Docs](API_DOCUMENTATION.md) • 
[🛠️ Deploy](DEPLOYMENT_GUIDE_ID.md) • 
[📞 Troubleshoot](troubleshoot.sh)
