from typing import Protocol

from openai import OpenAI

Embedding = list[float]


class EmbeddingModel(Protocol):
    def embed(
        self,
        texts: list[str],
    ) -> list[Embedding]: ...


class OpenAIEmbeddingModel:
    def __init__(
        self,
        *,
        client: OpenAI,
        model: str,
    ) -> None:
        self._client = client
        self._model = model

    def embed(
        self,
        texts: list[str],
    ) -> list[Embedding]:
        if not texts:
            return []

        response = self._client.embeddings.create(
            model=self._model,
            input=texts,
        )

        return [item.embedding for item in response.data]
