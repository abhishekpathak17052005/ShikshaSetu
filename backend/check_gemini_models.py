import os
import google.generativeai as genai

key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=key)

print("Available Gemini models:\n")
for m in genai.list_models():
    if 'embed' in m.name.lower():
        print(f"Model: {m.name}")
        print(f"Methods: {m.supported_generation_methods}")