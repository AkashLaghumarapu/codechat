from ingest import clone_repo, get_code_files
from chunker import chunk_python_file, chunk_generic_file
import os

def build_all_chunks(repo_path):
    """
    Loops through every code file in the repo.
    Python files get smart function/class chunking.
    All other code files get generic fixed-size line chunking,
    so no repo ever ends up with zero usable chunks.
    """
    all_files = get_code_files(repo_path)
    all_chunks = []

    for file_path in all_files:
        ext = os.path.splitext(file_path)[1]

        if ext == ".py":
            file_chunks = chunk_python_file(file_path)
        else:
            file_chunks = chunk_generic_file(file_path)

        all_chunks.extend(file_chunks)

    return all_chunks


if __name__ == "__main__":
    repo_path = "cloned_repo"
    chunks = build_all_chunks(repo_path)

    print(f"Total chunks created: {len(chunks)}\n")
    for c in chunks[:5]:
        print(f"[{c['type']}] {c['name']}  |  {c['file_path']}  (lines {c['start_line']}-{c['end_line']})")