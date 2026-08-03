import os
from dotenv import load_dotenv
from groq import Groq
from fastembed import TextEmbedding
import chromadb

# Load the API key from .env
load_dotenv()
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Load the same embedding model used before (must match!)
embed_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

# Connect to the same Chroma database
chroma_client = chromadb.PersistentClient(path="chroma_db")



def retrieve_chunks(question, top_k=3):
    """Search the vector database for the most relevant code chunks."""
    collection = chroma_client.get_or_create_collection(name="code_chunks")  # fetch fresh, in case it was recreated
    query_embedding = list(embed_model.embed([question]))[0].tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)

    chunks = []
    for i in range(len(results["ids"][0])):
        chunks.append({
            "code": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
        })
    return chunks


def build_prompt(question, chunks):
    """Build the prompt we send to the AI model, including retrieved code as context."""
    context_blocks = []
    for c in chunks:
        meta = c["metadata"]
        block = (
            f"File: {meta['file_path']} (lines {meta['start_line']}-{meta['end_line']})\n"
            f"```python\n{c['code']}\n```"
        )
        context_blocks.append(block)

    context_text = "\n\n".join(context_blocks)

    prompt = f"""You are a helpful assistant that explains code to developers.

Below are relevant code snippets retrieved from a codebase, each labeled with its file name and line numbers.

{context_text}

Using ONLY the code snippets above, answer this question in plain English:
"{question}"

Always mention which file and line numbers your answer is based on.
If the snippets don't contain enough information to answer, say so honestly instead of guessing."""

    return prompt


def ask_question(question):
    chunks = retrieve_chunks(question)
    prompt = build_prompt(question, chunks)

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
    )

    answer = response.choices[0].message.content
    return answer


if __name__ == "__main__":
    question = "how does the app handle sending static files"
    print(f"Question: {question}\n")

    answer = ask_question(question)
    print("Answer:\n")
    print(answer)