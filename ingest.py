import os
import shutil
from git import Repo

# Folder where we'll temporarily store cloned repos
CLONE_DIR = "cloned_repo"

# File extensions we consider "real code"
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
    ".go", ".rb", ".php", ".cs", ".html", ".css", ".md",
    ".sql", ".json", ".yaml", ".yml", ".sh", ".xml", ".kt", ".swift"
}
# Folders we NEVER want to look inside
IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", "venv", "env",
    "dist", "build", ".next", ".vscode", "vendor"
}


import stat

def _remove_readonly(func, path, excinfo):
    """Error handler for shutil.rmtree — clears the read-only flag and retries."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def clone_repo(github_url):
    """Clones a GitHub repo into a local folder. Deletes old clone if it exists."""
    if os.path.exists(CLONE_DIR):
        shutil.rmtree(CLONE_DIR, onerror=_remove_readonly)  # handle Windows read-only .git files
    print(f"Cloning {github_url} ...")
    Repo.clone_from(github_url, CLONE_DIR)
    print("Clone complete.")
    return CLONE_DIR


def get_code_files(base_path):
    """Walks through the cloned repo and returns a list of real code file paths."""
    code_files = []

    for root, dirs, files in os.walk(base_path):
        # Remove ignored directories IN PLACE so os.walk skips them entirely
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            ext = os.path.splitext(file)[1]  # e.g. ".py"
            if ext in CODE_EXTENSIONS:
                full_path = os.path.join(root, file)
                code_files.append(full_path)

    return code_files


if __name__ == "__main__":
    # TEMP TEST — replace with any small public repo URL to test
    test_url = "https://github.com/pallets/flask.git"

    repo_path = clone_repo(test_url)
    files = get_code_files(repo_path)

    print(f"\nFound {len(files)} code files:")
    for f in files:
        print(f)