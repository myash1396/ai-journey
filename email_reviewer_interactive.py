import requests

def review_email(draft, tone="professional"):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": f"You are a professional email writer. Rewrite the following draft email to be clear, polite and {tone}. Only return the rewritten email, nothing else.\n\nDraft: {draft}",
            "stream": False
        }
    )
    result = response.json()
    return result["response"]

print("=== AI Email Reviewer ===")
print("Type your draft email below. When done, type END on a new line and press Enter.\n")

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
choice = input("\nEnter 1, 2 or 3: ")

tones = {"1": "professional", "2": "friendly", "3": "formal"}
tone = tones.get(choice, "professional")

print(f"\nRewriting your email in a {tone} tone...\n")
print("=== AI Rewritten Email ===")
print(review_email(draft, tone))