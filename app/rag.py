"""
RAG over the insurance brochure.

Lightweight, dependency-free retrieval — uses character-overlap scoring plus
keyword bonuses. This is intentional: for a brochure split into ~203 snippets
across 17 sections, a simple BM25-ish scorer is faster, deterministic, and
easier to audit than spinning up sentence-transformers / FAISS.

In production we'd swap this for sarvam-embed (when available) or a small
sentence-transformers index.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

BROCHURE_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_insurance_policy.txt"


@dataclass
class Snippet:
    id: str
    section: str
    text: str

    def short(self, n: int = 220) -> str:
        return self.text if len(self.text) <= n else self.text[:n].rsplit(" ", 1)[0] + "…"


def _split_into_snippets(raw: str) -> List[Snippet]:
    """Split brochure into snippets by blank line, tag with nearest SECTION header.

    Handles the document format where section headers are wrapped in ---- dividers:
        ------------
        SECTION 1 — ELIGIBILITY
        ------------
    The first line of such a block is the dashes, so we search the whole block
    for a section tag rather than only inspecting the first line.

    Edge case: sometimes the document has no blank line between the closing ----
    divider and the first paragraph of content (especially for sections with dense
    bullet lists). In that case the header and content land in the same block.
    We detect this and salvage the trailing content rather than skipping the whole block.
    """
    current_section = "GENERAL"
    snippets: list[Snippet] = []
    blocks = [b.strip() for b in re.split(r"\n\s*\n", raw) if b.strip()]

    # Patterns that mark a block as a section header (not content)
    _SECTION_RE = re.compile(r"SECTION\s+\d+\s+[—–-]+\s*(.+)", re.IGNORECASE)
    _NAMED_HDR_RE = re.compile(
        r"^-{10,}\s*\n([A-Z][A-Z\s]+(?:\(.+\))?)\s*\n-{10,}$", re.MULTILINE
    )
    _DIVIDER_RE = re.compile(r"-{10,}")

    def _add_content_block(block_text: str, block_idx: int, section: str) -> None:
        """Parse a content block into sub-snippets and add to snippets list."""
        # Split on bullet-list boundaries and numbered-list boundaries so each
        # snippet is a tight, scoreable cluster.  Splitting numbered items (e.g.
        # "1. For planned..." → "2. For emergencies...") prevents long claim-process
        # blocks from being penalised by the length-penalty factor.
        sub_blocks = re.split(r"\n(?=- |\d+\. )", block_text)
        for j, sb in enumerate(sub_blocks):
            sb = sb.strip()
            if len(sb) < 30 or re.match(r"^-{5,}$", sb):
                continue
            if re.match(r"^-{5,}\s*\n\w", sb) or "SECTION" in sb.upper()[:20]:
                continue
            snippets.append(
                Snippet(
                    id=f"s{block_idx:02d}_{j:02d}",
                    section=section,
                    text=sb,
                )
            )

    for i, block in enumerate(blocks):
        # Check if this block is a section header
        m = _SECTION_RE.search(block)
        if m:
            current_section = m.group(1).strip()
            # Remove trailing parenthetical (e.g. "(use for fast pitch matching)")
            current_section = re.sub(r"\s*\(.+\)$", "", current_section).strip()

            # Salvage content that is merged into the same block as the header.
            # The header structure is: ----\nSECTION N — NAME\n----\n[content]
            # Split on ---- dividers; everything after the 2nd divider is content.
            parts = _DIVIDER_RE.split(block)
            # parts[0] = "" (before first ----), parts[1] = section name line,
            # parts[2+] = content lines (if any got merged in)
            if len(parts) >= 3:
                trailing = "\n".join(p for p in parts[2:]).strip()
                if trailing and len(trailing) >= 30:
                    _add_content_block(trailing, i, current_section)
            continue

        # Named header blocks (all-caps + dash dividers, no real content)
        if _NAMED_HDR_RE.match(block) or re.match(r"^-{10,}$", block):
            continue

        # Skip pure divider lines
        clean = re.sub(r"-{5,}", "", block).strip()
        if len(clean) < 30:
            continue

        _add_content_block(block, i, current_section)

    return snippets


class BrochureRAG:
    def __init__(self, brochure_path: Path = BROCHURE_PATH):
        self.brochure_path = brochure_path
        self.snippets: list[Snippet] = []
        self._load()

    def _load(self) -> None:
        if not self.brochure_path.exists():
            self.snippets = []
            return
        raw = self.brochure_path.read_text(encoding="utf-8")
        self.snippets = _split_into_snippets(raw)

    def retrieve(self, query: str, k: int = 3, min_score: float = 1.5) -> list[Snippet]:
        """Retrieve the top-k snippets most relevant to the query.

        min_score acts as a relevance gate: snippets scoring below it are
        discarded entirely. This prevents weakly-matched out-of-scope queries
        (e.g. "car insurance", "motor vehicle") from returning irrelevant
        snippets that could mislead the LLM.

        Threshold of 1.5 is calibrated for short voice queries (3–6 words):
          - Genuine health-insurance queries typically score 1.5–8+
          - Pure out-of-scope queries (car, motor vehicle) score near 0
          - Borderline queries like "term life insurance" may return a tangentially
            related snippet; the LLM system-prompt guardrail restricts claims to
            retrieved snippets only.
        """
        if not self.snippets:
            return []
        q_tokens = _tokenize(query)
        if not q_tokens:
            return []
        q_set = set(q_tokens)
        scored: list[tuple[float, Snippet]] = []
        for s in self.snippets:
            s_tokens = _tokenize(s.text)
            if not s_tokens:
                continue
            s_set = set(s_tokens)
            overlap = len(q_set & s_set)
            if overlap == 0:
                continue
            # IDF-ish bonus for less-common matches
            uncommon_bonus = sum(1 for w in (q_set & s_set) if w not in _STOPWORDS)
            length_penalty = 1.0 / (1.0 + len(s_tokens) / 80.0)
            score = (overlap + 1.5 * uncommon_bonus) * length_penalty
            if score >= min_score:
                scored.append((score, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:k]]

    def format_for_prompt(self, snippets: list[Snippet]) -> str:
        """Format snippets for injection into the LLM system prompt.

        IDs are intentionally excluded here — the LLM doesn't need them and
        will occasionally echo citation tags like [s57_00] verbatim into its
        reply, which TTS then reads aloud. The UI source citations use the
        original Snippet objects directly, so nothing is lost.
        """
        if not snippets:
            return "(no relevant brochure snippets found)"
        return "\n\n".join(f"[{s.section}] {s.text}" for s in snippets)


# --------------------------- helpers ---------------------------

_WORD_RE = re.compile(r"[a-zA-Z]+(?:'[a-zA-Z]+)?|\d+")
_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "to", "of", "in", "on", "for",
    "and", "or", "with", "this", "that", "it", "as", "by", "at", "from", "i", "you",
    "we", "they", "what", "how", "do", "does", "can", "could", "should", "would", "will",
    "ka", "ki", "ke", "se", "ko", "mein", "hai", "hain", "ho", "kya", "mujhe",
}


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _WORD_RE.findall(text)]
