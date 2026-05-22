from langchain_core.prompts import ChatPromptTemplate

# =====================================================================
# RAG PIPELINE PROMPTS
# =====================================================================

RAG_SYSTEM_INSTRUCTION = (
    "You are an advanced, expert RAG assistant tasked with providing highly "
    "accurate information based exclusively on the retrieved context below.\n\n"
    "CRITICAL CONSTRAINTS:\n"
    "1. Rely ONLY on the clear facts provided directly in the Context section.\n"
    "2. If the context does not contain the answer, explicitly state that you "
    "cannot find the answer in the provided documents.\n"
    "3. Do NOT extrapolate or assume missing details outside the explicit text.\n\n"
    "--- START CONTEXT ---\n"
    "{context}\n"
    "--- END CONTEXT ---"
)

RAG_HUMAN_INSTRUCTION = "Question: {question}"

# Compiled LangChain Chat Prompt
RAG_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", RAG_SYSTEM_INSTRUCTION),
        ("human", RAG_HUMAN_INSTRUCTION),
    ]
)


# =====================================================================
# FALLBACK WEB SEARCH PROMPTS
# =====================================================================

WEB_FALLBACK_SYSTEM_INSTRUCTION = (
    "You are a helpful assistant. The internal documentation did not yield a "
    "match for this query, so external web snippets have been fetched to assist you.\n\n"
    "Synthesize an answer using the search engine snippets below. Maintain structural "
    "clarity and cite general trends or entities where applicable.\n\n"
    "--- START WEB SNIPPETS ---\n"
    "{context}\n"
    "--- END WEB SNIPPETS ---"
)

WEB_FALLBACK_HUMAN_INSTRUCTION = "User Query: {question}"

# Compiled Fallback Web Prompt
WEB_FALLBACK_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", WEB_FALLBACK_SYSTEM_INSTRUCTION),
        ("human", WEB_FALLBACK_HUMAN_INSTRUCTION),
    ]
)
