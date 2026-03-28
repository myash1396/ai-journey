import requests
import json

def review_email(draft):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": f"You are a professional email writer. Rewrite the following draft email to make it clear, polite and professional. Only return the rewritten email, nothing else.\n\nDraft: {draft}",
            "stream": False
        }
    )
    result = response.json()
    return result["response"]

# Your draft email
draft_email = """
hi john,
I wanted to check on the last mail i sent you about the report. Can you please make sure to send before eod? The clients are looking for an update.
Let me know, if you have any questions.
Thanks,
"""

print("Original Draft:")
print(draft_email)
print("\nRewritten by AI:")
print(review_email(draft_email))