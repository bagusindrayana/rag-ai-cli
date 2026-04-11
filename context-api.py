import os
import sys
import json
import getpass
import warnings
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

# LangChain imports
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_core.messages import SystemMessage, HumanMessage

warnings.filterwarnings("ignore")

# Load environment variables
load_dotenv()

# ================= KONFIGURASI =================
FAISS_INDEX_PATH = os.getenv('FAISS_INDEX_PATH', "./faiss_db")
FAISS_INDEX_PATH_MISTRAL = os.getenv('FAISS_INDEX_PATH_MISTRAL', "./faiss_db_mistral")
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 5000))
# ===============================================

# Load Google API Key
if GOOGLE_API_KEY is None:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")
else:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# System prompt untuk context retrieval
SYSTEM_PROMPT = """Anda adalah asisten AI yang sangat membantu dan berpengetahuan luas.
Tugas Anda adalah menjawab pertanyaan berdasarkan dokumen yang disediakan.
Berikan jawaban yang jelas, akurat, dan relevan dengan informasi dari dokumen.
Jika informasi tidak tersedia dalam dokumen, jelaskan hal tersebut.
Selalu berikan jawaban dalam bahasa dengan pertanyaan yang diberikan."""

# Global variables untuk embeddings dan vector stores
embeddings = None
vector_store_gemini = None
vector_store_mistral = None


def initialize_embeddings():
    """Inisialisasi embeddings model"""
    global embeddings
    if embeddings is None:
        print("Initializing embeddings...")
        embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
    return embeddings


def load_vector_store(db_path=FAISS_INDEX_PATH):
    """Load vector store dari FAISS index"""
    if not os.path.exists(db_path):
        return None
    
    embeddings = initialize_embeddings()
    try:
        vector_store = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
        return vector_store
    except Exception as e:
        print(f"Error loading vector store from {db_path}: {str(e)}")
        return None


def get_vector_store(use_mistral=False):
    """Get vector store (cache result)"""
    global vector_store_gemini, vector_store_mistral
    
    if use_mistral:
        if vector_store_mistral is None:
            vector_store_mistral = load_vector_store(FAISS_INDEX_PATH_MISTRAL)
        return vector_store_mistral
    else:
        if vector_store_gemini is None:
            vector_store_gemini = load_vector_store(FAISS_INDEX_PATH)
        return vector_store_gemini


def format_context_response(answer, source_docs, query, use_llm=False):
    """Format response dengan konteks dan referensi"""
    references = []
    for idx, doc in enumerate(source_docs, 1):
        ref = {
            "id": idx,
            "source": doc.metadata.get("source", "Unknown"),
            "page": doc.metadata.get("page", 0),
            "content": doc.page_content[:300]  # First 300 chars
        }
        references.append(ref)
    
    response = {
        "status": "success",
        "query": query,
        "answer": answer if use_llm else None,
        "references": references,
        "reference_count": len(references),
        "use_llm": use_llm
    }
    
    return response


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    gemini_status = "loaded" if vector_store_gemini is not None else "not_loaded"
    mistral_status = "loaded" if vector_store_mistral is not None else "not_loaded"
    
    return jsonify({
        "status": "healthy",
        "vector_stores": {
            "gemini": gemini_status,
            "mistral": mistral_status
        }
    }), 200


@app.route('/api/context/retrieve', methods=['POST'])
def retrieve_context():
    """
    Retrieve context dari FAISS database
    
    Request body:
    {
        "query": "your question",
        "k": 5,  # number of documents to retrieve (optional, default: 5)
        "use_mistral": false  # use mistral index (optional, default: false)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing 'query' field in request body"
            }), 400
        
        query = data.get('query', '').strip()
        k = int(data.get('k', 5))
        use_mistral = data.get('use_mistral', False)
        
        if not query:
            return jsonify({
                "status": "error",
                "message": "Query cannot be empty"
            }), 400
        
        # Get vector store
        vector_store = get_vector_store(use_mistral)
        if vector_store is None:
            db_name = "Mistral" if use_mistral else "Gemini"
            return jsonify({
                "status": "error",
                "message": f"{db_name} vector store not found. Please build the index first."
            }), 404
        
        # Retrieve relevant documents
        retriever = vector_store.as_retriever(search_kwargs={"k": k})
        source_docs = retriever.invoke(query)
        
        # Format context from documents
        context = "\n\n---\n\n".join([doc.page_content for doc in source_docs])
        
        response = format_context_response(context, source_docs, query, use_llm=False)
        response["model"] = "mistral" if use_mistral else "gemini"
        
        return jsonify(response), 200
    
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid parameter: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Context retrieval error: {str(e)}"
        }), 500


@app.route('/api/context/query', methods=['POST'])
def query_with_llm():
    """
    Query dengan LLM untuk mendapatkan jawaban
    
    Request body:
    {
        "query": "your question",
        "k": 5,  # number of documents to retrieve (optional, default: 5)
        "use_mistral": false  # use mistral index (optional, default: false)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing 'query' field in request body"
            }), 400
        
        query = data.get('query', '').strip()
        k = int(data.get('k', 5))
        use_mistral = data.get('use_mistral', False)
        
        if not query:
            return jsonify({
                "status": "error",
                "message": "Query cannot be empty"
            }), 400
        
        # Get vector store
        vector_store = get_vector_store(use_mistral)
        if vector_store is None:
            db_name = "Mistral" if use_mistral else "Gemini"
            return jsonify({
                "status": "error",
                "message": f"{db_name} vector store not found. Please build the index first."
            }), 404
        
        # Retrieve relevant documents
        retriever = vector_store.as_retriever(search_kwargs={"k": k})
        source_docs = retriever.invoke(query)
        
        # Combine context
        context = "\n\n---\n\n".join([doc.page_content for doc in source_docs])
        
        # Create prompt with system message
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"""Berdasarkan dokumen berikut, jawab pertanyaan ini:
        
Dokumen:
{context}

Pertanyaan: {query}""")
        ]
        
        # Get answer from LLM
        response_llm = llm.invoke(messages)
        answer = response_llm.content
        
        response = format_context_response(answer, source_docs, query, use_llm=True)
        response["model"] = "mistral" if use_mistral else "gemini"
        
        return jsonify(response), 200
    
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid parameter: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Query error: {str(e)}"
        }), 500


