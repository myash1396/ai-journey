import requests

def review_email(draft, tone="professional", role="email assistant"):
    system_prompt = f"""You are an expert {role} working in the banking and finance industry. 
You understand compliance, professionalism and corporate communication. 
Rewrite emails to be {tone}, clear and appropriate for a banking environment.
Only return the rewritten email. Nothing else. No explanations."""

    full_prompt = f"{system_prompt}\n\nDraft email to rewrite:\n{draft}"

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

print("=== AI Email Reviewer - Banking Edition ===")
print("Type your draft email. When done, type END on a new line.\n")

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

print(f"\nProcessing...\n")
print("=== Rewritten Email ===")
print(review_email(draft, tone, role="banking communication specialist"))