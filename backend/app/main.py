from fastapi import FastAPI
from app.api.oauth import router as oauth_router
from app.api.chat import router as chat_router

app = FastAPI()
app.include_router(oauth_router)
app.include_router(chat_router)
