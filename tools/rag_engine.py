import chromadb
from sentence_transformers import SentenceTransformer
import anthropic
import os
import textwrap


def chunk_document(file_path, chunk_size=500, overlap=50):
    """Read a file and split it into overlapping chunks on sentence boundaries."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return []
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

    sentences = text.replace("\n", " ").split(".")
    sentences = [s.strip() + "." for s in sentences if s.strip()]

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Build overlap from the end of the current chunk
            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_chunk = overlap_text + " " + sentence
        else:
            current_chunk = (current_chunk + " " + sentence).strip()

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    print(f"Created {len(chunks)} chunks from {os.path.basename(file_path)}")
    return chunks


def ingest_documents(file_paths, collection_name="banking_docs"):
    """Embed and store document chunks in ChromaDB."""
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(name=collection_name)

    print("Loading embedding model...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    for file_path in file_paths:
        chunks = chunk_document(file_path)
        if not chunks:
            continue

        filename = os.path.basename(file_path)
        name_stem = os.path.splitext(filename)[0]

        embeddings = model.encode(chunks).tolist()

        ids = [f"doc_{name_stem}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": filename, "chunk_index": i} for i in range(len(chunks))]

        collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )

        print(f"Ingested {filename}: {len(chunks)} chunks added to collection '{collection_name}'")


def query_rag(question, collection_name="banking_docs", n_results=3):
    """Query the RAG pipeline: retrieve relevant chunks and ask Claude."""
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    client = chromadb.PersistentClient(path="./chroma_db")
    try:
        collection = client.get_collection(name=collection_name)
    except Exception:
        print(f"Error: Collection '{collection_name}' not found. Ingest documents first.")
        return None

    question_embedding = model.encode([question]).tolist()

    results = collection.query(
        query_embeddings=question_embedding,
        n_results=n_results,
    )

    documents = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    print("\n--- Retrieved Chunks ---\n")
    for i, (doc, dist, meta) in enumerate(zip(documents, distances, metadatas)):
        print(f"Chunk {i + 1} | Source: {meta['source']} | Distance: {dist:.4f}")
        print(textwrap.fill(doc, width=90))
        print()

    context = "\n\n".join(documents)

    system_prompt = (
        "You are a banking domain expert. Answer questions using ONLY the provided context. "
        "If the context does not contain the answer, say 'I don't have enough information to answer this.' "
        "Do not use any outside knowledge."
    )
    user_prompt = f"Context:\n\n{context}\n\nQuestion: {question}"

    try:
        claude = anthropic.Anthropic()
        response = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        answer = response.content[0].text
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return None

    print("--- RAG Answer ---\n")
    print(answer)
    return answer


if __name__ == "__main__":
    while True:
        print("\n=== RAG Engine ===")
        print("1. Ingest a document")
        print("2. Ask a question")
        print("3. Exit")

        choice = input("\nSelect an option: ").strip()

        if choice == "1":
            path = input("Enter file path: ").strip()
            if os.path.isfile(path):
                ingest_documents([path])
            else:
                print(f"File not found: {path}")
        elif choice == "2":
            question = input("Enter your question: ").strip()
            if question:
                query_rag(question)
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please choose 1, 2, or 3.")
