import pdfplumber
import os

def extract_text_from_pdf(file_path=None, file_object=None):
    """
    Extract text from a PDF file.
    Accepts either a file path (string) or a file object (from Streamlit uploader)
    Returns: (text, page_count, error)
    """
    try:
        if file_object is not None:
            with pdfplumber.open(file_object) as pdf:
                page_count = len(pdf.pages)
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        elif file_path is not None:
            if not os.path.exists(file_path):
                return None, 0, f"⚠️ File not found: {file_path}"
            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        else:
            return None, 0, "⚠️ No file provided."

        if len(text.strip()) == 0:
            return None, page_count, "⚠️ Could not extract any text from this PDF. It may be scanned or image based."

        return text, page_count, None

    except Exception as e:
        return None, 0, f"⚠️ Error reading PDF: {str(e)}"