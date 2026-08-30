import os
import google.generativeai as genai
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

print(f"GEMINI_API_KEY length: {len(GEMINI_API_KEY)}")
print(f"GROQ_API_KEY length: {len(GROQ_API_KEY)}")

print("\n--- Testing Gemini ---")
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content("Hello, this is a test. Reply OK.")
        print("Gemini response:", response.text)
    except Exception as e:
        print("Gemini error:", e)
else:
    print("No Gemini key configured.")

print("\n--- Testing Groq ---")
if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Hello, this is a test. Reply OK."}],
            max_tokens=10
        )
        print("Groq response:", completion.choices[0].message.content)
    except Exception as e:
        print("Groq error:", e)
else:
    print("No Groq key configured.")

