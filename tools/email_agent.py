import requests
import json
from datetime import datetime
import os

# Memory - stores all emails reviewed in this session
conversation_history = []

# Output file - all rewritten emails saved here
output_file = "reviewed_emails.txt"

def save_to_file(original, rewritten, tone):
    with open(output_file, "a") as f:
        f.write("=" * 50 + "\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Tone: {tone}\n")
        f.write("\nORIGINAL DRAFT:\n")
        f.write(original + "\n")
        f.write("\nREWRITTEN BY AI:\n")
        f.write(rewritten + "\n\n")
    print(f"\n✅ Saved to {output_file}")

def review_email(draft, tone="professional"):
    # Add the new draft to conversation history
    conversation_history.append({
        "role": "user",
        "content": f"Please rewrite this email in a {tone} tone:\n\n{draft}"
    })

    # Build the full prompt with memory
    system_prompt = """You are an expert email assistant working in the banking and finance industry.
You understand compliance, professionalism and corporate communication.
When asked to rewrite an email, only return the rewritten email. Nothing else.
When asked to modify a previous email, refer to the conversation history."""

    # Combine system prompt with full conversation history
    full_prompt = system_prompt + "\n\n"
    for message in conversation_history:
        if message["role"] == "user":
            full_prompt += f"User: {message['content']}\n"
        elif message["role"] == "assistant":
            full_prompt += f"Assistant: {message['content']}\n"

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": full_prompt,
            "stream": False
        }
    )

    result = response.json()
    ai_response = result["response"]

    # Save AI response to memory
    conversation_history.append({
        "role": "assistant",
        "content": ai_response
    })

    return ai_response

def main():
    print("=" * 50)
    print("   AI Email Agent - Banking Edition")
    print("   Powered by Llama3 running locally")
    print("=" * 50)
    print("\nSession started. I will remember all emails in this session.")
    print("Type 'quit' anytime to exit.\n")

    while True:
        print("\nWhat would you like to do?")
        print("1. Review a new email")
        print("2. Modify the last rewritten email")
        print("3. View session history")
        print("4. Quit")

        choice = input("\nEnter 1, 2, 3 or 4: ").strip()

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
            save_to_file(draft, rewritten, tone)

        elif choice == "2":
            if len(conversation_history) == 0:
                print("\n⚠️ No emails reviewed yet in this session.")
            else:
                print("\nWhat changes do you want? (e.g. make it shorter, more formal, add urgency)")
                modification = input("> ").strip()
                print("\nProcessing...\n")
                rewritten = review_email(modification, "as requested")
                print("=" * 50)
                print("MODIFIED EMAIL:")
                print("=" * 50)
                print(rewritten)
                save_to_file(f"(modification request): {modification}", rewritten, "modified")

        elif choice == "3":
            if len(conversation_history) == 0:
                print("\n⚠️ No history yet.")
            else:
                print(f"\n📝 Emails reviewed this session: {len(conversation_history) // 2}")
                print(f"💾 All saved to: {output_file}")

        elif choice == "4":
            print("\nGood work today. All emails saved to reviewed_emails.txt")
            print("See you next session! 👋")
            break

        else:
            print("\n⚠️ Invalid choice. Please enter 1, 2, 3 or 4.")

# Run the app
if __name__ == "__main__":
    main()
