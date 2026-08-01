import ast
import os


def chunk_python_file(file_path):
    """
    Reads a single .py file and splits it into chunks:
    - top-level functions -> one chunk each
    - classes -> each method inside becomes its own chunk (tagged with class name)
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        source_code = f.read()

    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []

    source_lines = source_code.splitlines()
    chunks = []

    def extract_code(node):
        start_line = node.lineno
        end_line = node.end_lineno
        return "\n".join(source_lines[start_line - 1:end_line])

    # Only walk TOP-LEVEL nodes in the file (not ast.walk, which goes too deep automatically)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            chunks.append({
                "file_path": file_path,
                "name": node.name,
                "type": "function",
                "start_line": node.lineno,
                "end_line": node.end_lineno,
                "code": extract_code(node),
            })

        elif isinstance(node, ast.ClassDef):
            # Instead of treating the whole class as 1 chunk,
            # go one level in and chunk each method separately
            for sub_node in node.body:
                if isinstance(sub_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    chunks.append({
                        "file_path": file_path,
                        "name": f"{node.name}.{sub_node.name}",  # e.g. Flask.run
                        "type": "method",
                        "start_line": sub_node.lineno,
                        "end_line": sub_node.end_lineno,
                        "code": extract_code(sub_node),
                    })

    return chunks


if __name__ == "__main__":
    test_file = "cloned_repo/src/flask/app.py"
    chunks = chunk_python_file(test_file)

    print(f"Found {len(chunks)} chunks in {test_file}\n")
    for c in chunks[:10]:
        print(f"[{c['type']}] {c['name']}  (lines {c['start_line']}-{c['end_line']})")

def chunk_generic_file(file_path, lines_per_chunk=40):
    """
    Fallback chunker for any non-Python file (.sql, .js, .java, .md, etc.).
    Splits the file into fixed-size line chunks instead of function-aware chunks,
    since we don't have a syntax parser for every possible language.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return []

    chunks = []
    for i in range(0, len(lines), lines_per_chunk):
        chunk_lines = lines[i:i + lines_per_chunk]
        code_snippet = "".join(chunk_lines)

        if not code_snippet.strip():
            continue  # skip empty chunks (blank sections of a file)

        chunks.append({
            "file_path": file_path,
            "name": f"lines_{i+1}-{i+len(chunk_lines)}",
            "type": "generic_block",
            "start_line": i + 1,
            "end_line": i + len(chunk_lines),
            "code": code_snippet,
        })

    return chunks