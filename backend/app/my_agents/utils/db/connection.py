import os
from dotenv import load_dotenv
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

load_dotenv()

DATABASE_URL = f"postgresql+asyncpg://{os.getenv('POSTGRES_USERNAME')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,          
    pool_size=10,                 
    max_overflow=20,
    pool_timeout=30,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,         
    expire_on_commit=False,      
    autoflush=False,
)

Base = declarative_base()

async def get_async_session() ->  AsyncGenerator[AsyncSession, None]:
    try:
        async with AsyncSessionLocal() as session:
            yield session
    finally:
        await session.close()

async def get_async_db_session() -> AsyncSession:
    return AsyncSessionLocal()