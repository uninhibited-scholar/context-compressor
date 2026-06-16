"""Compress retrieved RAG chunks before they reach the LLM.

Shows the LangChain-style transformer and the LlamaIndex-style node helper.
Both adapters duck-type the framework objects, so this example runs with no
LangChain / LlamaIndex installed — we use tiny stand-ins.

    python examples/rag_integration.py
"""

from dataclasses import dataclass, field

from context_compressor.integrations import (
    CompressorDocumentTransformer,
    compress_nodes,
)

CHUNK = """
2024-01-15 10:30:45 [INFO] retrieved document section
Connecting to vector store...
The refund policy allows returns within 30 days of purchase.
The refund policy allows returns within 30 days of purchase.
████████ 80%
Refunds are issued to the original payment method within 5 business days.
""".strip()


@dataclass
class Doc:                       # mimics a LangChain Document
    page_content: str
    metadata: dict = field(default_factory=dict)


class Node:                      # mimics a LlamaIndex TextNode
    def __init__(self, text):
        self.text = text

    def get_content(self):
        return self.text


def main() -> None:
    print("=== LangChain transformer ===")
    docs = [Doc(CHUNK, {"source": "policy.pdf"})]
    out = CompressorDocumentTransformer().transform_documents(docs)
    print(out[0].page_content)
    print("savings:", out[0].metadata["compression"])

    print("\n=== LlamaIndex compress_nodes ===")
    nodes = compress_nodes([Node(CHUNK)])
    print(nodes[0].get_content())


if __name__ == "__main__":
    main()
