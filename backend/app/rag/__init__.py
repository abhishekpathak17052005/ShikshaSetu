"""
RAG upgrade package for ShikshaSetu — P0 components.

Modules:
  embedding_index  - Persistent embedding storage + in-memory numpy index
  intent_router    - Query intent classification (USER_DATA / RAG / MCP / HYBRID / OUT_OF_SCOPE)
  hybrid_retrieval - Keyword + vector fusion with Reciprocal Rank Fusion
  reranker         - MMR diversity reranker
  groundedness     - Groundedness scoring and structured citation builder
"""
