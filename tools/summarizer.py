import requests
import os
from datetime import datetime

# Output folder
OUTPUT_FOLDER = "outputs"

def summarize_document(text, summary_type="general"):
    
    prompts = {
        "general": """You are an expert document analyst working in banking and finance.
Read the following document and provide a structured summary with these sections:
1. PURPOSE - What is this document about in one sentence
2. KEY POINTS - Top 5 most important points as bullet points
3. WHO IT AFFECTS - Who does this apply to
4. ACTION ITEMS - What actions are required if any
5. RISK FLAGS - Any compliance or risk related items to be aware of

Be concise. Use plain English. No jargon.""",

        "brief": """You are an expert document analyst working in banking and finance.
Summarize the following document in maximum 5 sentences.
Focus on the most critical information only.""",

        "bullet": """You are an expert document analyst working in banking and finance.
Convert the following document into clean bullet points only.
Maximum 10 bullet points. Each point must be one clear sentence."""
    }

    system_prompt = prompts.get(summary_type, prompts["general"])
    full_prompt = f"{system_prompt}\n\nDOCUMENT:\n{text}"

    print("\nAnalyzing document... please wait.\n")

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": full_prompt,
            "stream": False
        }
    )

    result = response.json()
    return result["response"]

def save_summary(original_file, summary, summary_type):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"summary_{timestamp}.txt"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    with open(output_path, "a") as f:
        f.write("=" * 50 + "\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source: {original_file}\n")
        f.write(f"Summary Type: {summary_type}\n")
        f.write("=" * 50 + "\n\n")
        f.write(summary)
        f.write("\n\n")

    print(f"✅ Summary saved to {output_path}")
    return output_path

def load_document(filepath):
    if not os.path.exists(filepath):
        print(f"⚠️ File not found: {filepath}")
        return None
    with open(filepath, "r") as f:
        return f.read()

def main():
    print("=" * 50)
    print("   AI Document Summarizer - Banking Edition")
    print("   Powered by Llama3 running locally")
    print("=" * 50)

    while True:
        print("\nWhat would you like to do?")
        print("1. Summarize a document file")
        print("2. Paste text directly")
        print("3. Quit")

        choice = input("\nEnter 1, 2 or 3: ").strip()

        if choice == "1":
            filepath = input("\nEnter file path (e.g. docs/sample_policy.txt): ").strip()
            text = load_document(filepath)
            if not text:
                continue

        elif choice == "2":
            print("\nPaste your text below. When done type END on a new line.\n")
            lines = []
            while True:
                line = input()
                if line.strip().upper() == "END":
                    break
                lines.append(line)
            text = "\n".join(lines)
            filepath = "pasted_text"

        elif choice == "3":
            print("\nGoodbye! 👋")
            break

        else:
            print("\n⚠️ Invalid choice.")
            continue

        print("\nChoose summary type:")
        print("1. General (structured with sections)")
        print("2. Brief (5 sentences)")
        print("3. Bullet points only")
        type_choice = input("\nEnter 1, 2 or 3: ").strip()

        summary_types = {"1": "general", "2": "brief", "3": "bullet"}
        summary_type = summary_types.get(type_choice, "general")

        summary = summarize_document(text, summary_type)

        print("\n" + "=" * 50)
        print("SUMMARY:")
        print("=" * 50)
        print(summary)

        save_summary(filepath, summary, summary_type)

if __name__ == "__main__":
    main()