from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import ai

app = FastAPI(title="SpendWise AI Service", version="1.0.0", description="Microservice for OCR, NLP Categorization, and Fraud Detection")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ai-microservice"}
