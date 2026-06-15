import tiktoken

_enc = tiktoken.get_encoding("cl100k_base")


def split_into_chunks(text: str, max_tokens: int = 500, overlap: int = 50) -> list[dict]:
    tokens = _enc.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append({
            "text": _enc.decode(chunk_tokens),
            "token_count": len(chunk_tokens),
        })
        start += max_tokens - overlap
    return chunks
