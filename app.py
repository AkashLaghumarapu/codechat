from flask import Flask, request, jsonify, render_template
from ask import ask_question
from ingest import clone_repo, get_code_files
from build_index import build_all_chunks
from sentence_transformers import SentenceTransformer
import chromadb
import os

app = Flask(__name__)

# Load the embedding model once when the server starts (not on every request)
embed_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path="chroma_db")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/load_repo", methods=["POST"])
def load_repo():
    data = request.get_json()
    repo_url = data.get("repo_url", "").strip()

    if not repo_url:
        return jsonify({"status": "error", "message": "Please enter a repo URL."})

    try:
        # Step 1: Wipe the old collection so no mismatched data remains
        try:
            chroma_client.delete_collection(name="code_chunks")
        except Exception:
            pass  # collection might not exist yet on first run — that's fine

        collection = chroma_client.get_or_create_collection(name="code_chunks")

        # Step 2: Clone the new repo
        repo_path = clone_repo(repo_url)

        # Step 3 + 4: Chunk all files in the new repo
        chunks = build_all_chunks(repo_path)

        if len(chunks) == 0:
            return jsonify({"status": "error", "message": "No Python code chunks found in this repo."})

        # Step 5: Embed and store in batches (same logic as embed_and_store.py)
        batch_size = 50
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [c["code"] for c in batch]
            embeddings = embed_model.encode(texts).tolist()
            ids = [f"{c['file_path']}::{c['name']}::{c['start_line']}" for c in batch]
            metadatas = [{
                "file_path": c["file_path"],
                "name": c["name"],
                "type": c["type"],
                "start_line": c["start_line"],
                "end_line": c["end_line"],
            } for c in batch]

            collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

        return jsonify({
            "status": "success",
            "message": f"Repo indexed successfully! {len(chunks)} code chunks loaded."
        })

    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to load repo: {str(e)}"})


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"answer": "Please enter a question."})

    try:
        answer = ask_question(question)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"answer": f"Something went wrong: {str(e)}"})


if __name__ == "__main__":
    app.run(debug=True)