import pdfplumber
import os

def extract_text_from_pdf(file_path=None, file_object=None):
    """
    Extract text from a PDF file.
    Accepts either a file path (string) or a file object (from Streamlit uploader)
    Returns: (text, error)
    """
    try:
        if file_object is not None:
            with pdfplumber.open(file_object) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        elif file_path is not None:
            if not os.path.exists(file_path):
                return None, f"⚠️ File not found: {file_path}"
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        else:
            return None, "⚠️ No file provided."

        if len(text.strip()) == 0:
            return None, "⚠️ Could not extract any text from this PDF. It may be scanned or image based."

        return text, None

    except Exception as e:
        return None, f"⚠️ Error reading PDF: {str(e)}"