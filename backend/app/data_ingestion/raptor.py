from langchain_groq import ChatGroq
from langchain_core.documents import Document
import uuid
from typing import List
from chunking import perform_agentic_chunking

def build_leaf_documents(agent_chunks: List[Document], source):
    leaf_docs = []

    for idx, chunk in enumerate(agent_chunks):
        leaf_id = f"leaf_{uuid.uuid4().hex[:12]}"
        doc = Document(
            page_content=chunk.page_content,
            metadata={
                "node_type": "leaf",
                "leaf_id": leaf_id,
                "chunk_id": chunk.metadata["chunk_id"],
                "title": chunk.metadata["title"],
                "source": source,
                "level": 0
            }
        )
        leaf_docs.append(doc)

    return leaf_docs


def group_leaf_nodes(leaf_docs, group_size=5):
    groups = []
    current = []

    for doc in leaf_docs:
        current.append(doc)
        if len(current) == group_size:
            groups.append(current)
            current = []

    if current:
        groups.append(current)

    return groups


def build_raptor_parent_nodes(llm, leaf_groups, source):
    parent_docs = []

    for i, group in enumerate(leaf_groups):
        leaf_ids = [doc.metadata["leaf_id"] for doc in group]
        combined_text = "\n\n".join(doc.page_content for doc in group)

        summary_prompt = f"""
        Summarize the following content into a short navigation-level summary.
        Do NOT include details.

        Content:
        {combined_text}
        """

        summary = str(llm.invoke(summary_prompt).content).strip()

        parent_doc = Document(
            page_content=summary,
            metadata={
                "node_type": "parent",
                "parent_id": f"parent_{i+1}",
                "level": 1,
                "source": source,
                "leaf_node_ids": leaf_ids
            }
        )

        parent_docs.append(parent_doc)

    return parent_docs


def create_parent_and_leaf_chunks_with_raptor(llm, path: str, filename: str):
    agent_chunks = perform_agentic_chunking(llm, path=path, filename=filename)

    leaf_nodes = build_leaf_documents(agent_chunks, filename)

    leaf_groups = group_leaf_nodes(leaf_nodes, group_size=5)

    parent_nodes = build_raptor_parent_nodes(llm, leaf_groups, filename)

    return leaf_nodes + parent_nodes


if __name__ == "__main__":

    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

    nodes = create_parent_and_leaf_chunks_with_raptor(llm, "../../static/policy.txt", "policy.txt")

    for i in nodes:
        print(i)
        print("_"* 50)
    print(len(nodes))