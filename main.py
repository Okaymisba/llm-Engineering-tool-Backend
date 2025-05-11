from fastapi import FastAPI
from models.user import init_db

from routers import upload_custom_model, ask

app = FastAPI()

init_db()

app.include_router(upload_custom_model.router)
app.include_router(ask.router)
