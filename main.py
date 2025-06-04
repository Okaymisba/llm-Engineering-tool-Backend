from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.__init__ import init_db
from routers import auth, chat, payment_gateway, api
from routers import upload_custom_model, ask
from routers.auth import TokenRefreshMiddleware

app = FastAPI()

# Add token refresh middleware
app.add_middleware(
    TokenRefreshMiddleware,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.include_router(upload_custom_model.router)
app.include_router(ask.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(payment_gateway.router)
app.include_router(api.router)
