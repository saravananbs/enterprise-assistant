from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langchain_postgres import PGVector
from sqlalchemy import create_engine
from langchain_huggingface import HuggingFaceEmbeddings
from ..states.enterprise_state import EnterpriseState
from ..prompts.query_transalation import ( 
    DECOMPOSITION_SYSTEM_PROMPT, RAG_FUSION_SYSTEM_PROMPT, STEP_BACK_SYSTEM_PROMPT,
    HYDE_SYSTEM_PROMPT, TEMPORAL_NORMALIZATION_SYSTEM_PROMPT, GENERIC_SYSTEM_PROMPT
)
from ..prompts.policy_graph import ANSWER_GENERATION_SYSTEM_PROMPT
import ast
import os
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

CONNECTION_STRING = f"postgresql+psycopg://{os.getenv('POSTGRES_USERNAME')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
engine = create_engine(CONNECTION_STRING)

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5"
)


def query_translation_node(state: EnterpriseState) -> dict:
    user_query = state["messages"][-1].content

    SYSTEM_PROMPT = GENERIC_SYSTEM_PROMPT
    if state["query_translation"] == "decomposition":
        SYSTEM_PROMPT = DECOMPOSITION_SYSTEM_PROMPT
    elif state["query_translation"] == "rag_fusion":
        SYSTEM_PROMPT = RAG_FUSION_SYSTEM_PROMPT
    elif state["query_translation"] == "step_back_prompting":
        SYSTEM_PROMPT = STEP_BACK_SYSTEM_PROMPT
    elif state["query_translation"] == "hypothetical_document_embeddings":
        SYSTEM_PROMPT = HYDE_SYSTEM_PROMPT
    elif state["query_translation"] == "temporal_normalization":
        SYSTEM_PROMPT = TEMPORAL_NORMALIZATION_SYSTEM_PROMPT
   
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_query)
    ]

    raw_output = llm.invoke(messages).content.strip()
    
    try:
        decomposed_queries = ast.literal_eval(raw_output)
        if not isinstance(decomposed_queries, list):
            raise ValueError("Output is not a list")
        decomposed_queries = [
            q for q in decomposed_queries if isinstance(q, str)
        ]
    except Exception:
        decomposed_queries = [user_query]
    return {
        "translated_queries": decomposed_queries
    }


def reciprocal_rank_fusion_with_parents(results_per_query, k: int = 60):
    fused_scores = defaultdict(float)
    for docs in results_per_query:
        for rank, doc in enumerate(docs):
            score = 1 / (k + rank + 1)
            meta = doc.metadata
            if meta["node_type"] == "leaf":
                fused_scores[meta["leaf_id"]] += score
            elif meta["node_type"] == "parent":
                for leaf_id in meta["leaf_node_ids"]:
                    fused_scores[leaf_id] += score
    return fused_scores


def retrival_node(state: EnterpriseState) -> dict:
    existing_vstore = PGVector(
        connection=engine,
        collection_name=state["policy_file"],
        embeddings=embeddings
    )
    per_query_results = []
    for query in state["translated_queries"]:
        docs = existing_vstore.similarity_search(query, k=5)
        per_query_results.append(docs)

    fused_scores = reciprocal_rank_fusion_with_parents(per_query_results)

    ranked_leaf_ids = [
        leaf_id
        for leaf_id, _ in sorted(
            fused_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
    ]

    leaf_docs = existing_vstore.similarity_search(
        query="",
        k=len(ranked_leaf_ids),
        filter={"leaf_id": {"$in": ranked_leaf_ids}}
    )

    doc_map = {doc.metadata["leaf_id"]: doc for doc in leaf_docs}
    ordered_docs = [
        doc_map[lid] for lid in ranked_leaf_ids if lid in doc_map
    ]
    print(ordered_docs)
    return {
        "retrieved_context": ordered_docs
    }


def answer_generation_node(state: EnterpriseState) -> dict:
    user_query = state["messages"][-1].content
    docs = state.get("retrieved_context", [])

    if not docs:
        return {
            "messages": [AIMessage(content="No relevant policy information found.")]
        }

    context_blocks = []
    for doc in docs:
        title = doc.metadata.get("title", "Untitled Section")
        context_blocks.append(
            f"### {title}\n{doc.page_content}"
        )

    context_text = "\n\n".join(context_blocks)
    system_prompt = ANSWER_GENERATION_SYSTEM_PROMPT.format(
        context_text=context_text
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_query)
    ]

    response = llm.invoke(messages).content.strip()

    return {
        "messages": [AIMessage(content=response)]
    }
