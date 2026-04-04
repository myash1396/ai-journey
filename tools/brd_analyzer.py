import os
import requests
from datetime import datetime

def analyze_brd(document_text, model="llama3", temperature=0.2):
    """
    Analyze a BRD document and return structured analysis.
    Returns: (analysis, error)
    """
    prompt_path = os.path.join("prompts", "brd_analyzer.md")
    try:
       with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        return None, "⚠️ BRD analyzer prompt file not found."

    prompt = f"{system_prompt}\n\nBRD DOCUMENT:\n{document_text}\n\nANALYSIS:"

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature
            },
            timeout=120
        )
        result = response.json()
        return result["response"], None

    except requests.exceptions.ConnectionError:
        return None, "⚠️ Cannot connect to Ollama. Please make sure Ollama is running."
    except requests.exceptions.Timeout:
        return None, "⚠️ Analysis timed out. Document may be too large. Try a smaller section."
    except Exception as e:
        return None, f"⚠️ Something went wrong: {str(e)}"

def save_analysis(document_name, analysis):
    """
    Save BRD analysis to outputs folder.
    Returns: output_path
    """
    os.makedirs("outputs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join("outputs", f"brd_analysis_{timestamp}.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# BRD Analysis Report\n\n")
        f.write(f"**Document:** {document_name}\n")
        f.write(f"**Analyzed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Model:** Llama3 (Local)\n\n")
        f.write("---\n\n")
        f.write(analysis)

    return output_path