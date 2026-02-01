# /Users/jas/Documents/Coding/EasyLearn/voice_agent/parse_pdf.py
from PyPDF2 import PdfReader

def parse_pdf(file_path):
    """Parse PDF and extract text"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def get_lecture_context():
    """Load backtracking lecture notes"""
    pdf_file = "../backend/source_example/02-backtracking.pdf"
    extracted_text = parse_pdf(pdf_file)
    return {
        "label": "backtracking lecture notes",
        "content": extracted_text
    }

if __name__ == "__main__":
    context = get_lecture_context()
    print(f"Loaded: {context['label']}")