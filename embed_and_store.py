from sentence_transformers import SentenceTransformer
import chromadb
from build_index import build_all_chunks

# Load the free, local embedding model (downloads once, then cached)
print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# Set up Chroma — a persistent local vector database (saves to disk, not memory-only)
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection(name="code_chunks")


def embed_and_store(repo_path):
    chunks = build_all_chunks(repo_path)
    print(f"Total chunks to embed: {len(chunks)}")

    # We'll process in batches so we can show progress and avoid overload
    batch_size = 50

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]

        # Extract just the code text to embed
        texts = [c["code"] for c in batch]

        # Generate embeddings for this batch
        embeddings = model.encode(texts).tolist()

        # Unique IDs required by Chroma — combine file path + name + line number
        ids = [f"{c['file_path']}::{c['name']}::{c['start_line']}" for c in batch]

        # Metadata we want to retrieve later (file, name, type, lines)
        metadatas = [{
            "file_path": c["file_path"],
            "name": c["name"],
            "type": c["type"],
            "start_line": c["start_line"],
            "end_line": c["end_line"],
        } for c in batch]

        # Store this batch in Chroma
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        print(f"Stored batch {i // batch_size + 1} / {(len(chunks) // batch_size) + 1}")

    print("\nAll chunks embedded and stored successfully.")


if __name__ == "__main__":
    embed_and_store("cloned_repo")