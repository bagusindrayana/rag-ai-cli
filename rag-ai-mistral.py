import os
import sys
import io
import json
import getpass
import warnings
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredPowerPointLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_mistralai import ChatMistralAI
from langchain_mistralai import MistralAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import SystemMessage, HumanMessage

# Compatibility import: langchain v1.0 moved some modules to `langchain_classic`.
try:
    from langchain.chains import RetrievalQA
except Exception:
    from langchain_classic.chains import RetrievalQA

warnings.filterwarnings("ignore")

# Load environment variables dari .env file
load_dotenv()

# ================= KONFIGURASI =================
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE', 'service_account.json')
FOLDER_ID = os.getenv('FOLDER_ID', '1PrfQ-xxxxxxxxxxxxxxxxxxxxxxxxxxx')
LOCAL_TEMP_DIR = './temp_drive_files'
FAISS_INDEX_PATH = "./faiss_db_mistral"
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')

# Load Mistral API Key dari .env atau prompt user
if MISTRAL_API_KEY is None:
    os.environ["MISTRAL_API_KEY"] = getpass.getpass("Enter your Mistral API key: ")
else:
    os.environ["MISTRAL_API_KEY"] = MISTRAL_API_KEY

# ===============================================

def files_already_downloaded():
    """Cek apakah file sudah pernah didownload sebelumnya"""
    if not os.path.exists(LOCAL_TEMP_DIR):
        return False
    
    # Cek apakah ada minimal 1 file yang didukung
    for file in os.listdir(LOCAL_TEMP_DIR):
        if any(file.endswith(ext) for ext in ['.pdf', '.docx', '.pptx']):
            return True
    return False

def download_files_from_drive():
    # Skip download jika file sudah ada
    if files_already_downloaded():
        print(f"File sudah ada di {LOCAL_TEMP_DIR}. Skip download.")
        return
    
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    if not os.path.exists(LOCAL_TEMP_DIR):
        os.makedirs(LOCAL_TEMP_DIR)

    # List file dalam folder
    results = service.files().list(
        q=f"'{FOLDER_ID}' in parents and trashed = false",
        fields="files(id, name, mimeType)"
    ).execute()
    items = results.get('files', [])

    if not items:
        print("Folder kosong atau tidak ditemukan.")
        return

    print(f"Mengunduh {len(items)} file dari Google Drive...")
    for item in items:
        file_id = item['id']
        file_name = item['name']
        file_path = os.path.join(LOCAL_TEMP_DIR, file_name)

        # Skip jika file bukan dokumen yang didukung
        if not any(file_name.endswith(ext) for ext in ['.pdf', '.docx', '.pptx']):
            continue

        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(file_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        print(f"Selesai: {file_name}")

def load_documents():
    documents = []
    for file in os.listdir(LOCAL_TEMP_DIR):
        file_path = os.path.join(LOCAL_TEMP_DIR, file)
        if file.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif file.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
        elif file.endswith(".pptx"):
            loader = UnstructuredPowerPointLoader(file_path)
        else:
            continue
        documents.extend(loader.load())
    return documents

def format_output_with_references(answer: str, source_docs: list) -> str:
    """Format output sebagai JSON dengan jawaban dan referensi dari dokumen"""
    references = []
    for doc in source_docs:
        ref = {
            "source": doc.metadata.get("source", "Unknown"),
            "page": doc.metadata.get("page", 0),
            "content": doc.page_content[:500]  # Ambil 500 karakter pertama
        }
        references.append(ref)
    
    output = {
        "answer": answer,
        "references": references,
        "reference_count": len(references)
    }
    
    return json.dumps(output, indent=2, ensure_ascii=False)

SYSTEM_PROMPT = """Anda adalah asisten AI yang sangat membantu dan berpengetahuan luas.
Tugas Anda adalah menjawab pertanyaan berdasarkan dokumen yang disediakan.
Berikan jawaban yang jelas, akurat, dan relevan dengan informasi dari dokumen.
Jika informasi tidak tersedia dalam dokumen, jelaskan hal tersebut.
Selalu berikan jawaban dalam bahasa dengan pertanyaan yang diberikan."""

def main():
    if len(sys.argv) < 2:
        print('Penggunaan: python main-mistral.py "pertanyaan anda"')
        sys.exit(1)

    query = sys.argv[1]

    # 1. Sync file dari Drive
    download_files_from_drive()

    # 2. Inisialisasi Embeddings (menggunakan HuggingFace sebagai alternatif)
    # Anda bisa mengganti dengan MistralEmbeddings jika tersedia
    # embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    embeddings = MistralAIEmbeddings(
        model="mistral-embed",
    )

    # 3. Load/Create Vector Store
    if os.path.exists(FAISS_INDEX_PATH):
        vector_store = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    else:
        docs = load_documents()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        splits = text_splitter.split_documents(docs)
        vector_store = FAISS.from_documents(splits, embeddings)
        vector_store.save_local(FAISS_INDEX_PATH)

    # 4. RAG Chain dengan Mistral, System Prompt dan Output JSON
    llm = ChatMistralAI(
        model="mistral-large-latest",
        temperature=0.7,
        api_key=os.environ.get("MISTRAL_API_KEY")
    )
    retriever = vector_store.as_retriever()
    
    # Ambil dokumen relevan
    source_docs = retriever.invoke(query)
    
    # Gabungkan konteks dari dokumen
    context = "\n\n---\n\n".join([doc.page_content for doc in source_docs])
    
    # Buat prompt dengan sistem
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""Berdasarkan dokumen berikut, jawab pertanyaan ini:
        
Dokumen:
{context}

Pertanyaan: {query}""")
    ]
    
    # Dapatkan jawaban dari LLM
    response = llm.invoke(messages)
    answer = response.content
    
    # Format output sebagai JSON dengan referensi
    json_output = format_output_with_references(answer, source_docs)
    print(json_output)

if __name__ == "__main__":
    main()
