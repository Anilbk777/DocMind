from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

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
    "CONTEXT={context}\n"
)

RAG_HUMAN_INSTRUCTION = "Question: {question}"

# Compiled LangChain Chat Prompt
RAG_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", RAG_SYSTEM_INSTRUCTION),
        MessagesPlaceholder(variable_name="history"),
        ("human", RAG_HUMAN_INSTRUCTION),
    ]
)


# =====================================================================
# GENERAL / CONVERSATIONAL PROMPTS
# =====================================================================

GENERAL_SYSTEM_INSTRUCTION = (
    "You are a helpful, brilliant, and adaptive AI assistant. Answer the user's "
    "question directly, clearly, and comprehensively using your internal knowledge.\n\n"
    "CRITICAL CONSTRAINTS:\n"
    "1. For coding, mathematics, explaining concepts or technical queries, provide clean formatting and clear logic.\n"
    "2. If the user is just engaging in small talk (e.g., saying hello, greeting you), respond warmly and naturally."
)

GENERAL_HUMAN_INSTRUCTION = "User Query: {question}"

# Compiled General Chat Prompt
GENERAL_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", GENERAL_SYSTEM_INSTRUCTION),
        MessagesPlaceholder(variable_name="history"),
        ("human", GENERAL_HUMAN_INSTRUCTION),
    ]
)
