import os
import logging
import json
from typing import List, Dict, Any

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import io

from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse 

# --- IMPORTS FOR PDF & AI ---
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from pypdf import PdfReader, PdfWriter 
import google.generativeai as genai
from dotenv import load_dotenv

# --- IMPORT YOUR ENGINES ---
from knowledge_base import KnowledgeBase 
from entity_engine import extract_hard_facts # Imported only once now


from new_generator import create_policy_brief
from pydantic import BaseModel # Used for data validation 

# --- CONFIGURATION ---
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not API_KEY:
    logger.error("GOOGLE_API_KEY not found. Please set it in .env file.")

genai.configure(api_key=API_KEY)

class AnalysisPayload(BaseModel):
    about: str
    decisions: List[str]
    risks: List[str]
    impact: str
    hard_data: Dict[str, List[str]] 

# --- INITIALIZE APP & KNOWLEDGE BASE ---
app = FastAPI(title="Xaana.AI Government Platform", version="2.0.0")

# Initialize the Vector DB (The Brain)
kb = KnowledgeBase()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- HELPER FUNCTIONS ---

def extract_text_from_pdf(file_stream) -> str:
    """Extracts text using pdfplumber (Read-Only)"""
    full_text = ""
    try:
        with pdfplumber.open(file_stream) as pdf:
            for page in pdf.pages:
                text = page.extract_text(x_tolerance=1, y_tolerance=1)
                if text:
                    full_text += text + "\n"
    except Exception as e:
        logger.error(f"Extraction Error: {e}")
        raise ValueError("Could not extract text.")
    return full_text

def insert_page_logic(base_bytes: bytes, insert_bytes: bytes, index: int = 0) -> io.BytesIO:
    """Merges two PDFs (pypdf)"""
    writer = PdfWriter()
    reader_base = PdfReader(io.BytesIO(base_bytes))
    reader_insert = PdfReader(io.BytesIO(insert_bytes))
    
    total_base = len(reader_base.pages)
    if index > total_base: index = total_base

    for i in range(index):
        writer.add_page(reader_base.pages[i])
    for page in reader_insert.pages:
        writer.add_page(page)
    for i in range(index, total_base):
        writer.add_page(reader_base.pages[i])

    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out

# --- ENDPOINTS ---

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """
    Serves the HTML Frontend when you visit the root URL.
    """
    try:
        with open("index.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "Error: index.html not found. Make sure it is in the same folder."

@app.post("/analyze")
async def analyze_document_endpoint(file: UploadFile = File(...)):
    """
    1. Extracts Text
    2. Indexes it into Vector DB (Memorizes it)
    3. Extracts Hard Facts (NER)
    4. Generates Decision Brief
    """
    logger.info(f"Processing: {file.filename}")
    
    # 1. Read & Extract
    file_bytes = await file.read()
    try:
        # We use a bytes buffer so pdfplumber can read it
        raw_text = extract_text_from_pdf(io.BytesIO(file_bytes))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if len(raw_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="PDF is empty or scanned image.")

    # 2. INGEST INTO KNOWLEDGE BASE (The "Learning" Step)
    try:
        kb.ingest_text(file.filename, raw_text)
        logger.info(f"Document {file.filename} saved to Knowledge Graph.")
    except Exception as e:
        logger.warning(f"Indexing failed (non-critical): {e}")

    # 3. EXTRACT HARD FACTS (Deterministic/Math Layer)
    # This runs locally using spaCy
    facts = extract_hard_facts(raw_text) 

    # 4. Analyze with Gemini (Generative Layer)
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    You are a Senior Policy Analyst. Analyze this document text.
    Return valid JSON with: "about", "decisions" (list), "risks" (list), "impact", "brief".
    Document: {raw_text[:50000]}
    """
    
    try:
        response = model.generate_content(
            prompt, 
            generation_config={"response_mime_type": "application/json"}
        )
        
        # --- CRITICAL FIX: MERGE DATA ---
        ai_response = json.loads(response.text)
        
        # We combine the AI's "Soft" summary with the NLP's "Hard" facts
        final_response = {
            **ai_response,
            "hard_data": facts 
        }
        
        return final_response

    except Exception as e:
        logger.error(f"AI Error: {e}")
        raise HTTPException(status_code=502, detail="AI Analysis Failed")

@app.post("/chat")
async def chat_with_documents(
    query: str = Form(...), 
):
    """
    Semantic Search Endpoint.
    Searches the Vector DB for answers across ALL uploaded PDFs.
    """
    logger.info(f"Chat Query: {query}")
    
    # 1. Retrieve Relevant Facts (RAG)
    retrieved_docs = kb.search(query, top_k=5)
    
    if not retrieved_docs:
        return {"answer": "I could not find any relevant information in the uploaded documents.", "sources": []}

    # 2. Construct Prompt with Ground Truth
    context_text = "\n\n".join([f"[Source: {d['source']}]\n{d['text']}" for d in retrieved_docs])
    
    system_prompt = f"""
    You are a Government Intelligence Assistant. 
    Answer the user's question strictly based on the provided context below.
    If the answer is not in the context, say "Data not found in intelligence database."
    Cite your sources (filenames) for every claim.

    CONTEXT:
    {context_text}

    QUESTION:
    {query}
    """

    # 3. Generate Answer
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(system_prompt)
    
    return {
        "answer": response.text,
        "sources": [d['source'] for d in retrieved_docs]
    }

@app.post("/export/docx")
async def export_brief(payload: AnalysisPayload):
    """
    Generates a Word Document from the provided analysis data.
    """
    # Convert Pydantic model back to dict
    data = payload.dict()

    # Generate Doc
    doc_stream = create_policy_brief(data)

    return StreamingResponse(
        doc_stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=ministerial_brief.docx"}
    )

@app.post("/tools/insert-pdf")
async def insert_pdf_endpoint(
    base_file: UploadFile = File(...),
    insert_file: UploadFile = File(...),
    at_page: int = 0
):
    if not base_file.filename.endswith(".pdf") or not insert_file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Requires PDFs.")
    
    try:
        base_bytes = await base_file.read()
        insert_bytes = await insert_file.read()
        new_pdf = insert_page_logic(base_bytes, insert_bytes, at_page)
        
        return StreamingResponse(
            new_pdf, 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=modified_{base_file.filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    