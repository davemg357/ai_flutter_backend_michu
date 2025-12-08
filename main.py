from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

app = FastAPI(title="Flutter AI Backend")

# --- CORS Middleware for Flutter Web ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# STATIC MICHU CONTEXT
# -------------------------------
MICHU_CONTEXT = """
Michu is a digital lending platform owned by Cooperative Bank of Oromia.
It provides collateral-free loans to MSMEs, youth, women, and informal businesses.

Main Products:
- Michu Guyyaa: 2,000 – 15,000 ETB, 7 days, 12% facility fee.
- Michu Kiyya (Informal): 3,000 – 5,000 ETB, 14 days, 3.75% interest.
- Michu Kiyya (Formal): 10,000 – 30,000 ETB, 30 days, 3.75% interest.
- Michu Wabi: 50,000 – 300,000 ETB, 30–90 days, 6.5%–8% interest.

Michu requires no collateral and provides instant approval through the app.
"""

# -------------------------------
# MULTIPLE COOPBANK URLS
# -------------------------------
COOPBANK_URLS = [
    "https://coopbankoromia.com.et",
    "https://coopbankoromia.com.et/about/",
    "https://coopbankoromia.com.et/coopbank-alhuda/",
    "https://coopbankoromia.com.et/deposit-products/ordinary-saving-account/",
    "https://diasporabanking.coopbankoromiasc.com/",
    "https://coopbankoromia.com.et/coopay-ebirr/",
    "https://coopbankoromia.com.et/e-banking-2-3/#card-banking",
]

# -------------------------------
# SCRAPER FUNCTION
# -------------------------------
def fetch_multiple_urls(urls: list) -> str:
    combined_text = ""

    for url in urls:
        try:
            print(f"Scraping: {url}")
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove useless elements
            for tag in soup(["script", "style", "noscript", "header", "footer", "svg"]):
                tag.decompose()

            # Extract visible text
            text = soup.get_text(separator=" ")
            cleaned = " ".join(text.split())  # Normalize spacing

            combined_text += cleaned + "\n\n"

        except Exception:
            combined_text += ""

    return combined_text.strip()


# Fetch Coopbank website content ONCE (you can later add caching)
dynamic_coopbank_text = fetch_multiple_urls(COOPBANK_URLS)

COOPBANK_CONTEXT = f"""
Cooperative Bank of Oromia Banking Solutions

Products and Services:
Digital banking, CoopApp, Ebirr, card banking, agri-finance, MSME finance,
loans, advances, deposits, trade services, and cooperative relations.

Live Website Data:
{dynamic_coopbank_text}
"""


# -------------------------------
# REQUEST BODY MODEL
# -------------------------------
class ChatRequest(BaseModel):
    messages: list  # [{"role": "user", "content": "Hello"}]


# -------------------------------
# CHAT ENDPOINT
# -------------------------------
@app.post("/chat")
def chat_endpoint(request: ChatRequest):

    url = "https://router.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    # SYSTEM PROMPT WITH CONTEXTS
    system_context = {
        "role": "system",
        "content": (
            "You are an AI assistant that knows everything about "
            "1) Michu Digital Lending Platform and "
            "2) Cooperative Bank of Oromia. "
            "Use both the static context and the live scraped website content. "
            "Answer clearly in plain text only. No emojis, markdown, or tables.\n\n"
            f"{MICHU_CONTEXT}\n\n"
            f"{COOPBANK_CONTEXT}"
        )
    }

    # PREPEND SYSTEM CONTEXT
    messages_with_context = [system_context] + request.messages

    payload = {
        "model": "openai/gpt-oss-20b:groq",
        "messages": messages_with_context
    }

    # SEND TO HF ROUTER
    try:
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
