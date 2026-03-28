import os
import requests
from datetime import datetime

# Import our existing tools
from tools.email_agent import review_email, conversation_history
from tools.summarizer import summarize_document, save_summary, load_document

def answer_question(document_text, question):
    prompt = f"""You are an expert document analyst working in banking and finance.
You have been given a document to read and a question to answer.
Answer the question using ONLY the information found in the document.
If the answer is not in the document, say "I could not find this information in the document."
Be specific and quote relevant parts where helpful.
Keep your answer concise and clear.

DOCUMENT:
{document_text}

QUESTION:
{question}

ANSWER:"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    result = response.json()
    return result["response"]

def save_qa_session(document_path, qa_pairs):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join("outputs", f"qa_session_{timestamp}.txt")

    with open(output_path, "a") as f:
        f.write("=" * 50 + "\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Document: {document_path}\n")
        f.write("=" * 50 + "\n\n")
        for i, (question, answer) in enumerate(qa_pairs, 1):
            f.write(f"Q{i}: {question}\n")
            f.write(f"A{i}: {answer}\n\n")

    print(f"\n✅ Q&A session saved to {output_path}")

def main():
    print("=" * 50)
    print("   Master AI Agent - Banking Edition")
    print("   Powered by Llama3 running locally")
    print("=" * 50)

    while True:
        print("\nWhat would you like to do?")
        print("1. Review and rewrite an email")
        print("2. Summarize a document")
        print("3. Ask questions about a document")
        print("4. Quit")

        choice = input("\nEnter 1, 2, 3 or 4: ").strip()

        # ─── EMAIL REVIEWER ───
        if choice == "1":
            print("\nType your draft email. When done type END on a new line.\n")
            lines = []
            while True:
                line = input()
                if line.strip().upper() == "END":
                    break
                lines.append(line)
            draft = "\n".join(lines)

            print("\nChoose tone:")
            print("1. Professional")
            print("2. Friendly")
            print("3. Formal")
            tone_choice = input("\nEnter 1, 2 or 3: ").strip()
            tones = {"1": "professional", "2": "friendly", "3": "formal"}
            tone = tones.get(tone_choice, "professional")

            print("\nProcessing...\n")
            rewritten = review_email(draft, tone)
            print("=" * 50)
            print("REWRITTEN EMAIL:")
            print("=" * 50)
            print(rewritten)

        # ─── DOCUMENT SUMMARIZER ───
        elif choice == "2":
            filepath = input("\nEnter file path (e.g. docs/sample_policy.txt): ").strip()
            text = load_document(filepath)
            if not text:
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

        # ─── DOCUMENT Q&A ───
        elif choice == "3":
            filepath = input("\nEnter file path (e.g. docs/sample_policy.txt): ").strip()
            text = load_document(filepath)
            if not text:
                continue

            print(f"\n✅ Document loaded successfully.")
            print("You can now ask questions about this document.")
            print("Type DONE when finished.\n")

            qa_pairs = []

            while True:
                question = input("Your question: ").strip()
                if question.upper() == "DONE":
                    break
                if not question:
                    continue

                print("\nSearching document...\n")
                answer = answer_question(text, question)
                print("=" * 50)
                print(f"ANSWER: {answer}")
                print("=" * 50)

                qa_pairs.append((question, answer))

            if qa_pairs:
                save_qa_session(filepath, qa_pairs)
                print(f"\n📝 Session complete. {len(qa_pairs)} questions answered.")

        elif choice == "4":
            print("\nGoodbye! Keep building. 👋")
            break

        else:
            print("\n⚠️ Invalid choice. Please enter 1, 2, 3 or 4.")

if __name__ == "__main__":
    main()