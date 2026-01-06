from langchain_postgres import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
from sqlalchemy import create_engine
from langchain_groq import ChatGroq
from raptor import create_parent_and_leaf_chunks_with_raptor
import os


load_dotenv()


folder_name = "../../static"

files = []

if os.path.exists(folder_name):
    for filename in os.listdir(folder_name):
        file = {"file_name": filename, "path": folder_name+"/"+filename, "collection_name":filename[:-4]}
        files.append(file)
else:
    print(f"No folder name {folder_name} exists")
    quit()


"""
Perform chunking and use vectordb to ingest those chuks
"""
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5"
)

CONNECTION_STRING = f"postgresql+psycopg://{os.getenv('POSTGRES_USERNAME')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

engine = create_engine(CONNECTION_STRING)

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

for file in files[:2]:
    print("processing", file)
    PGVector.from_documents(
        documents=create_parent_and_leaf_chunks_with_raptor(llm, file["path"], file["file_name"]),
        embedding=embeddings,
        collection_name=file["collection_name"],
        connection=engine,
        pre_delete_collection=False
    )
    print("completed", file)