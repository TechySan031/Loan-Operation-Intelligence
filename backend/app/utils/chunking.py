"""
Text Chunking Strategies (Q2)

Implements category-aware chunking for knowledge base content.

Strategy by document type:
- FAQ entries: 1 FAQ = 1 chunk (atomic, no splitting)
- Policy docs: 300-500 tokens, 50 token overlap
- Objection scripts: 1 objection = 1 chunk (atomic)
- Product info: 400-600 tokens, 75 token overlap
- Compliance rules: 200-400 tokens, 50 token overlap

Uses tiktoken for accurate token counting.
"""

import logging
import tiktoken

logger = logging.getLogger(__name__)

# Token counting
ENCODER = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding


# Chunk size configuration per category
CHUNK_CONFIG = {
    "faq": {"max_tokens": 500, "overlap_tokens": 0, "atomic": True},
    "objection": {"max_tokens": 500, "overlap_tokens": 0, "atomic": True},
    "escalation": {"max_tokens": 400, "overlap_tokens": 0, "atomic": True},
    "policy": {"max_tokens": 400, "overlap_tokens": 50, "atomic": False},
    "product": {"max_tokens": 500, "overlap_tokens": 75, "atomic": False},
    "compliance": {"max_tokens": 300, "overlap_tokens": 50, "atomic": False},
    "payment": {"max_tokens": 400, "overlap_tokens": 50, "atomic": False},
}

DEFAULT_CONFIG = {"max_tokens": 400, "overlap_tokens": 50, "atomic": False}


def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken."""
    return len(ENCODER.encode(text))


def chunk_text(text: str, category: str = "default") -> list[dict]:
    """
    Chunk text based on category-specific strategy.
    
    Args:
        text: Text to chunk
        category: KB category (faq, policy, product, etc.)
    
    Returns:
        List of chunk dicts: [{text, token_count, chunk_index}]
    """
    config = CHUNK_CONFIG.get(category, DEFAULT_CONFIG)
    
    # Atomic categories: return as-is (1 record = 1 chunk)
    if config["atomic"]:
        return [{
            "text": text.strip(),
            "token_count": count_tokens(text),
            "chunk_index": 0,
        }]
    
    # Split into chunks with overlap
    max_tokens = config["max_tokens"]
    overlap_tokens = config["overlap_tokens"]
    
    # Split by paragraphs first for natural boundaries
    paragraphs = text.split("\n\n")
    
    chunks = []
    current_chunk = ""
    current_tokens = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        para_tokens = count_tokens(para)
        
        # If single paragraph exceeds max, force-split by sentences
        if para_tokens > max_tokens:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
                current_tokens = 0
            
            sentence_chunks = _split_by_sentences(para, max_tokens, overlap_tokens)
            chunks.extend(sentence_chunks)
            continue
        
        # Add paragraph to current chunk if it fits
        if current_tokens + para_tokens <= max_tokens:
            current_chunk += "\n\n" + para if current_chunk else para
            current_tokens += para_tokens
        else:
            # Save current chunk, start new one
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # Apply overlap: include tail of previous chunk
            if overlap_tokens > 0 and chunks:
                overlap_text = _get_overlap(chunks[-1], overlap_tokens)
                current_chunk = overlap_text + "\n\n" + para
                current_tokens = count_tokens(current_chunk)
            else:
                current_chunk = para
                current_tokens = para_tokens
    
    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # Format output
    return [
        {
            "text": chunk,
            "token_count": count_tokens(chunk),
            "chunk_index": i,
        }
        for i, chunk in enumerate(chunks)
    ]


def _split_by_sentences(text: str, max_tokens: int, overlap_tokens: int) -> list[str]:
    """Split text by sentence boundaries when paragraphs are too large."""
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current = ""
    current_tokens = 0
    
    for sentence in sentences:
        sent_tokens = count_tokens(sentence)
        if current_tokens + sent_tokens <= max_tokens:
            current += " " + sentence if current else sentence
            current_tokens += sent_tokens
        else:
            if current:
                chunks.append(current.strip())
            current = sentence
            current_tokens = sent_tokens
    
    if current.strip():
        chunks.append(current.strip())
    
    return chunks


def _get_overlap(text: str, overlap_tokens: int) -> str:
    """Get the last N tokens of text as overlap."""
    tokens = ENCODER.encode(text)
    overlap = tokens[-overlap_tokens:] if len(tokens) > overlap_tokens else tokens
    return ENCODER.decode(overlap)
