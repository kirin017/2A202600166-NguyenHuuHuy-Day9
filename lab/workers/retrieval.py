"""
workers/retrieval.py — Retrieval Worker
Sprint 2: Implement dense retrieval với ChromaDB và OpenAI embeddings.
"""

import os
import chromadb
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()
WORKER_NAME = "retrieval_worker"
DEFAULT_TOP_K = 3

def _get_embedding_fn():
    """
    Trả về embedding function dùng OpenAI.
    """
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    def embed(text: str) -> list:
        # Sử dụng model text-embedding-3-small mặc định của ChromaDB nếu không spec
        resp = client.embeddings.create(input=text, model="text-embedding-3-small")
        return resp.data[0].embedding
    return embed

def _get_collection():
    """
    Kết nối ChromaDB collection.
    """
    client = chromadb.PersistentClient(path="./chroma_db")
    try:
        collection = client.get_collection("day09_docs")
        return collection
    except Exception as e:
        print(f"⚠️  Error getting collection: {e}")
        return None

def retrieve_dense(query: str, top_k: int = DEFAULT_TOP_K) -> List[Dict[str, Any]]:
    """
    Dense retrieval: embed query → query ChromaDB → trả về top_k chunks.
    """
    embed_fn = _get_embedding_fn()
    query_embedding = embed_fn(query)
    
    collection = _get_collection()
    if not collection:
        return []
        
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "distances", "metadatas"]
        )
        
        chunks = []
        if results["documents"]:
            for i in range(len(results["documents"][0])):
                chunks.append({
                    "text": results["documents"][0][i],
                    "source": results["metadatas"][0][i].get("source", "unknown"),
                    "score": round(1 - results["distances"][0][i], 4),
                    "metadata": results["metadatas"][0][i]
                })
        return chunks
    except Exception as e:
        print(f"⚠️  Retrieval error: {e}")
        return []

def run(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Worker entry point.
    """
    task = state.get("task", "")
    top_k = state.get("retrieval_top_k", DEFAULT_TOP_K)
    
    # Copy relevant state parts to avoid side effects if needed, 
    # but here we return a dict to be merged.
    
    chunks = retrieve_dense(task, top_k=top_k)
    sources = list({c["source"] for c in chunks})
    
    worker_io = {
        "worker": WORKER_NAME,
        "input": {"task": task, "top_k": top_k},
        "output": {"chunks_count": len(chunks), "sources": sources},
        "timestamp": os.getlogin() if hasattr(os, 'getlogin') else 'system'
    }
    
    # Return ONLY the keys that need to be updated in AgentState
    return {
        "retrieved_chunks": chunks,
        "retrieved_sources": sources,
        "worker_io_logs": state.get("worker_io_logs", []) + [worker_io]
    }

if __name__ == "__main__":
    # Simple test
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-key-here")
    res = run({"task": "SLA P1 là bao lâu?"})
    print(f"Retrieved {len(res['retrieved_chunks'])} chunks")
    for c in res['retrieved_chunks']:
        print(f"- {c['source']}: {c['text'][:50]}...")
