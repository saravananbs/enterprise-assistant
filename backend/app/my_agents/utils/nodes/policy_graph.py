from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from sqlalchemy import create_engine
from langchain_huggingface import HuggingFaceEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..states.enterprise_state import EnterpriseState
from ..prompts.query_transalation import ( 
    DECOMPOSITION_SYSTEM_PROMPT, RAG_FUSION_SYSTEM_PROMPT, STEP_BACK_SYSTEM_PROMPT,
    HYDE_SYSTEM_PROMPT, TEMPORAL_NORMALIZATION_SYSTEM_PROMPT, GENERIC_SYSTEM_PROMPT
)
from ..prompts.policy_graph import ANSWER_GENERATION_SYSTEM_PROMPT
from ..db.connection import AsyncSessionLocal
from ..db.models import LangchainPgCollection, LangchainPgEmbedding
import ast
import os
from typing import List
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

CONNECTION_STRING = f"postgresql+psycopg://{os.getenv('POSTGRES_USERNAME')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5"
)

async def query_translation_node(state: EnterpriseState) -> dict:
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
        HumanMessage(content=user_query),
    ]
    response = await llm.ainvoke(messages)
    raw_output = response.content.strip()
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

async def reciprocal_rank_fusion_with_parents(results_per_query: List[LangchainPgEmbedding], k: int = 60):
    fused_scores = defaultdict(float)
    for docs in results_per_query:
        for rank, doc in enumerate(docs):
            score = 1 / (k + rank + 1)
            meta = doc.cmetadata
            print(meta)
            print(type(meta))
            print(str(meta))
            if meta["node_type"] == "leaf":
                fused_scores[meta["leaf_id"]] += score
            elif meta["node_type"] == "parent":
                for leaf_id in meta["leaf_node_ids"]:
                    fused_scores[leaf_id] += score
    return fused_scores

async def async_similarity_search(
    db: AsyncSession,
    collection_name: str,
    query: str,
    k: int = 5,
):
    query_embedding = await embeddings.aembed_query(query)
    collection_stmt = (
        select(LangchainPgCollection.uuid)
        .where(LangchainPgCollection.name == collection_name)
    )
    collection_id = await db.scalar(collection_stmt)
    if not collection_id:
        return []
    distance = LangchainPgEmbedding.embedding.op("<->")(query_embedding)
    stmt = (
        select(LangchainPgEmbedding)
        .where(LangchainPgEmbedding.collection_id == collection_id)
        .order_by(distance)
        .limit(k)
    )
    result = await db.execute(stmt)
    return [
        row.LangchainPgEmbedding
        for row in result.fetchall()
    ]


async def retrival_node(state: EnterpriseState) -> dict:
    per_query_results = []
    async with AsyncSessionLocal() as db:
        for query in state["translated_queries"]:
            docs = await async_similarity_search(
                db=db,
                collection_name=state["policy_file"],
                query=query,
                k=5,
            )
            per_query_results.append(docs)
    fused_scores = await reciprocal_rank_fusion_with_parents(per_query_results)
    ranked_leaf_ids = [
        leaf_id
        for leaf_id, _ in sorted(
            fused_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )
    ]
    async with AsyncSessionLocal() as db:
        stmt = (
            select(LangchainPgEmbedding)
            .where(LangchainPgEmbedding.cmetadata["leaf_id"].astext.in_(ranked_leaf_ids))
        )
        result = await db.execute(stmt)
        leaf_docs = result.scalars().all()
    doc_map = {doc.cmetadata["leaf_id"]: doc for doc in leaf_docs}
    ordered_docs = [
        doc_map[lid]
        for lid in ranked_leaf_ids
        if lid in doc_map
    ]
    serialized_docs = [
        {
            "leaf_id": doc.cmetadata.get("leaf_id"),
            "title": doc.cmetadata.get("title"),
            "content": doc.document,
            "metadata": doc.cmetadata,
        }
        for doc in ordered_docs
    ]
    print(serialized_docs)
    return {
        "retrieved_context": serialized_docs
    }


async def answer_generation_node(state: EnterpriseState) -> dict:
    user_query = state["messages"][-1].content
    docs = state.get("retrieved_context", [])

    if not docs:
        return {
            "messages": [AIMessage(content="No relevant policy information found.")]
        }

    context_blocks = []
    print(docs)
    for doc in docs:
        title = doc["title"]
        context_blocks.append(
            f"### {title}\n{doc['content']}"
        )

    context_text = "\n\n".join(context_blocks)
    system_prompt = ANSWER_GENERATION_SYSTEM_PROMPT.format(
        context_text=context_text
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_query)
    ]

    res = await llm.ainvoke(messages)
    response = res.content.strip()

    return {
        "messages": [AIMessage(content=response)]
    }
