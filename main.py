# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import time
from cachetools import TTLCache, cached
from typing import List, Optional
from urllib.parse import urlparse

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

# Default external sources (feel free to change to coopbank/gamtaa domains)
EXTRA_SOURCES = os.getenv(
    "EXTRA_SOURCES",
    "https://coopbankoromia.com.et/,https://coopbankoromia.com.et/our-digital-offerings/,https://coopbankoromia.com.et/coopbank-smart-branch/,https://coopbankoromia.com.et/about/"
)
WEBSITE_CACHE_TTL = int(os.getenv("WEBSITE_CACHE_TTL", "3600"))

app = FastAPI(title="GamtaaAPP - AI Backend (Coopbank)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Replace these with your full long contexts as needed ----
MICHU_CONTEXT = """Michu Loan: Empowering Ethiopian MSMEs Through Digital Lending

Welcome to Michu, the digital lending platform that understands your business needs and supports your growth. Whether you’re a small vendor, an aspiring entrepreneur, or an established MSME, Michu is here to help you thrive. Say goodbye to collateral requirements and long approval processes with Michu, your financing is just a few taps away.

Loans Tailored for Your Business

With Michu, we believe in making financing accessible to all. That’s why we’ve designed three unique products to meet the diverse needs of Ethiopian businesses:

Michu Wabi

This product is ideal for medium-sized enterprises looking for significant capital. With loan amounts ranging from 50,000 ETB to 300,000 ETB, Michu Wabi provides the financial boost you need to expand operations, purchase inventory, or upgrade equipment.

Michu Guyyaa

Tailored for small businesses, including those operating informally like street vendors, Michu Guyyaa offers loans between 2,000 ETB and 15,000 ETB. No business license? No problem. We focus on your potential, not paperwork.

Michu Kiyya

Designed to empower women entrepreneurs, Michu Kiyya provides loans up to 30,000 ETB with fewer service charges and minimal hassle. It’s our way of supporting women who are making a difference in their communities.

How Michu Works

Michu is entirely digital, making it easy and convenient for you to access the funds you need. Here’s how it works:

Install the app, available on major platforms.

Sign Up: Create your profile, link your bank account, and provide some basic details about your business.

Get Your Loan: Apply for the amount you need and receive approval instantly. Funds are transferred directly to your account, ready for use.

Achieve More: As you repay your loans on time, Michu’s AI-powered system increases your eligible loan amount, helping your business grow with every step.

Transforming Lives, One at a time

With over 2.3 million MSMEs already supported, Michu is making a tangible impact across Ethiopia.

“When my business faced cash flow issues, Michu helped me cover my rent and keep the doors open.”
“Thanks to Michu, I expanded my street vending business without worrying about collateral.”
“As a woman in business, I found Michu Kiyya’s low charges and easy process to be a game-changer.”

Pricing
Michu Guyyaa

Credit Limit: 2,000 – 15,000 ETB

Credit Period: 7 Days

Access/Facility Fee: 12%

Michu Kiyya Informal

Credit Limit: 3,000 – 5,000 ETB

Credit Period: 14 Days

Interest Rate: 3.75%

Michu Kiyya Formal

Credit Limit: 10,000 – 30,000 ETB

Credit Period: 30 Days

Interest Rate: 3.75%

Michu Wabi

Credit Limit: 50,000 – 300,000 ETB

Credit Period: 30 to 90 Days

Interest Rate: 6.5% to 8% per month

Frequently Asked Questions

Do I need a business license to apply?
Michu Guyyaa is designed for informal businesses, so a license is not required.

How quickly can I get my loan?
Approval is instant, and funds are deposited directly into your bank account.

What happens if I repay on time?
Repaying your loan on time increases your eligible loan amount for future applications, thanks to our AI-based system.

Privacy Policy

Michu operates strictly within all regulatory frameworks, ensuring a safe and secure lending experience for our customers.
"""

COOPBANK_CONTEXT = """
Cooperative Bank of Oromia Banking Solutions

Digital Offerings:
COOPay-Ebirr
Card Banking
CoopApp
CoopApp Alhuda
Farmpass
Coopbank SACCO-Link

Deposit Products:
Demand Deposit
Saving Deposit
Fixed Time Deposit

Trade Service:
Import
Export
Money Transfers
Guarantee (Foreign)

Agri and Cooperative Relations:
Cooperatives Saving Products:
- Cooperative Saving
- Requirements

Cooperative Financing:
- Working Capital Loan
- Agriculture Mechanization
- Agriculture Processing
- Export Financing Facilities
- Others

Cooperatives Capacity Building and Advisory:
- Capacity Building and Advisory Services
- Intended Impact of Coopbank’s Advisory Services
- Stakeholders to Partner with Coopbank

Loan and Advances:
- Collateralized Commodity Financing (CCF)
- Overdraft Facility
- Merchandise Loan Facility
- Pre-shipment Export Credit Facility
- Letter of Guarantee Facility
- Term Loan
- Agricultural Term Loan
- Motor Vehicle Loan
- Revolving Export Credit Facility

Other Financings:
- Partial Financing for Acquired and Foreclosed Collateral
- Equipment/machinery Lease Financing
- Import Letter of Credit Settlement Loan
"""
# ---------------------------------------------------------------

class ChatRequest(BaseModel):
    messages: list  # [{"role": "user", "content": "Hello"}]
    extra_urls: Optional[List[str]] = None

website_cache = TTLCache(maxsize=256, ttl=WEBSITE_CACHE_TTL)

HEADERS = {
    "User-Agent": "GamtaaAPP-AI-Backend/1.0 (+https://gamtaaapp.local/)",
}

def extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.body or soup
    text = main.get_text(separator="\n", strip=True)
    max_chars = 20_000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n[truncated]"
    return text

@cached(website_cache)
def fetch_site_text(url: str, timeout: int = 8) -> str:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return extract_text_from_html(resp.text)
    except Exception:
        return ""

def gather_web_context(urls: List[str]) -> str:
    pieces = []
    for u in urls:
        parsed = urlparse(u)
        if parsed.scheme == "":
            u = "https://" + u
        if parsed.hostname and parsed.hostname.startswith(("127.", "localhost", "192.", "10.", "172.")):
            continue
        text = fetch_site_text(u)
        if not text:
            continue
        snippet = text[:2000]
        pieces.append(f"Source: {u}\n{snippet}\n---")
        time.sleep(0.2)
    if not pieces:
        return ""
    return "\n".join(pieces)

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    env_urls = [s.strip() for s in EXTRA_SOURCES.split(",") if s.strip()]
    request_urls = request.extra_urls or []
    combined_urls = []
    for u in request_urls + env_urls:
        if u not in combined_urls:
            combined_urls.append(u)

    web_context = gather_web_context(combined_urls) if combined_urls else ""

    system_content = (
    "You are an assistant for gamtaaAPP — the Cooperative Bank of Oromia's mobile super-app. "
    "Michu (Michu Loan) is a lending product offered by Cooperative Bank of Oromia and is available inside gamtaaAPP. "
    "Answer clearly and concisely in plain text only. Do not use emojis, tables, markdown, or symbols. "
    "Keep responses short and easy to read.\n\n"
    "Static Context (Coopbank + Michu):\n"
    f"{MICHU_CONTEXT}\n\n"
    f"{COOPBANK_CONTEXT}\n\n"
    "Use extracts from external websites (if available) to provide updated information.\n"
    "If the user query is not covered in any of the above contexts, answer using your general AI knowledge, "
    "while maintaining accuracy and clarity relevant to Ethiopian banking and fintech.\n"
    )

    if web_context:
        system_content += "Augmented with short extracts from external websites (for factual freshness):\n" + web_context + "\n\n"

    system_context = {"role": "system", "content": system_content}
    messages_with_context = [system_context] + request.messages

    payload = {
        "model": "openai/gpt-oss-20b:groq",
        "messages": messages_with_context,
    }

    url = "https://router.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Small helper endpoint to test extraction quickly
class URLRequest(BaseModel):
    url: str

@app.post("/extract")
def extract_endpoint(req: URLRequest):
    url = req.url
    parsed = urlparse(url)
    if parsed.scheme == "":
        url = "https://" + url
    text = fetch_site_text(url)
    if not text:
        raise HTTPException(status_code=404, detail="Could not fetch or extract content from the URL.")
    # return a short snippet for quick verification
    return {"url": url, "snippet": text[:2000]}
