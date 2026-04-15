<!-- Last updated: 2026-04-15 13:34 UTC -->
SCRATCH_ADD: Researching TiDB's AI memory architecture and Mem0's agent memory mechanisms to structure EternalMind's layers.  

BROWSER_NAV: https://www.pingcap.com/blog/how-to-build-an-ai-memory-architecture-that-actually-remembers/  
BROWSER_READ:  

FILE_WRITE: memory/research/tidb-memory-architecture.md  
FILE_CONTENT_START  
**TiDB AI Memory Architecture Insights**  
- **Ephemeral vs. Persistent Memory**:  
  - *Ephemeral*: Short-term working memory for live sessions (e.g., chat context).  
  - *Persistent*: Long-term storage for facts, preferences, and summaries.  
- **Semantic Retrieval**: Embeddings and similarity search over notes, chats, and documents.  
- **Procedural Memory**: Automation of workflows (e.g., "publish newsletter").  

**Key Takeaways**:  
- Layered memory avoids context-window overload by precomputing structure.  
- Integration with existing systems (e.g., ForgeCore) requires modular design.  
FILE_CONTENT_END  

BROWSER_NAV: https://mem0.ai/blog/memory-in-agents-what-why-and-how  
BROWSER_READ:  

FILE_WRITE: memory/research/mem0-agent-memory.md  
FILE_CONTENT_START  
**Mem0 Agent Memory Mechanisms**  
- **Memory Types**:  
  - *Short-term*: Context for current tasks.  
  - *Long-term*: Summaries, facts, and preferences.  
- **Retrieval Strategies**: Keyword search, semantic similarity, and contextual filtering.  
- **Implementation**: Tools like Redis for storage and vector databases for embeddings.  

**Relevance to EternalMind**:  
- Aligns with Rob's layered approach (Ingestion → Normalization → Storage → Retrieval → Synthesis).  
- Emphasizes modularity for integration with existing workflows.  
FILE_CONTENT_END  

LIVE_CONTEXT_ADD: TiDB and Mem0 research completed. EternalMind's layered memory architecture will prioritize modularity, semantic retrieval, and procedural automation. Next: Map layers to ForgeCore/OpenClaw workflows.