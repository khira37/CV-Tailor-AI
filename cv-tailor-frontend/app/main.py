# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn

from router import router as cv_router
load_dotenv()

app = FastAPI(
    title="Resume Tailor Backend Pipeline",
    description="API to extract Google Doc content, optimize via Gemini, and compile tailored PDFs.",
    version="1.0"
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register our modular routes cleanly
app.include_router(cv_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)