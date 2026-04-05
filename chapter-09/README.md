# Chapter 9: Ragonomics - The Science of Retrieval-Augmented Generation

## 12 RAG Strategies

The most technically dense chapter. Based on Ragpedia, a 28-chapter
RAG encyclopedia.

- `naive_rag.py` - Foundation: retrieve top-k chunks, stuff into prompt
- `fusion_rag.py` - Multi-query expansion for better recall
- `reranking_rag.py` - Two-stage retrieval with LLM reranking
- `rag_evaluation.py` - RAGAS metrics: faithfulness, relevancy, precision
- `decision_matrix.py` - Interactive tool to choose the right RAG strategy

```bash
uv run python chapter-09/naive_rag.py
uv run python chapter-09/rag_evaluation.py
uv run python chapter-09/decision_matrix.py
```
