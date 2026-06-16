"""Tests for the LangChain / LlamaIndex adapters using lightweight fakes.

We don't install the real frameworks; we replicate just the duck-typed shape of
their document objects.
"""

from dataclasses import dataclass, field

from context_compressor.integrations import (
    CompressorDocumentTransformer,
    compress_nodes,
)

NOISY = "Connecting to db...\nreal payload line\nreal payload line\n"


@dataclass
class FakeLCDocument:
    """Mimics langchain_core.documents.Document."""
    page_content: str
    metadata: dict = field(default_factory=dict)


class FakeLINode:
    """Mimics a LlamaIndex TextNode (text + get/set_content)."""

    def __init__(self, text: str) -> None:
        self._text = text

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value

    def get_content(self) -> str:
        return self._text

    def set_content(self, value: str) -> None:
        self._text = value


def test_langchain_transformer_compresses_and_records_stats():
    docs = [FakeLCDocument(NOISY, {"source": "a"})]
    out = CompressorDocumentTransformer().transform_documents(docs)
    assert len(out) == 1
    assert "Connecting" not in out[0].page_content
    assert "real payload line" in out[0].page_content
    # Original is untouched (we return copies).
    assert "Connecting" in docs[0].page_content
    comp = out[0].metadata["compression"]
    assert comp["compressed_tokens"] <= comp["original_tokens"]
    assert out[0].metadata["source"] == "a"


def test_langchain_transformer_can_skip_stats():
    docs = [FakeLCDocument(NOISY)]
    out = CompressorDocumentTransformer(record_stats=False).transform_documents(docs)
    assert "compression" not in out[0].metadata


def test_compress_nodes_llamaindex_shape():
    nodes = [FakeLINode(NOISY)]
    out = compress_nodes(nodes)
    assert "Connecting" not in out[0].get_content()
    assert "real payload line" in out[0].get_content()
    # Original untouched.
    assert "Connecting" in nodes[0].get_content()


def test_adapters_pass_through_unknown_objects():
    sentinel = object()
    out = compress_nodes([sentinel])
    assert out == [sentinel]
