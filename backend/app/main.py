import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, departments, users, expenses, approvals, budgets, upload, logs

app = FastAPI(title="SpendWise AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(departments.router, prefix="/departments", tags=["departments"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
app.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
app.include_router(budgets.router, prefix="/budgets", tags=["budgets"])
app.include_router(upload.router, prefix="/upload", tags=["upload"])
app.include_router(logs.router, prefix="/logs", tags=["logs"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
