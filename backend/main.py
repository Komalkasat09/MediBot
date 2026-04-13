import os
import base64
import json
import re
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None
from dotenv import load_dotenv
from PIL import Image
import io
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# Load environment variables from .env file in this directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

# --- Configuration ---
BASE_DIR = os.path.dirname(__file__)
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "vector_store")
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Configure Groq Llama
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please set it in .env file or environment.")

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Configure Gemini for image analysis
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

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
print(f"Using Groq model: {GROQ_MODEL}")

gemini_client = None

def get_gemini_client():
    """Create a singleton Gemini client for image analysis."""
    global gemini_client
    if genai is None:
        raise RuntimeError("google-genai package not installed")
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")
    if gemini_client is None:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return gemini_client

def extract_gemini_text(response) -> str:
    """Extract text from a Gemini response across SDK versions."""
    text = getattr(response, "text", None)
    if text:
        return text.strip()
    try:
        return response.candidates[0].content.parts[0].text.strip()
    except Exception:
        return ""

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

def groq_chat_completion(prompt: str) -> str:
    """Call Groq chat completion API with a single user prompt."""
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful medical assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 512
    }

    req = Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "MediBot/1.0"
        }
    )

    try:
        with urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else str(e)
        raise RuntimeError(f"Groq API error: {error_body}")

    return data["choices"][0]["message"]["content"].strip()

def build_reference(doc) -> str:
    """Build a compact citation with page and in-page location instead of filename."""
    metadata = doc.metadata or {}

    # PyPDFLoader usually provides 0-based `page`; prefer explicit page labels when available.
    page_label = metadata.get("page_label")
    page_number = metadata.get("page")
    if page_label is not None:
        page_text = str(page_label)
    elif isinstance(page_number, int):
        page_text = str(page_number + 1)
    else:
        page_text = "Unknown"

    # If start_index exists (from ingestion), expose an exact span in the page text.
    start_index = metadata.get("start_index")
    if isinstance(start_index, int):
        end_index = start_index + len((doc.page_content or "").strip())
        location_text = f"chars {start_index}-{end_index}"
    else:
        location_text = "chunk"

    excerpt = " ".join((doc.page_content or "").split())
    if len(excerpt) > 90:
        excerpt = excerpt[:87].rstrip() + "..."

    return f"Page {page_text} | {location_text} | {excerpt}"

def is_medical_query(query: str) -> bool:
    """Heuristic gate: run web search fallback only for medical questions."""
    if not query:
        return False

    medical_terms = {
        "medical", "medicine", "disease", "condition", "diagnosis", "diagnose",
        "symptom", "symptoms", "treatment", "therapy", "drug", "medication",
        "dose", "infection", "virus", "bacteria", "blood", "pressure", "diabetes",
        "hypertension", "cancer", "cardiac", "heart", "kidney", "liver", "lung",
        "pain", "fever", "cough", "headache", "doctor", "hospital", "report",
        "lab", "test", "scan", "xray", "mri", "ct", "patient", "clinical"
    }
    query_words = {w.strip(".,!?():;\"'").lower() for w in query.split()}
    return len(medical_terms.intersection(query_words)) > 0

