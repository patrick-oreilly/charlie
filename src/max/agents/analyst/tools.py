from typing import Dict, Any

def search_codebase(query: str) -> Dict[str, Any]:
    """
    Search the codebase using vector similarity.
    
    Args:
        query: What to search for in the codebase
    
    Returns:
        Relevant code snippets with file paths
    """
    from ...vectorstore import build_or_load_vectorstore
    
    # Get project path from context or use default
    vectorstore = build_or_load_vectorstore(".")
    results = vectorstore.similarity_search(query, k=5)
    
    return {
        "status": "success",
        "results": [
            {
                "file": doc.metadata.get("source", "unknown"),
                "content": doc.page_content
            }
            for doc in results
        ],
        "count": len(results)
    }