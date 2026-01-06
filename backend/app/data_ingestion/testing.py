from langchain_postgres import PGVector
from dotenv import load_dotenv
from sqlalchemy import create_engine
import os
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

CONNECTION_STRING = f"postgresql+psycopg://{os.getenv('POSTGRES_USERNAME')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

engine = create_engine(CONNECTION_STRING)
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5"
)
existing_vstore = PGVector(
    connection=engine,
    collection_name="remote_work_policy",
    embeddings=embeddings
)

# Now you can search immediately without re-inserting
while True:
    print(existing_vstore.similarity_search(input("Enter the query\n")))