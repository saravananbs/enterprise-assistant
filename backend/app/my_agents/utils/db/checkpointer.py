import os
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver


DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USERNAME')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:"
    f"{os.getenv('POSTGRES_PORT')}/"
    f"{os.getenv('POSTGRES_DB')}"
)

checkpoint_pool = ConnectionPool(
    conninfo=DATABASE_URL,
    max_size=10,
    kwargs={"autocommit": True},
)

checkpointer = PostgresSaver(checkpoint_pool)