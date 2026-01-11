import os
import base64
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import io

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
VECTOR_STORE_DIR = "vector_store"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Configure Google Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set. Please set it in .env file or environment.")

genai.configure(api_key=GOOGLE_API_KEY)

# --- Initialization ---
app = FastAPI(
    title="Multimodal Medical RAG Chatbot",
    description="A Retrieval-Augmented Generation chatbot with image and voice support.",
    version="3.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Starting Multimodal Medical RAG Chatbot API...")

# Initialize Gemini models
print("Initializing Google Gemini models...")

# Text model
text_model_names = [
    'models/gemini-2.5-flash',
    'models/gemini-flash-latest',
    'models/gemini-2.0-flash',
]

gemini_text_model = None
for model_name in text_model_names:
    try:
        print(f"Trying text model: {model_name}")
        gemini_text_model = genai.GenerativeModel(model_name)
        test_response = gemini_text_model.generate_content("Hello")
        print(f"✅ Successfully loaded text model: {model_name}")
        break
    except Exception as e:
        print(f"❌ Failed to load {model_name}: {str(e)[:100]}")
        continue

# Vision model (for multimodal)
vision_model_names = [
    'models/gemini-2.5-flash',
    'models/gemini-2.0-flash',
    'models/gemini-pro-vision',
]

gemini_vision_model = None
for model_name in vision_model_names:
    try:
        print(f"Trying vision model: {model_name}")
        gemini_vision_model = genai.GenerativeModel(model_name)
        print(f"✅ Successfully loaded vision model: {model_name}")
        break
    except Exception as e:
        print(f"❌ Failed to load {model_name}: {str(e)[:100]}")
        continue

if gemini_text_model is None:
    raise ValueError("Could not initialize text model. Please check your API key.")

# Load the embedding model
print("Loading embedding model...")
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL_NAME,
    model_kwargs={'device': 'cpu'}
)

# Load the persistent vector store
print("Loading vector store...")
if not os.path.exists(VECTOR_STORE_DIR):
    raise FileNotFoundError(
        f"Vector store directory '{VECTOR_STORE_DIR}' not found. "
        "Please run `ingest_docs.py` first."
    )

vectorstore = FAISS.load_local(
    folder_path=VECTOR_STORE_DIR,
    embeddings=embeddings,
    allow_dangerous_deserialization=True
)

print("✅ All components loaded successfully!")

# --- Pydantic Models ---
class AskRequest(BaseModel):
    query: str
    image_base64: Optional[str] = None

class AskResponse(BaseModel):
    answer: str
    sources: List[str]

class TranscribeRequest(BaseModel):
    audio_base64: str

class TranscribeResponse(BaseModel):
    text: str


# --- Helper Functions ---
def construct_prompt(context: str, question: str) -> str:
    """Constructs a detailed prompt for the LLM."""
    prompt_template = """You are a helpful medical assistant. Your task is to answer the user's question based *only* on the provided context.

IMPORTANT GUIDELINES:
- Be concise and to the point.
- If the context does not contain the answer, state that you don't have enough information.
- Do not make up information.
- Base your answer strictly on the context provided.

CONTEXT:
{context}

USER QUESTION:
{question}

Please provide a clear and accurate answer based on the context above."""
    
    return prompt_template.format(context=context, question=question)

def construct_vision_prompt(context: str, question: str) -> str:
    """Constructs a prompt for vision-based queries."""
    prompt_template = """You are a helpful medical assistant analyzing medical images. 

CONTEXT FROM KNOWLEDGE BASE:
{context}

USER QUESTION:
{question}

Please analyze the image and provide insights based on:
1. What you observe in the image
2. Relevant medical information from the context provided
3. Any potential concerns or observations

Be clear that you're an AI assistant and recommend consulting healthcare professionals for proper diagnosis."""
    
    return prompt_template.format(context=context, question=question)


# --- API Endpoints ---
@app.get("/")
def read_root():
    """Root endpoint to check if the API is running."""
    return {
        "message": "Multimodal Medical RAG Chatbot is running.",
        "status": "active",
        "features": ["text", "vision", "voice"],
        "endpoints": {
            "ask": "/ask",
            "transcribe": "/transcribe",
            "docs": "/docs"
        }
    }


@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Receives a user query (text and/or image), retrieves relevant context, 
    and generates an answer using Google Gemini.
    """
    query = request.query
    image_base64 = request.image_base64
    
    if not query and not image_base64:
        raise HTTPException(status_code=400, detail="Query or image must be provided.")

    try:
        # 1. Retrieve relevant context from vector store
        print(f"Retrieving context for query: '{query}'")
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
        retrieved_docs = retriever.invoke(query if query else "medical information")
        
        context = ""
        sources = []
        if retrieved_docs:
            context = "\n\n".join([doc.page_content for doc in retrieved_docs])
            sources = list(set([
                os.path.basename(doc.metadata.get('source', 'Unknown')) 
                for doc in retrieved_docs
            ]))

        # 2. Handle image-based queries
        if image_base64:
            if not gemini_vision_model:
                raise HTTPException(
                    status_code=503, 
                    detail="Vision model not available."
                )
            
            # Decode base64 image
            image_data = base64.b64decode(image_base64.split(',')[1] if ',' in image_base64 else image_base64)
            image = Image.open(io.BytesIO(image_data))
            
            # Construct vision prompt
            prompt = construct_vision_prompt(context, query if query else "What do you see in this medical image?")
            
            print("Generating answer with vision model...")
            response = gemini_vision_model.generate_content(
                [prompt, image],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=512,
                )
            )
            answer = response.text.strip()
        
        # 3. Handle text-only queries
        else:
            if not context:
                return AskResponse(
                    answer="I don't have enough information to answer that question.", 
                    sources=[]
                )
            
            prompt = construct_prompt(context, query)
            
            print("Generating answer with text model...")
            response = gemini_text_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=512,
                )
            )
            answer = response.text.strip()

        print(f"✅ Answer generated successfully")
        return AskResponse(answer=answer, sources=sources)

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal Server Error: {str(e)}"
        )


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(request: TranscribeRequest):
    """
    Transcribes audio to text using browser's built-in speech recognition.
    This endpoint is a placeholder - transcription happens on the frontend.
    """
    # Note: For server-side transcription, you could use services like:
    # - Google Cloud Speech-to-Text
    # - OpenAI Whisper
    # - Azure Speech Services
    
    return TranscribeResponse(
        text="Server-side transcription not implemented. Using browser speech recognition."
    )


# To run the app:
# 1. Install: pip install google-generativeai pillow
# 2. Set API key: export GOOGLE_API_KEY="your-api-key-here"
# 3. Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000