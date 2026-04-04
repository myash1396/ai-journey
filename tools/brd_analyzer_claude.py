import os
import anthropic
from datetime import datetime

def analyze_brd(document_text, model="claude-sonnet-4-6", temperature=0.2):
    """
    Analyze a BRD document using Claude via the Anthropic API.
    Returns: (analysis, error)
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None, "⚠️ ANTHROPIC_API_KEY environment variable is not set. Please set it and restart the app."

    prompt_path = os.path.join("prompts", "brd_analyzer.md")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        return None, "⚠️ BRD analyzer prompt file not found."

    user_message = f"BRD DOCUMENT:\n{document_text}\n\nANALYSIS:"

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            temperature=temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        return response.content[0].text, None

    except anthropic.APIConnectionError:
        return None, "⚠️ Cannot connect to the Anthropic API. Please check your internet connection."
    except anthropic.APIStatusError as e:
        return None, f"⚠️ Anthropic API error (status {e.status_code}): {str(e)}"
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
        f.write(f"**Model:** Claude Sonnet (Anthropic API)\n\n")
        f.write("---\n\n")
        f.write(analysis)

    return output_path
