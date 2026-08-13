import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Protocol

from agent.knowledge.model import (
    Chunk,
)


@dataclass(
    frozen=True,
    slots=True,
)
class LexicalSearchResult:
    chunk: Chunk
    score: float


_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")


def tokenize(
    text: str,
) -> list[str]:
    return [match.group(0).lower() for match in _TOKEN_PATTERN.finditer(text)]


class LexicalIndex(Protocol):
    def add(
        self,
        chunks: list[Chunk],
    ) -> None: ...

    def search(
        self,
        query: str,
        *,
        limit: int,
    ) -> list[LexicalSearchResult]: ...


class InMemoryBM25Index:
    def __init__(
        self,
        *,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self._chunks: list[Chunk] = []

        self._tokens: dict[
            str,
            list[str],
        ] = {}

        self._term_frequencies: dict[
            str,
            dict[str, int],
        ] = {}

        self._document_frequencies: dict[
            str,
            int,
        ] = {}

        self._document_lengths: dict[
            str,
            int,
        ] = {}

        self._k1 = k1
        self._b = b

    def add(
        self,
        chunks: list[Chunk],
    ) -> None:
        for chunk in chunks:
            terms = tokenize(chunk.content)

            frequencies = Counter(terms)

            self._chunks.append(chunk)

            self._term_frequencies[chunk.id] = frequencies

            self._document_lengths[chunk.id] = len(terms)

            for term in frequencies:
                self._document_frequencies[term] = (
                    self._document_frequencies.get(term, 0) + 1
                )

    def _average_document_length(
        self,
    ) -> float:
        if not self._chunks:
            return 0.0

        return sum(self._document_lengths.values()) / len(self._chunks)

    def search(
        self,
        query: str,
        *,
        limit: int,
    ) -> list[LexicalSearchResult]:
        if limit < 1:
            raise ValueError("limit must be >= 1")

        query_terms = tokenize(query)

        if not query_terms:
            return []

        if not self._chunks:
            return []

        average_length = self._average_document_length()
        results: list[LexicalSearchResult] = []
        for chunk in self._chunks:
            score = self._score_chunk(
                chunk,
                query_terms,
                average_length,
            )

            if score <= 0:
                continue

            results.append(
                LexicalSearchResult(
                    chunk=chunk,
                    score=score,
                )
            )

        results.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return results[:limit]

    def _score_chunk(
        self,
        chunk: Chunk,
        query_terms: list[str],
        average_length: float,
    ) -> float:
        score = 0.0

        term_frequencies = self._term_frequencies[chunk.id]

        document_length = self._document_lengths[chunk.id]

        document_count = len(self._chunks)

        for term in set(query_terms):
            tf = term_frequencies.get(
                term,
                0,
            )

            if tf == 0:
                continue

            df = self._document_frequencies.get(term, 0)

            idf = math.log(1.0 + (document_count - df + 0.5) / (df + 0.5))

            denominator = tf + self._k1 * (
                1.0 - self._b + self._b * document_length / average_length
            )

            score += idf * (tf * (self._k1 + 1.0)) / denominator

        return score
