"""
Text and offset utilities for BrandProof Review Engine.

All persisted and transmitted finding offsets in BrandProof are standardized as
zero-based, half-open UTF-16 code-unit offsets [start_offset, end_offset).

This guarantees exact 1:1 compatibility with JavaScript:
    contentText.substring(start_offset, end_offset)
extracts the exact finding claim text, even when the content contains
supplementary characters (such as emojis outside the Basic Multilingual Plane),
Indic scripts (e.g., Tamil), or accented characters.
"""
from typing import Tuple


def codepoint_to_utf16_offset(text: str, codepoint_index: int) -> int:
    """
    Convert a 0-based Python Unicode codepoint index to a 0-based UTF-16 code-unit offset.

    Compatible with JavaScript String.prototype.substring(start, end) and String.prototype.length.
    - Characters in the Basic Multilingual Plane (BMP, <= U+FFFF) use 1 UTF-16 code unit.
    - Characters outside the BMP (> U+FFFF, e.g. surrogate pairs like 🚀, 🔬) use 2 code units.
    """
    if codepoint_index <= 0:
        return 0
    if codepoint_index >= len(text):
        return sum(2 if ord(ch) > 0xFFFF else 1 for ch in text)
    return sum(2 if ord(ch) > 0xFFFF else 1 for ch in text[:codepoint_index])


def utf16_to_codepoint_offset(text: str, utf16_offset: int) -> int:
    """
    Convert a 0-based UTF-16 code-unit offset back to a 0-based Python Unicode codepoint index.
    """
    if utf16_offset <= 0:
        return 0
    current_units = 0
    for idx, ch in enumerate(text):
        if current_units >= utf16_offset:
            return idx
        current_units += 2 if ord(ch) > 0xFFFF else 1
    return len(text)


def match_to_utf16_offsets(text: str, match_start: int, match_end: int) -> Tuple[int, int]:
    """
    Convert Python regex or string search match positions into zero-based,
    half-open UTF-16 code-unit offsets [start_offset, end_offset).

    Args:
        text: The source string searched.
        match_start: Python codepoint start index (e.g., match.start()).
        match_end: Python codepoint end index (e.g., match.end()).

    Returns:
        Tuple of (start_offset, end_offset) in UTF-16 code units.

    Raises:
        ValueError: If match_start < 0, match_start >= match_end, or match_end > len(text).
    """
    if match_start < 0:
        raise ValueError(f"match_start cannot be negative: {match_start}")
    if match_end > len(text):
        raise ValueError(f"match_end ({match_end}) cannot exceed text length ({len(text)})")
    if match_start >= match_end:
        raise ValueError(f"match_start ({match_start}) must be strictly less than match_end ({match_end})")

    start_utf16 = codepoint_to_utf16_offset(text, match_start)
    end_utf16 = codepoint_to_utf16_offset(text, match_end)
    return start_utf16, end_utf16


def extract_utf16_substring(text: str, start_offset: int, end_offset: int) -> str:
    """
    Extract a substring using zero-based, half-open UTF-16 code-unit offsets [start_offset, end_offset).
    Behaves identically to JavaScript's `text.substring(start_offset, end_offset)`.
    """
    if start_offset < 0:
        start_offset = 0
    total_utf16 = codepoint_to_utf16_offset(text, len(text))
    if end_offset > total_utf16:
        end_offset = total_utf16
    if start_offset >= end_offset:
        return ""

    utf16_bytes = text.encode("utf-16-le")
    byte_start = start_offset * 2
    byte_end = end_offset * 2
    return utf16_bytes[byte_start:byte_end].decode("utf-16-le", errors="replace")
