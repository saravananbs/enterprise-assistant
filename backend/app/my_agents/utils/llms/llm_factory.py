from langchain_groq import ChatGroq

_llm = None

def get_llm(model="llama-3.3-70b-versatile", **kwargs):
    global _llm
    if _llm is None:
        _llm = ChatGroq(model=model, temperature=0, **kwargs)
    return _llm

