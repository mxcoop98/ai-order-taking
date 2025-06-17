from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
from openai import OpenAI
from dotenv import load_dotenv
import os
import csv
import chardet

# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

with open("BWW_Menu.csv", "rb") as f:
    result = chardet.detect(f.read())
    print(result)

# Load menu from CSV with updated field names and parse size/price pairs
def load_menu():
    menu_items = []
    with open("BWW_Menu.csv", newline='', encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",")

        reader.fieldnames = [field.strip().replace('"', '') for field in reader.fieldnames]
        
        print("Detected headers:", reader.fieldnames)
        
        expected_fields = {"Category", "Item Name", "Description", "Available Sizes", "Prices", "Tags"}
        if not expected_fields.issubset(set(reader.fieldnames)):
            raise ValueError(f"CSV file is missing required fields. Found: {reader.fieldnames}")

        for row in reader:
            sizes = [s.strip() for s in row['Available Sizes'].split("/")]
            prices = [p.strip() for p in row['Prices'].split("/")]

            if len(sizes) != len(prices):
                size_price_info = "Invalid size/price pairing"
            else:
                size_price_info = ", ".join([f"{size} - ${price}" for size, price in zip(sizes, prices)])

            item_line = (
                f"{row['Item Name']} ({row['Category']}) - {row['Description']}\n"
                f"Options: {size_price_info} | Tags: {row['Tags']}"
            )
            menu_items.append(item_line.strip())

    return "\n\n".join(menu_items)

MENU_TEXT = load_menu()

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
