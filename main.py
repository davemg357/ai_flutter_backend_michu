from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
from dotenv import load_dotenv

load_dotenv()  # only needed for local .env

HF_TOKEN = os.getenv("HF_TOKEN")

app = FastAPI(title="Flutter AI Backend")

class ChatRequest(BaseModel):
    messages: list  # [{"role": "user", "content": "Hello"}]

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    url = "https://router.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-oss-20b:groq",
        "messages": request.messages
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
