import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
# Import document loaders for different file types
from langchain_community.document_loaders import PyPDFLoader, TextLoader

# --- Configuration ---
DOCS_DIR = "medical_docs"
VECTOR_STORE_DIR = "vector_store"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 70

def load_documents(directory_path):
    """
    Loads documents from the specified directory, handling .pdf and .txt files.
    """
    documents = []
    print(f"Loading documents from {directory_path}...")
    
    if not os.path.exists(directory_path):
        print(f"Directory {directory_path} does not exist. Creating it...")
        os.makedirs(directory_path)
        print(f"Please add your medical documents to {directory_path} and run again.")
        return documents
    
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        
        # Skip directories
        if os.path.isdir(file_path):
            continue
            
        try:
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
                print(f" - Loaded PDF: {filename}")
            elif filename.endswith(".txt"):
                loader = TextLoader(file_path, encoding='utf-8')
                documents.extend(loader.load())
                print(f" - Loaded TXT: {filename}")
            # Add more loaders for other file types (e.g., .docx, .csv) here
        except Exception as e:
            print(f"Failed to load {filename}: {e}")
            continue
    
    return documents

def main():
    """
    Loads documents, splits them into chunks, generates embeddings,
    and stores them in a FAISS vector store.
    """
    print("Starting document ingestion process...")
    
    # 1. Load medical documents using the new loading function
    documents = load_documents(DOCS_DIR)
    
    if not documents:
        print(f"No documents found in {DOCS_DIR}. Please add some text or PDF files.")
        return
    
    print(f"\nLoaded a total of {len(documents)} document pages/sections.")
    
    # 2. Split documents into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    docs = text_splitter.split_documents(documents)
    print(f"Split documents into {len(docs)} chunks.")
    
    # 3. Initialize the embedding model
    print("Initializing embedding model (all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}  # Use CPU for embeddings
    )
    
    # 4. Create and persist the FAISS vector store
    print(f"Creating and persisting FAISS vector store in '{VECTOR_STORE_DIR}'...")
    vectorstore = FAISS.from_documents(
        documents=docs,
        embedding=embeddings
    )
    
    # Save the vector store
    vectorstore.save_local(VECTOR_STORE_DIR)
    
    print("\n-----------------------------------------")
    print("✅ Ingestion complete!")
    print(f" - Total chunks created: {len(docs)}")
    print(f" - Vector store location: {VECTOR_STORE_DIR}")
    print("-----------------------------------------")

if __name__ == "__main__":
    main()