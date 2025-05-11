from fastapi import FastAPI

from routers import upload_custom_model, ask

app = FastAPI()

app.include_router(upload_custom_model.router)
app.include_router(ask.router)
