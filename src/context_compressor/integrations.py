"""Drop-in adapters for LangChain and LlamaIndex.

These adapters are **dependency-free**: they duck-type the document objects of
each framework instead of importing it, so installing ``context-compressor``
never pulls in LangChain or LlamaIndex. If you pass real framework objects they
just work.

LangChain ``Document`` exposes ``page_content`` (str) and ``metadata`` (dict).
LlamaIndex ``Document`` / ``TextNode`` expose ``text`` (str) and
``get_content()`` / ``set_content()``. We support both shapes.
"""

from __future__ import annotations

import copy
from typing import Any, Iterable, List, Optional

from .config import CompressionConfig
from .core.compressor import ContextCompressor


class CompressorDocumentTransformer:
    """Compress the text of LangChain-style documents.

    Mirrors LangChain's ``BaseDocumentTransformer`` interface
    (``transform_documents``) so it can be dropped into a retrieval chain to
    shrink retrieved chunks before they reach the LLM.

    Example
    -------
    >>> transformer = CompressorDocumentTransformer()
    >>> smaller_docs = transformer.transform_documents(retrieved_docs)
    """

    def __init__(self, compressor: Optional[ContextCompressor] = None,
                 config: Optional[CompressionConfig] = None,
                 record_stats: bool = True) -> None:
        self.compressor = compressor or ContextCompressor(config)
        self.record_stats = record_stats

    def transform_documents(self, documents: Iterable[Any],
                            **_: Any) -> List[Any]:
        out: List[Any] = []
        for doc in documents:
            out.append(self._compress_doc(doc))
        return out

    async def atransform_documents(self, documents: Iterable[Any],
                                   **kwargs: Any) -> List[Any]:
        # No real async work; provided for interface compatibility.
        return self.transform_documents(documents, **kwargs)

    def _compress_doc(self, doc: Any) -> Any:
        text = _get_text(doc)
        if text is None:
            return doc
        result = self.compressor.compress(text)
        new_doc = copy.copy(doc)
        _set_text(new_doc, result.compressed)
        if self.record_stats:
            meta = getattr(new_doc, "metadata", None)
            if isinstance(meta, dict):
                meta = dict(meta)
                meta["compression"] = {
                    "original_tokens": result.stats.original_tokens,
                    "compressed_tokens": result.stats.compressed_tokens,
                    "reduction_pct": round(result.stats.reduction_pct, 1),
                }
                try:
                    new_doc.metadata = meta
                except Exception:
                    pass
        return new_doc


def compress_nodes(nodes: Iterable[Any],
                   compressor: Optional[ContextCompressor] = None,
                   config: Optional[CompressionConfig] = None) -> List[Any]:
    """Compress LlamaIndex nodes/documents in place-ish (returns copies).

    Works with any object exposing ``text`` or ``get_content()/set_content()``.

    Example
    -------
    >>> from context_compressor.integrations import compress_nodes
    >>> nodes = compress_nodes(index.docstore.docs.values())
    """
    comp = compressor or ContextCompressor(config)
    out: List[Any] = []
    for node in nodes:
        text = _get_text(node)
        if text is None:
            out.append(node)
            continue
        compressed = comp.compress(text).compressed
        new_node = copy.copy(node)
        _set_text(new_node, compressed)
        out.append(new_node)
    return out


# -- duck-typed accessors -------------------------------------------------
def _get_text(obj: Any) -> Optional[str]:
    # LangChain Document
    if hasattr(obj, "page_content") and isinstance(obj.page_content, str):
        return obj.page_content
    # LlamaIndex get_content()
    getter = getattr(obj, "get_content", None)
    if callable(getter):
        try:
            val = getter()
            if isinstance(val, str):
                return val
        except Exception:
            pass
    # LlamaIndex / generic .text
    if hasattr(obj, "text") and isinstance(obj.text, str):
        return obj.text
    if isinstance(obj, str):
        return obj
    return None


def _set_text(obj: Any, value: str) -> None:
    if hasattr(obj, "page_content"):
        try:
            obj.page_content = value
            return
        except Exception:
            pass
    setter = getattr(obj, "set_content", None)
    if callable(setter):
        try:
            setter(value)
            return
        except Exception:
            pass
    if hasattr(obj, "text"):
        try:
            obj.text = value
        except Exception:
            pass
