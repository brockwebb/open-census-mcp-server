"""RAG Retriever for Ablation Experiment.

Retrieves relevant chunks from FAISS index for the RAG condition.
Used by generate_responses.py to augment the system prompt with retrieved context.
"""

import json
from pathlib import Path
from typing import Dict, List, Any

# Lazy imports for optional dependencies
def lazy_imports():
    """Import heavy dependencies only when needed."""
    global SentenceTransformer, faiss
    from sentence_transformers import SentenceTransformer
    import faiss
    return SentenceTransformer, faiss


class RAGRetriever:
    """Retrieves relevant document chunks for query augmentation.

    Uses FAISS for efficient similarity search over embedded document chunks.
    Returns formatted context suitable for system prompt injection.
    """

    def __init__(self, index_dir: str, top_k: int = 5):
        """Initialize retriever.

        Args:
            index_dir: Path to directory containing faiss_index.bin and chunks.jsonl
            top_k: Number of chunks to retrieve (default: 5)
        """
        SentenceTransformer, faiss = lazy_imports()

        self.index_dir = Path(index_dir)
        self.top_k = top_k

        # Load embedding model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

        # Load FAISS index
        index_path = self.index_dir / 'faiss_index.bin'
        if not index_path.exists():
            raise FileNotFoundError(f"FAISS index not found: {index_path}")
        self.index = faiss.read_index(str(index_path))

        # Load chunks
        chunks_path = self.index_dir / 'chunks.jsonl'
        if not chunks_path.exists():
            raise FileNotFoundError(f"Chunks file not found: {chunks_path}")

        self.chunks = []
        with open(chunks_path) as f:
            for line in f:
                self.chunks.append(json.loads(line))

        # Load metadata
        metadata_path = self.index_dir / 'metadata.json'
        if metadata_path.exists():
            with open(metadata_path) as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}

        print(f"RAGRetriever initialized:")
        print(f"  Index: {index_path}")
        print(f"  Chunks: {len(self.chunks)}")
        print(f"  Top-k: {top_k}")

    def retrieve(self, query: str) -> Dict[str, Any]:
        """Retrieve relevant chunks for a query.

        Args:
            query: User query text

        Returns:
            Dictionary with:
            - context_text: Formatted text for system prompt injection
            - retrieved_chunks: List of chunk metadata (chunk_id, score, source, etc.)
            - total_context_chars: Total characters in retrieved context
        """
        SentenceTransformer, faiss = lazy_imports()

        # Embed query
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)

        # Search index
        scores, indices = self.index.search(query_embedding, self.top_k)

        # Format results
        retrieved = []
        context_parts = []

        for i, idx in enumerate(indices[0]):
            if idx >= len(self.chunks):
                # Should not happen, but guard against index mismatch
                continue

            chunk = self.chunks[idx]
            score = float(scores[0][i])

            # Store metadata about retrieved chunk
            retrieved.append({
                'chunk_id': chunk.get('chunk_id', idx),
                'score': score,
                'source': chunk.get('source', 'unknown'),
                'page': chunk.get('page'),
                'section': chunk.get('section'),
                'text_length': len(chunk['text'])
            })

            # Format chunk for prompt injection
            source_label = chunk.get('source', 'unknown')
            page_label = f", p. {chunk['page']}" if chunk.get('page') else ""
            section_label = f", Section: {chunk['section']}" if chunk.get('section') else ""

            context_parts.append(
                f"[Source: {source_label}{page_label}{section_label}]\n"
                f"{chunk['text']}"
            )

        # Join chunks with clear separators
        context_text = "\n\n---\n\n".join(context_parts)

        return {
            'context_text': context_text,
            'retrieved_chunks': retrieved,
            'total_context_chars': sum(r['text_length'] for r in retrieved),
            'retrieval_config': {
                'top_k': self.top_k,
                'embedding_model': self.metadata.get('embedding_model', 'all-MiniLM-L6-v2')
            }
        }

    def format_system_prompt(self, base_prompt: str, query: str) -> tuple[str, Dict[str, Any]]:
        """Format system prompt with retrieved context.

        Args:
            base_prompt: Base system prompt (same as control condition)
            query: User query text

        Returns:
            (augmented_prompt, retrieval_metadata)
        """
        retrieval = self.retrieve(query)

        augmented_prompt = (
            f"{base_prompt}\n\n"
            f"## Reference Materials\n\n"
            f"The following excerpts from Census methodology documentation may be relevant:\n\n"
            f"{retrieval['context_text']}\n\n"
            f"Use these materials to inform your response where applicable."
        )

        return augmented_prompt, retrieval
