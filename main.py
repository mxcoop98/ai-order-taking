from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

def load_menu_json():
    with open("BWW_Menu.json", "r", encoding="utf-8") as f:
        items = json.load(f)

    formatted = []
    for item in items:
        size_price_info = ", ".join(
            [f"{s} - ${p}" for s, p in zip(item["sizes"], item["prices"])]
        )
        formatted_item = (
            f"{item['item_name']} ({item['category']}) - {item['description']}\n"
            f"Options: {size_price_info} | Tags: {', '.join(item['tags'])}"
        )
        formatted.append(formatted_item)

    return "\n\n".join(formatted)


MENU_TEXT = load_menu_json()

@app.post("/voice", response_class=PlainTextResponse)
async def voice(
    Called: str = Form(...),
    Caller: str = Form(...),
    CallSid: str = Form(...),
    SpeechResult: str = Form(None),
    SpeechConfidence: str = Form(None),
):
    user_input = SpeechResult or "I'd like to place an order."

    print(f"User said: {user_input}")

    chat_resp = await order(user_input)

    try:
        reply_text = chat_resp.choices[0].message.content
    except Exception as e:
        reply_text = f"Sorry, there was an error. {str(e)}"

    print(f"AI Reply: {reply_text}")

    twiml = f"""
    <Response>
        <Say>{reply_text}</Say>
        <Pause length="1"/>
        <Gather input="speech" action="/voice" method="POST">
            <Say>You can continue your order when you're ready.</Say>
        </Gather>
    </Response>
    """

    return twiml.strip()


async def order(user_input: str):
    """Sends user input to OpenAI ChatCompletion API"""
    system_prompt = f"""You are a food ordering assistant for Buffalo Wild Wings.
Here’s the current menu:

{MENU_TEXT}

Your job is to guide the customer through placing an order. If they ask about prices or sizes, respond based on the listed options. If they mention something not listed, offer an alternative. Ask clarifying questions when needed."""

    chat_completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )
    return chat_completion