def fetch_medical_web_context(query: str) -> tuple[str, List[str]]:
    """Fetch concise, non-paywalled medical web context from Wikipedia search endpoints."""
    try:
        def wiki_titles(search_text: str) -> List[str]:
            encoded_query = quote(search_text)
            search_url = (
                "https://en.wikipedia.org/w/api.php"
                f"?action=opensearch&search={encoded_query}&limit=3&namespace=0&format=json"
            )
            req = Request(search_url, headers={"User-Agent": "MediBot/1.0"})
            with urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data[1] if isinstance(data, list) and len(data) > 1 else []

        titles = wiki_titles(query)
        if not titles:
            # Retry with compact medical key-terms from natural language prompts.
            stop_words = {
                "what", "is", "are", "how", "why", "the", "a", "an", "and", "or",
                "of", "for", "to", "in", "on", "with", "does", "do", "i", "me", "my"
            }
            words = [w.lower() for w in re.findall(r"[a-zA-Z0-9]+", query)]
            filtered = [w for w in words if w not in stop_words]
            if filtered:
                retry_queries = []
                retry_queries.append(" ".join(filtered[:6]).strip())
                retry_queries.append(" ".join(filtered[:4]).strip())
                retry_queries.append(" ".join(filtered[:2]).strip())

                for compact_query in retry_queries:
                    if not compact_query or compact_query == query.strip().lower():
                        continue
                    titles = wiki_titles(compact_query)
                    if titles:
                        break

        if not titles:
            # Final fallback: DuckDuckGo instant answer for quick medical definitions.
            ddg_url = (
                "https://api.duckduckgo.com/"
                f"?q={quote(query)}&format=json&no_html=1&skip_disambig=1"
            )
            ddg_req = Request(ddg_url, headers={"User-Agent": "MediBot/1.0"})
            with urlopen(ddg_req, timeout=8) as ddg_resp:
                ddg_data = json.loads(ddg_resp.read().decode("utf-8"))

            abstract = (ddg_data.get("AbstractText") or "").strip()
            abstract_url = ddg_data.get("AbstractURL")
            heading = (ddg_data.get("Heading") or "Medical Reference").strip()

            if abstract:
                web_source = [f"Web | {heading} | {abstract_url}"] if abstract_url else [f"Web | {heading}"]
                return f"{heading}: {abstract}", web_source
            return "", []

        snippets = []
        sources = []

        for title in titles[:2]:
            title_encoded = quote(title)
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title_encoded}"
            summary_req = Request(summary_url, headers={"User-Agent": "MediBot/1.0"})

            with urlopen(summary_req, timeout=8) as summary_resp:
                summary_data = json.loads(summary_resp.read().decode("utf-8"))

            extract = (summary_data.get("extract") or "").strip()
            if extract:
                snippets.append(f"{title}: {extract}")

            page_url = summary_data.get("content_urls", {}).get("desktop", {}).get("page")
            if page_url:
                sources.append(f"Web | {title} | {page_url}")

        if not snippets:
            return "", sources

        return "\n\n".join(snippets), sources
    except Exception as e:
        print(f"Web fallback search failed: {e}")
        return "", []


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
    and generates an answer using Groq Llama.
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
            seen = set()
            for doc in retrieved_docs:
                reference = build_reference(doc)
                if reference not in seen:
                    seen.add(reference)
                    sources.append(reference)

        # 1b. Medical-only web fallback to improve coverage when local context is weak.
        if is_medical_query(query):
            web_context, web_sources = fetch_medical_web_context(query)
            if web_context:
                context = f"{context}\n\n{web_context}".strip() if context else web_context
            if web_sources:
                for src in web_sources:
                    if src not in sources:
                        sources.append(src)

        # 2. Handle image-based queries
        if image_base64:
            try:
                client = get_gemini_client()
            except RuntimeError:
                raise HTTPException(
                    status_code=503,
                    detail="Gemini model not available. Set GEMINI_API_KEY and install google-genai to enable image analysis."
                )

            image_data = base64.b64decode(image_base64.split(',')[1] if ',' in image_base64 else image_base64)
            image = Image.open(io.BytesIO(image_data))

            prompt = construct_vision_prompt(
                context,
                query if query else "What do you see in this medical image?"
            )

            mime_type = "image/png"
            if image_base64.startswith("data:") and ";base64," in image_base64:
                mime_type = image_base64.split(";")[0].split(":", 1)[1]

            print("Generating answer with Gemini model...")
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_bytes(data=image_data, mime_type=mime_type)
                ]
            )
            answer = extract_gemini_text(response)
            if not answer:
                raise HTTPException(
                    status_code=502,
                    detail="Gemini response contained no text."
                )
        
        # 3. Handle text-only queries
        else:
            if not context:
                return AskResponse(
                    answer="I don't have enough information to answer that question.", 
                    sources=[]
                )
            
            prompt = construct_prompt(context, query)
            
            print("Generating answer with Groq Llama...")
            answer = groq_chat_completion(prompt)

        print(f"✅ Answer generated successfully")
        return AskResponse(answer=answer, sources=sources)

    except HTTPException:
        raise
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
# 1. Install: pip install fastapi uvicorn python-dotenv langchain langchain-community sentence-transformers faiss-cpu pypdf
# 2. Set API key: export GROQ_API_KEY="your-api-key-here"
# 3. Optional model: export GROQ_MODEL="llama-3.1-8b-instant"
# 4. Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000