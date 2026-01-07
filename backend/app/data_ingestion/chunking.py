from dotenv import load_dotenv
import json
import re
from langchain_groq import ChatGroq
from langchain_core.documents import Document
import time

load_dotenv()

AGENTIC_CHUNK_PROMPT = """
You are a precision document architect. Your task is to extract text into semantic chunks without losing a single word of the original content.

STRICT RULES:
1. NO SUMMARIZATION: Every word, bullet point, and detail from the provided text must be included in the chunks. 
2. CLEANING: Remove purely decorative symbols like '===' or '---' from the "chunk_text".
3. SELF-CONTAINED: If a chunk refers to "this policy", ensure the context is clear.
4. COMPLETENESS: Ensure lists (like Retention Periods) are kept together in one chunk or split logically without dropping items.

Return STRICT JSON:
{
  "chunks": [
    {
      "chunk_id": "chunk_1",
      "title": "Title of the section",
      "chunk_text": "Full text of the section with all bullet points"
    }
  ]
}

Document to process:
----------------
{document}
----------------
"""

def load_txt(path: str) -> str:
    """
    This function loads the txt file located in the path and return as the readable string

    :param path: path of the txt file which has the policy and other related stuffs
    :type path: str
    :return: the content of given file in str format
    :rtype: str
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def agentic_chunk_document(llm, document_text: str, max_safe_tokens=5000, recursion_depth=0):
    if recursion_depth > 5:  
        print("Max recursion depth reached; skipping.")
        return []

    prompt_template_len = len(AGENTIC_CHUNK_PROMPT) - len("{document}")
    approx_tokens = (len(document_text) + prompt_template_len) // 4

    if approx_tokens <= max_safe_tokens:
        try:
            response = llm.invoke(
                AGENTIC_CHUNK_PROMPT.replace("{document}", document_text),
                response_format={"type": "json_object"}
            )
            data = json.loads(response.content)
            return data.get("chunks", [])
        except Exception as e:  
            if "APIStatusError" in str(type(e)) and "413" in str(e):
                print(f"Rate limit or size hit. Waiting 60s... (Depth: {recursion_depth})")
                for i in range(60, 0, -1):
                    time.sleep(1)
                    if i % 10 == 0: print(f"{i}s remaining...")
                return agentic_chunk_document(llm, document_text, max_safe_tokens, recursion_depth + 1)
            else:
                print(f"Unexpected error: {e}")
                return []
    else:
        print(f"Document too large ({approx_tokens} tokens); splitting into sections.")
        sections = re.split(r'(SECTION \d+: .+?\n)', document_text, flags=re.DOTALL)
        
        split_sections = [sections[0].strip()] if sections[0].strip() else []
        for i in range(1, len(sections), 2):
            title = sections[i].strip()
            content = sections[i+1].strip() if i+1 < len(sections) else ''
            section_text = title + '\n' + content
            section_approx = len(section_text) // 4
            if section_approx > max_safe_tokens:
                print(f"Large section ({section_approx} tokens); splitting further.")
                subsections = re.split(r'(\d+\.\d+ .+?\n)', section_text, flags=re.DOTALL)
                for j in range(1, len(subsections), 2):
                    sub_title = subsections[j].strip()
                    sub_content = subsections[j+1].strip() if j+1 < len(subsections) else ''
                    split_sections.append(sub_title + '\n' + sub_content)
            else:
                split_sections.append(section_text)
        
        all_chunks = []
        chunk_counter = 1
        for idx, section in enumerate(split_sections):
            if not section.strip():
                continue
            section_chunks = agentic_chunk_document(llm, section, max_safe_tokens, recursion_depth + 1)
            for chunk in section_chunks:
                chunk['chunk_id'] = f"chunk_{chunk_counter}"
                chunk_counter += 1
            all_chunks.extend(section_chunks)
            time.sleep(1) 
        
        return all_chunks

def build_documents(agent_chunks, source_file: str, version: str):
    documents = []

    for idx, chunk in enumerate(agent_chunks):
        doc = Document(
            page_content=chunk["chunk_text"],
            metadata={
                "chunk_id": chunk["chunk_id"],
                "title": chunk["title"],
                "source": source_file,
                "doc_type": "txt",
                "version": version,
                "chunk_index": idx,
                "chunking_strategy": "agentic"
            }
        )
        documents.append(doc)

    return documents

def perform_agentic_chunking(llm, path: str, filename: str):
    raw_text = load_txt(path=path)

    agent_chunks = agentic_chunk_document(llm, raw_text)

    documents = build_documents(
        agent_chunks,
        source_file=filename,
        version="v1"
    )

    return documents

#testing code to check each file is working fine
if __name__ == "__main__":
    
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0
    )

    for file in ["../../static/privacy_policy.txt"]:

        documents = perform_agentic_chunking(llm, file)

        for i in documents:
            print(i)
            print("-" * 50)
        print("=" * 50)