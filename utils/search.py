"""
Hospital Management System — Smart Search Utility (NLP / Fuzzy Matching)
Uses rapidfuzz so users can search "Nguyen Van A" and match "Nguyễn Văn A"
"""

import unicodedata
import re

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False


def normalize_text(text: str) -> str:
    """
    Normalise Vietnamese text:
      • Remove diacritics (NFD decompose + strip combining chars)
      • Lowercase
      • Collapse whitespace
    """
    if not text:
        return ""
    nfd = unicodedata.normalize("NFD", text)
    ascii_text = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", ascii_text).strip().lower()


def fuzzy_filter(query: str, candidates: list, key_fn=None, threshold: int = 65):
    """
    Filter a list of candidates using fuzzy matching on normalised text.

    Args:
        query:      Search string (may be un-accented Vietnamese)
        candidates: List of objects or strings
        key_fn:     Function to extract comparable text from each candidate
                    (if None, candidates must be strings)
        threshold:  Minimum similarity score 0-100 (default 65)

    Returns:
        Filtered + sorted list of candidates
    """
    if not query:
        return candidates

    norm_query = normalize_text(query)

    results = []
    for item in candidates:
        text = key_fn(item) if key_fn else str(item)
        norm_text = normalize_text(text)

        # Fast substring check first (exact after normalisation)
        if norm_query in norm_text:
            results.append((item, 100))
            continue

        # Fuzzy ratio
        if RAPIDFUZZ_AVAILABLE:
            score = fuzz.partial_ratio(norm_query, norm_text)
        else:
            score = _simple_ratio(norm_query, norm_text)

        if score >= threshold:
            results.append((item, score))

    # Sort by score descending
    results.sort(key=lambda x: -x[1])
    return [item for item, _ in results]


def _simple_ratio(a: str, b: str) -> int:
    """Fallback similarity when rapidfuzz not installed."""
    if not a or not b:
        return 0
    longer = max(len(a), len(b))
    if longer == 0:
        return 100
    matches = sum(ca == cb for ca, cb in zip(a, b))
    return int(matches / longer * 100)


def smart_search_patients(query: str, patient_rows: list) -> list:
    """
    Intelligent search over patient rows (sqlite3.Row objects).
    Searches: full_name, patient_code, phone, birth_date
    """
    if not query:
        return patient_rows

    # First pass: exact / substring on raw data
    norm_q = normalize_text(query)
    exact_hits = [
        p for p in patient_rows
        if (norm_q in normalize_text(p["full_name"] or "")
            or norm_q in (p["patient_code"] or "").lower()
            or norm_q in (p["phone"] or "")
            or norm_q in (p["birth_date"] or ""))
    ]
    if exact_hits:
        return exact_hits

    # Second pass: fuzzy on full_name
    return fuzzy_filter(query, patient_rows,
                        key_fn=lambda p: p["full_name"] or "",
                        threshold=60)
