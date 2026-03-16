"""
Document indexing and retrieval for the CP-AM-DRILL knowledge base.

Parses the three Festo manuals into page-level chunks and provides
simple keyword-based retrieval. No vector database required — the full
corpus fits comfortably in Claude's context window for this prototype.

In production, use Amazon Bedrock Knowledge Bases or Databricks Vector
Search for semantic retrieval over larger document sets.
"""

import json
import os
import re

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "documents")
CHUNKS_FILE = os.path.join(os.path.dirname(__file__), "chunks.json")

DOC_CONFIGS = [
    {
        "filename": "operating_manual.txt",
        "doc_name": "CP-AM-DRILL Operating Manual",
        "doc_short": "Operating Manual",
    },
    {
        "filename": "maintenance_manual.txt",
        "doc_name": "CP Factory Maintenance Manual",
        "doc_short": "Maintenance Manual",
    },
    {
        "filename": "circuit_diagrams.txt",
        "doc_name": "CP-AM-DRILL Circuit Diagrams",
        "doc_short": "Circuit Diagrams",
    },
]

# High-value pages to always include for the Z-axis anomaly diagnosis
PRIORITY_PAGES = {
    "Operating Manual": {38, 39, 40, 41, 42, 44, 61, 62, 63, 64, 65, 66, 82, 83, 84, 85, 86},
    "Maintenance Manual": {4, 5, 6, 7, 8},
    "Circuit Diagrams": {16, 17},
    "Technical Notes": {1},
}


def build_chunks() -> list[dict]:
    """Parse all three document files into page-level chunks."""
    chunks = []
    page_pattern = re.compile(r"^---\s*Page\s+(\d+)\s*---\s*$", re.IGNORECASE)

    for doc_cfg in DOC_CONFIGS:
        filepath = os.path.join(DOCS_DIR, doc_cfg["filename"])
        if not os.path.exists(filepath):
            print(f"WARNING: Document not found: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            raw = f.read()

        # Split by page delimiter
        lines = raw.splitlines()
        current_page = None
        current_lines = []

        for line in lines:
            match = page_pattern.match(line.strip())
            if match:
                # Save previous page
                if current_page is not None and current_lines:
                    content = "\n".join(current_lines).strip()
                    if content:
                        chunks.append(_make_chunk(doc_cfg, current_page, content))
                current_page = int(match.group(1))
                current_lines = []
            else:
                current_lines.append(line)

        # Save final page
        if current_page is not None and current_lines:
            content = "\n".join(current_lines).strip()
            if content:
                chunks.append(_make_chunk(doc_cfg, current_page, content))

    return chunks


def _make_chunk(doc_cfg: dict, page: int, content: str) -> dict:
    # Extract section header (first non-empty line if it looks like a heading)
    first_line = content.split("\n")[0].strip()
    section = first_line if len(first_line) < 80 else ""
    return {
        "id":        f"{doc_cfg['doc_short'].lower().replace(' ', '_')}_p{page}",
        "doc_name":  doc_cfg["doc_name"],
        "doc_short": doc_cfg["doc_short"],
        "page":      page,
        "section":   section,
        "content":   content,
        "keywords":  _extract_keywords(content),
    }


def _extract_keywords(content: str) -> list[str]:
    """Extract meaningful keywords from chunk content for retrieval."""
    # Normalise to lowercase, extract alphanumeric tokens
    tokens = re.findall(r"[a-zA-Z0-9_\-]+", content.lower())
    # Filter short words and very common ones
    stopwords = {"the", "and", "for", "with", "from", "this", "that", "are", "not",
                 "can", "has", "have", "been", "will", "its", "all", "any", "each"}
    keywords = [t for t in tokens if len(t) > 3 and t not in stopwords]
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            unique.append(k)
    return unique[:50]


def save_chunks(chunks: list[dict]) -> None:
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)


def load_chunks() -> list[dict]:
    """Load chunks from cache, building the cache if it doesn't exist."""
    if not os.path.exists(CHUNKS_FILE):
        chunks = build_chunks()
        save_chunks(chunks)
        return chunks
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def retrieve_chunks(query: str, chunks: list[dict], top_k: int = 8) -> list[dict]:
    """
    Retrieve the most relevant chunks for a given query using keyword matching.

    Priority pages for the Z-axis anomaly scenario are always included.
    Remaining slots are filled by keyword overlap score.
    """
    query_terms = set(re.findall(r"[a-zA-Z0-9_\-]+", query.lower()))
    query_terms -= {"the", "and", "for", "with", "from", "this", "what", "how",
                    "does", "when", "where", "which", "should"}

    scored = []
    priority_chunks = []

    for chunk in chunks:
        short = chunk["doc_short"]
        is_priority = (short in PRIORITY_PAGES and chunk["page"] in PRIORITY_PAGES[short])
        if is_priority:
            priority_chunks.append(chunk)
            continue
        kw_set = set(chunk["keywords"])
        score = len(query_terms & kw_set)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_by_score = [c for _, c in scored[:max(0, top_k - len(priority_chunks))]]

    # Merge priority + scored, deduplicate by id
    seen_ids = set()
    result = []
    for chunk in priority_chunks + top_by_score:
        if chunk["id"] not in seen_ids:
            seen_ids.add(chunk["id"])
            result.append(chunk)

    return result[:top_k]


def rebuild_index() -> list[dict]:
    """Force-rebuild the chunk index from source documents."""
    chunks = build_chunks()
    save_chunks(chunks)
    return chunks
