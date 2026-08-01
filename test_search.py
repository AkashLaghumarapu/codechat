from sentence_transformers import SentenceTransformer
import chromadb

# Load the same model used for storing (must match!)
model = SentenceTransformer("all-MiniLM-L6-v2")

# Connect to the same Chroma database we just built
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection(name="code_chunks")


def search(query, top_k=3):
    # Convert the question into an embedding, same way we embedded the code
    query_embedding = model.encode([query]).tolist()

    # Ask Chroma for the most similar chunks
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )

    print(f"\nTop {top_k} results for: \"{query}\"\n")
    for i in range(len(results["ids"][0])):
        meta = results["metadatas"][0][i]
        distance = results["distances"][0][i]
        print(f"{i+1}. [{meta['type']}] {meta['name']}  |  {meta['file_path']}  "
              f"(lines {meta['start_line']}-{meta['end_line']})  |  distance: {distance:.4f}")


if __name__ == "__main__":
    search("how does the app handle sending static files")