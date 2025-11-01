import hashlib
from pathlib import Path

def should_index(path: Path, supported_exts: set[str] | None = None) -> bool:
    if supported_exts is None:
        supported_exts = {'.txt', '.md', '.py', '.json', '.csv', '.yaml',
                          '.yml', '.html', '.xml', '.js', '.css', '.java',
                            '.c', '.cpp', '.rb', '.go', '.rs', '.php', '.sh'}

    ignored_dirs = {'node_modules', '.git', '__pycache__', 'venv', '.venv', 'env',
                    '.env', 'build', 'dist', '.idea', '.vscode'}
    ignored_files = {'.DS_Store', 'Thumbs.db'}

    return(
        path.is_file() and
        path.suffix.lower() in supported_exts and
        not any(part in ignored_dirs for part in path.parts) and
        path.name not in ignored_files
    )
    

def file_hash(path: Path, chunk_size: int = 65536) -> str | None:
    if not path.is_file():
        return None
    if (path.stat().st_size == 0) or (path.stat().st_size > 5_000_000):
        return None

    hasher = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            hasher.update(chunk)
    return hasher.hexdigest()