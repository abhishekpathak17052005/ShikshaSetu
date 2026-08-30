import os
from google import genai

key = os.getenv("GEMINI_API_KEY")
if key:
    client = genai.Client(api_key=key)
    print("Available Gemini models:\n")
    for m in client.models.list():
        print(f"Model: {m.name}")
else:
    print("GEMINI_API_KEY environment variable not set.")