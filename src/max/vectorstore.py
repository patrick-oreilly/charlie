import os
import json
from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .utils import should_index, file_hash

def build_or_load_vectorstore(project_path: str):
    # Define new directory name
    CHARLIE_INDEX_DIR = ".charlie_index"
    old_dir = os.path.join(project_path, ".codeflow_index")
    new_dir = os.path.join(project_path, CHARLIE_INDEX_DIR)

    # Migration: Move old directory if it exists
    if os.path.exists(old_dir) and not os.path.exists(new_dir):
        import shutil
        print("Migrating index from .codeflow_index to .charlie_index...")
        shutil.move(old_dir, new_dir)

    persist_dir = new_dir
    meta_path = os.path.join(persist_dir, "index_meta.json")
    os.makedirs(persist_dir, exist_ok=True)

    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)

    # Load existing metadata
    old_meta = {}
    if Path(meta_path).exists():
        try:
            old_meta = json.loads(Path(meta_path).read_text())
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not load index metadata: {e}")

    new_docs = []
    new_meta = {}

    print("Scanning project files...")
    for file_path in Path(project_path).rglob("*"):
        if not should_index(file_path):
            continue

        current_hash = file_hash(file_path)
        file_key = str(file_path.resolve())

        if file_key in old_meta and old_meta[file_key] == current_hash:
            continue  # Unchanged

        try:
            loader = TextLoader(str(file_path), encoding="utf-8")
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = file_key
            new_docs.extend(docs)
            new_meta[file_key] = current_hash
        except (FileNotFoundError, PermissionError) as e:
            # Silently skip files that don't exist or we can't read
            pass
        except UnicodeDecodeError as e:
            # Skip binary files
            pass
        except OSError as e:
            print(f"Warning: Could not read {file_path}: {e}")
        except Exception as e:
            # Log unexpected errors for debugging
            print(f"Error loading {file_path}: {e}")

    # Build or update
    if new_docs:
        print(f"Indexing {len(new_docs)} changed files...")
        chunks = splitter.split_documents(new_docs)
        vectorstore = Chroma.from_documents(
            chunks, embeddings, persist_directory=persist_dir
        )
        print(f"Indexed {len(chunks)} chunks.")
    else:
        # Check if this is first run (no existing index database)
        index_db_file = Path(persist_dir) / "chroma.sqlite3"
        if not index_db_file.exists():
            print("No files to index. Creating empty vectorstore.")
            # Create empty vectorstore for first run
            vectorstore = Chroma(
                persist_directory=persist_dir,
                embedding_function=embeddings
            )
        else:
            print("No changes detected. Loading existing index.")
            vectorstore = Chroma(
                persist_directory=persist_dir,
                embedding_function=embeddings
            )

    # Save meta - merge old and new metadata
    old_meta.update(new_meta)
    Path(meta_path).write_text(json.dumps(old_meta, indent=2))
    return vectorstore