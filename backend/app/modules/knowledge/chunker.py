import re
from dataclasses import dataclass, field


@dataclass
class ChunkOutput:
    chunk_index: int
    page_number: int
    section_title: str | None
    content: str
    metadata: dict = field(default_factory=dict)


class SemanticChunker:
    """Sliding window semantic text chunker with structure detection and heading extraction."""

    def __init__(self, target_words: int = 250, overlap_words: int = 40):
        self.target_words = target_words
        self.overlap_words = overlap_words

    def _normalize_text(self, text: str) -> str:
        text = re.sub(r"\r\n|\r", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _detect_section_heading(self, line: str) -> str | None:
        clean = line.strip()
        if not clean:
            return None
        if clean.startswith("#") or clean.startswith("Section") or clean.startswith("Chapter"):
            return clean.lstrip("#").strip()
        if len(clean) < 60 and (clean.isupper() or clean.endswith(":")):
            return clean.rstrip(":").strip()
        return None

    def chunk_page(
        self, page_number: int, text: str, starting_chunk_index: int = 0
    ) -> list[ChunkOutput]:
        normalized = self._normalize_text(text)
        if not normalized:
            return []

        lines = normalized.split("\n")
        current_section = None
        chunks: list[ChunkOutput] = []

        # Find first heading if present
        for line in lines[:5]:
            heading = self._detect_section_heading(line)
            if heading:
                current_section = heading
                break

        words = normalized.split()
        if len(words) <= self.target_words:
            # Page fits in a single chunk
            chunks.append(
                ChunkOutput(
                    chunk_index=starting_chunk_index,
                    page_number=page_number,
                    section_title=current_section,
                    content=normalized,
                    metadata={
                        "word_count": len(words),
                        "char_count": len(normalized),
                        "char_start": 0,
                        "char_end": len(normalized),
                        "word_start": 0,
                        "word_end": len(words),
                    },
                )
            )
            return chunks

        # Multi-chunk sliding window
        step = max(self.target_words - self.overlap_words, 50)
        idx = starting_chunk_index

        for i in range(0, len(words), step):
            chunk_words = words[i : i + self.target_words]
            chunk_text = " ".join(chunk_words)

            if len(chunk_words) < 20 and len(chunks) > 0:
                # Append residual short trailing fragment to previous chunk
                break

            char_start = normalized.find(chunk_text[:30]) if len(chunk_text) >= 30 else 0
            if char_start < 0:
                char_start = 0
            char_end = char_start + len(chunk_text)

            chunks.append(
                ChunkOutput(
                    chunk_index=idx,
                    page_number=page_number,
                    section_title=current_section,
                    content=chunk_text,
                    metadata={
                        "word_count": len(chunk_words),
                        "char_count": len(chunk_text),
                        "char_start": char_start,
                        "char_end": char_end,
                        "word_start": i,
                        "word_end": i + len(chunk_words),
                    },
                )
            )
            idx += 1

        return chunks
