from pathlib import Path
import re

KNOWLEDGE_FOLDER = Path("scam_docs")


def tokenize(text):
    """
    Convert text into simple searchable words.
    """
    return set(
        re.findall(r"[a-zA-Z0-9]+", text.lower())
    )


def retrieve(query, top_k=3):
    """
    Search approved scam knowledge files and return
    the most relevant records.
    """

    query_words = tokenize(query)

    results = []

    for file_path in KNOWLEDGE_FOLDER.glob("*.txt"):

        document = file_path.read_text(encoding="utf-8")

        document_words = tokenize(document)

        matching_words = query_words.intersection(document_words)

        score = len(matching_words)

        results.append({
            "source": file_path.name,
            "score": score,
            "matched_terms": sorted(list(matching_words)),
            "content": document
        })

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:top_k]
