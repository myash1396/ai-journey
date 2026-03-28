import streamlit as st
import requests

def review_email(draft, tone):
    prompt = f"""You are an expert email assistant working in the banking 
and finance industry. Rewrite the following draft email to be {tone}, 
clear and professional. Only return the rewritten email. Nothing else.

Draft: {draft}"""

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

# ─── PAGE CONFIG ───
st.set_page_config(
    page_title="AI Email Agent",
    page_icon="✉️",
    layout="centered"
)

# ─── HEADER ───
st.title("✉️ AI Email Agent")
st.subheader("Banking Edition — Powered by Llama3")
st.divider()

# ─── INPUT SECTION ───
st.markdown("### 📝 Your Draft Email")
draft = st.text_area(
    label="Type or paste your draft email here",
    height=200,
    placeholder="e.g. hi john, need the report asap. let me know."
)

# ─── TONE SELECTOR ───
st.markdown("### 🎯 Choose Tone")
tone = st.radio(
    label="Select the tone for your rewritten email",
    options=["Professional", "Friendly", "Formal"],
    horizontal=True
)

st.divider()

# ─── SUBMIT BUTTON ───
if st.button("✨ Rewrite Email", type="primary", use_container_width=True):
    if not draft.strip():
        st.warning("⚠️ Please enter a draft email first.")
    else:
        with st.spinner("AI is rewriting your email..."):
            result = review_email(draft, tone.lower())

        st.markdown("### ✅ Rewritten Email")
        st.success(result)

        # Copy friendly output
        st.markdown("### 📋 Copy Ready Version")
        st.code(result, language=None)
