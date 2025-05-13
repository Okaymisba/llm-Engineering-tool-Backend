from fastapi import FastAPI

from models.__init__ import init_db
from routers import auth
from routers import upload_custom_model, ask

app = FastAPI()

init_db()

app.include_router(upload_custom_model.router)
app.include_router(ask.router)
app.include_router(auth.router)
