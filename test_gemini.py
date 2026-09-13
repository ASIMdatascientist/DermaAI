import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("API Key loaded:", bool(api_key))

if not api_key:
    print("ERROR: GEMINI_API_KEY nahi mili!")
    exit()

llm = LLM(
    model="gemini/gemini-3.6-flash",
    api_key=api_key
)

prompt = """
Explain Acne in simple words.

Include:
1. What is Acne?
2. Common symptoms
3. General skin-care information
4. When should a person consult a doctor?

Keep the answer short and educational.
"""

print("\nGemini se response aa raha hai...\n")

response = llm.call(prompt)

print("=================================")
print("GEMINI RESPONSE")
print("=================================")
print(response)