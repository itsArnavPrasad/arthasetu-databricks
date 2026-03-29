import os
import glob
import pandas as pd

# For PDF Extraction
# pip install PyPDF2
from PyPDF2 import PdfReader

# For Chunking
# pip install langchain
from langchain_text_splitters import RecursiveCharacterTextSplitter

# For Embeddings
# pip install langchain-community sentence-transformers
from langchain_community.embeddings import HuggingFaceEmbeddings

# Define paths
PDF_DIR = "raw_data/pdfs/"
OUTPUT_PATH = "output/pdf_chunks_with_embeddings.json"

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a given PDF file.
    Note: For digital PDFs, PyPDF2 works perfectly. 
    If the PDFs are scanned images, you would need true OCR using libraries like `pytesseract` and `pdf2image`.
    """
    print(f"Reading {pdf_path}...")
    try:
        reader = PdfReader(pdf_path)
        full_text = ""
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                full_text += f"\n{text}"
        return full_text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""

def chunk_text(text):
    """
    Splits a large text block into smaller chunks for embeddings and RAG.
    """
    print("Chunking text...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.create_documents([text])
    return [chunk.page_content for chunk in chunks]

def generate_embeddings(chunks):
    """
    Generates vector embeddings for a list of text chunks using HuggingFace sentence-transformers.
    """
    print(f"Generating embeddings for {len(chunks)} chunks...")
    # This uses a free, local model that doesn't require an API key
    # Model: all-MiniLM-L6-v2 is an excellent balance of speed and semantic performance
    embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    embeddings = embeddings_model.embed_documents(chunks)
    return embeddings

def main():
    # 1. Find all PDFs in the input directory
    pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
    if not pdf_files:
        print(f"No PDFs found in {PDF_DIR}")
        return
        
    print(f"Found {len(pdf_files)} PDFs to process.")
    all_chunks = []
    
    # 2. Extract Text & Chunk
    for pdf_file in pdf_files:
        # Extract text
        text = extract_text_from_pdf(pdf_file)
        
        if not text.strip():
            print(f"Warning: No text extracted from {pdf_file}. It might be a scanned image requiring true OCR.")
            continue
            
        # Chunk text
        chunks = chunk_text(text)
        
        # Store chunks with metadata
        for chunk in chunks:
            all_chunks.append({
                "source": os.path.basename(pdf_file),
                "text": chunk
            })
            
    if not all_chunks:
        print("No text chunks were generated.")
        return
        
    # Prepare data for embedding
    chunk_texts = [item["text"] for item in all_chunks]
    
    # 3. Generate Embeddings
    embeddings = generate_embeddings(chunk_texts)
    
    # Attach embeddings to our chunk dictionary
    for i, item in enumerate(all_chunks):
        item["embedding"] = embeddings[i]
        
    print(f"\nSuccessfully processed {len(pdf_files)} PDFs.")
    print(f"Resulting chunks: {len(all_chunks)}")
    print(f"Embedding dimensions: {len(all_chunks[0]['embedding'])}")
    
    # 4. Save results
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df = pd.DataFrame(all_chunks)
    
    # Saving as JSON is generally better for embeddings since native array lists are preserved 
    df.to_json(OUTPUT_PATH, orient="records", lines=True)
    print(f"\nSaved all text chunks and embeddings to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
