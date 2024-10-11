from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

@app.get("/")
async def root():
    verify_token = os.getenv("VERIFY_TOKEN")
    return {"VERIFY_TOKEN": verify_token}
