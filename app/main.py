from __future__ import annotations

from fastapi import FastAPI

from app.interface.api.customer.routes import router as customers_router
from app.interface.api.auth.routes import router as auth_router

app = FastAPI(title="FastAPI Onion Architecture Example")


# ルーターを登録
app.include_router(customers_router)
app.include_router(auth_router)
