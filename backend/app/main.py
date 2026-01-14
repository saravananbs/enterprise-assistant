from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.my_agents.utils.db.checkpointer import checkpointer, checkpoint_pool
from app.api.oauth import router as oauth_router
from app.api.chat import router as chat_router
from app.api.auth import router as auth_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    checkpointer.setup()
    yield 
    checkpoint_pool.close()

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",   
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],     
    allow_headers=["*"],    
)

app.include_router(auth_router)
app.include_router(oauth_router)
app.include_router(chat_router)
