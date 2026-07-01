# backend/rag/chunker.py
"""
Hierarchical statute-aware chunker.
Splits Indian legal text by Act → Chapter → Section → Sub-clause
instead of blind token windows. This is Contribution 1 of the paper.
"""
import re
from dataclasses import dataclass, field


@dataclass
class StatuteChunk:
    chunk_id: str          # e.g. "IPC_CH2_S302"
    act: str               # "IPC" | "BNS" | "CrPC"
    chapter: str           # "Chapter II"
    section: str           # "Section 302"
    sub_clause: str        # "(1)(a)" or ""
    title: str             # "Punishment for murder"
    text: str              # full text of this unit
    metadata: dict = field(default_factory=dict)


# ── Regex patterns for Indian statute structure ──────────────────────────────

CHAPTER_RE = re.compile(
    r"(CHAPTER\s+[IVXLCDM\d]+[\.\-]?\s*[^\n]*)", re.IGNORECASE
)
SECTION_RE = re.compile(
    r"(Section\s+\d+[A-Z]?[\.\-]?\s*[^\n]*\.?)", re.IGNORECASE
)
SUB_CLAUSE_RE = re.compile(
    r"(\(\s*\d+\s*\)|\(\s*[a-z]\s*\))"
)


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_section_title(section_header: str) -> str:
    """Pull human-readable title from section header line."""
    title = re.sub(r"Section\s+\d+[A-Z]?[\.\-]?\s*", "", section_header, flags=re.IGNORECASE)
    return _clean(title).rstrip(".")


def chunk_statute(raw_text: str, act_name: str) -> list[StatuteChunk]:
    """
    Parse a full statute text into structured StatuteChunk objects.
    Each chunk is one Section (or Sub-clause if the section is long).
    """
    chunks: list[StatuteChunk] = []
    current_chapter = "Preamble"
    chunk_counter = 0

    # Split by section boundaries
    parts = SECTION_RE.split(raw_text)

    i = 0
    while i < len(parts):
        part = parts[i]

        # Update current chapter if this part contains a chapter header
        chapter_match = CHAPTER_RE.search(part)
        if chapter_match:
            current_chapter = _clean(chapter_match.group(1))

        # If this is a section header (odd index after split)
        if SECTION_RE.match(part.strip()) and i + 1 < len(parts):
            section_header = _clean(part)
            section_body = _clean(parts[i + 1])
            section_title = _extract_section_title(section_header)

            # Extract section number for the ID
            sec_num_match = re.search(r"\d+[A-Z]?", section_header)
            sec_num = sec_num_match.group() if sec_num_match else str(chunk_counter)

            # If body is short (<600 chars): keep as one chunk
            if len(section_body) < 600:
                chunk_id = f"{act_name}_S{sec_num}"
                chunks.append(StatuteChunk(
                    chunk_id=chunk_id,
                    act=act_name,
                    chapter=current_chapter,
                    section=section_header,
                    sub_clause="",
                    title=section_title,
                    text=f"{section_header}\n{section_body}",
                    metadata={"source": act_name, "section_num": sec_num},
                ))
            else:
                # Split long sections into sub-clauses
                sub_parts = SUB_CLAUSE_RE.split(section_body)
                sub_idx = 0
                j = 0
                while j < len(sub_parts):
                    sub = sub_parts[j]
                    if SUB_CLAUSE_RE.match(sub.strip()) and j + 1 < len(sub_parts):
                        clause_label = sub.strip()
                        clause_text = _clean(sub_parts[j + 1])
                        chunk_id = f"{act_name}_S{sec_num}_{sub_idx}"
                        chunks.append(StatuteChunk(
                            chunk_id=chunk_id,
                            act=act_name,
                            chapter=current_chapter,
                            section=section_header,
                            sub_clause=clause_label,
                            title=f"{section_title} {clause_label}",
                            text=f"{section_header} {clause_label}\n{clause_text}",
                            metadata={"source": act_name, "section_num": sec_num},
                        ))
                        sub_idx += 1
                        j += 2
                    else:
                        j += 1

            chunk_counter += 1
            i += 2  # skip the body we just consumed
        else:
            i += 1

    return chunks