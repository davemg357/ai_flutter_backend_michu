from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os, requests
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

app = FastAPI(title="Flutter AI Backend")

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

Michu operates strictly within all regulatory frameworks, ensuring a safe and secure lending experience for our customers."""  # (your full context here)

class ChatRequest(BaseModel):
    messages: list  # [{"role": "user", "content": "Hello"}]

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    url = "https://router.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    # Inject Michu context as system prompt (must be inside the function)
    system_context = {
        "role": "system",
        "content": (
            "You are an assistant that knows everything about the Michu digital lending platform. "
            "Answer clearly and concisely in plain text only. Do not use emojis, tables, markdown, or symbols. "
            "Make it short and easy to read.\n\n"
            f"Context:\n{MICHU_CONTEXT}"
        )
    }

    # Prepend system context
    messages_with_context = [system_context] + request.messages

    payload = {
        "model": "openai/gpt-oss-20b:groq",
        "messages": messages_with_context
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
