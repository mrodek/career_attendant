from fastapi import UploadFile
from pypdf import PdfReader
import docx
import io

async def extract_text(file: UploadFile) -> str:
    """Extracts text from an uploaded file (PDF or DOCX)."""
    content = await file.read()
    
    if file.content_type == "application/pdf":
        return extract_text_from_pdf(content)
    elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(content)
    else:
        raise ValueError("Unsupported file type")

def extract_text_from_pdf(content: bytes) -> str:
    """Extracts text from PDF content."""
    pdf_reader = PdfReader(io.BytesIO(content))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(content: bytes) -> str:
    """Extracts text from DOCX content."""
    doc = docx.Document(io.BytesIO(content))
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text