@app.route('/api/context/search', methods=['POST'])
def search_documents():
    """
    Search documents dengan similarity score
    
    Request body:
    {
        "query": "search term",
        "k": 5,
        "use_mistral": false
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing 'query' field in request body"
            }), 400
        
        query = data.get('query', '').strip()
        k = int(data.get('k', 5))
        use_mistral = data.get('use_mistral', False)
        
        if not query:
            return jsonify({
                "status": "error",
                "message": "Query cannot be empty"
            }), 400
        
        # Get vector store
        vector_store = get_vector_store(use_mistral)
        if vector_store is None:
            db_name = "Mistral" if use_mistral else "Gemini"
            return jsonify({
                "status": "error",
                "message": f"{db_name} vector store not found."
            }), 404
        
        # Search with scores
        search_results = vector_store.similarity_search_with_score(query, k=k)
        
        results = []
        for idx, (doc, score) in enumerate(search_results, 1):
            result = {
                "id": idx,
                "score": float(score),
                "source": doc.metadata.get("source", "Unknown"),
                "page": doc.metadata.get("page", 0),
                "content": doc.page_content[:500]
            }
            results.append(result)
        
        response = {
            "status": "success",
            "query": query,
            "results": results,
            "result_count": len(results),
            "model": "mistral" if use_mistral else "gemini"
        }
        
        return jsonify(response), 200
    
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid parameter: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Search error: {str(e)}"
        }), 500


@app.route('/api/context/batch', methods=['POST'])
def batch_query():
    """
    Batch query multiple questions
    
    Request body:
    {
        "queries": ["question 1", "question 2"],
        "k": 5,
        "use_mistral": false
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'queries' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing 'queries' field in request body"
            }), 400
        
        queries = data.get('queries', [])
        if not isinstance(queries, list) or len(queries) == 0:
            return jsonify({
                "status": "error",
                "message": "queries must be a non-empty list"
            }), 400
        
        k = int(data.get('k', 5))
        use_mistral = data.get('use_mistral', False)
        
        # Get vector store
        vector_store = get_vector_store(use_mistral)
        if vector_store is None:
            db_name = "Mistral" if use_mistral else "Gemini"
            return jsonify({
                "status": "error",
                "message": f"{db_name} vector store not found."
            }), 404
        
        # Process each query
        results = []
        retriever = vector_store.as_retriever(search_kwargs={"k": k})
        
        for query in queries:
            query = query.strip()
            if not query:
                continue
            
            source_docs = retriever.invoke(query)
            context = "\n\n---\n\n".join([doc.page_content for doc in source_docs])
            
            references = []
            for idx, doc in enumerate(source_docs, 1):
                ref = {
                    "id": idx,
                    "source": doc.metadata.get("source", "Unknown"),
                    "page": doc.metadata.get("page", 0),
                    "content": doc.page_content[:300]
                }
                references.append(ref)
            
            result = {
                "query": query,
                "context": context,
                "references": references,
                "reference_count": len(references)
            }
            results.append(result)
        
        response = {
            "status": "success",
            "batch_size": len(results),
            "results": results,
            "model": "mistral" if use_mistral else "gemini"
        }
        
        return jsonify(response), 200
    
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid parameter: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Batch query error: {str(e)}"
        }), 500


@app.route('/api/context/info', methods=['GET'])
def get_info():
    """Get information tentang available vector stores"""
    info = {
        "status": "success",
        "vector_stores": []
    }
    
    # Check Gemini store
    gemini_store = get_vector_store(use_mistral=False)
    if gemini_store:
        info["vector_stores"].append({
            "name": "Gemini",
            "path": FAISS_INDEX_PATH,
            "status": "loaded"
        })
    else:
        info["vector_stores"].append({
            "name": "Gemini",
            "path": FAISS_INDEX_PATH,
            "status": "not_found"
        })
    
    # Check Mistral store
    mistral_store = get_vector_store(use_mistral=True)
    if mistral_store:
        info["vector_stores"].append({
            "name": "Mistral",
            "path": FAISS_INDEX_PATH_MISTRAL,
            "status": "loaded"
        })
    else:
        info["vector_stores"].append({
            "name": "Mistral",
            "path": FAISS_INDEX_PATH_MISTRAL,
            "status": "not_found"
        })
    
    return jsonify(info), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500


if __name__ == '__main__':
    print(f"Starting Context API Server on {API_HOST}:{API_PORT}...")
    print(f"Gemini FAISS DB: {FAISS_INDEX_PATH}")
    print(f"Mistral FAISS DB: {FAISS_INDEX_PATH_MISTRAL}")
    print("\nAvailable endpoints:")
    print("  GET  /health - Health check")
    print("  GET  /api/context/info - Get available vector stores")
    print("  POST /api/context/retrieve - Retrieve context documents")
    print("  POST /api/context/query - Query with LLM answer")
    print("  POST /api/context/search - Search documents with similarity scores")
    print("  POST /api/context/batch - Batch query multiple questions")
    
    app.run(host=API_HOST, port=API_PORT, debug=False)
