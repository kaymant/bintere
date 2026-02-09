import os
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: GEMINI_API_KEY is not set.")
    exit()

client = genai.Client(api_key=api_key)

print("🔍 Listing available models for your key...")
try:
    # Get the list of models
    for m in client.models.list():
        # The new SDK uses 'supported_actions' instead of 'supported_generation_methods'
        if "generateContent" in (m.supported_actions or []):
            # Print the clean name (e.g., 'gemini-1.5-flash')
            print(f" - {m.name.split('/')[-1]}")
            
except Exception as e:
    print(f"Error: {e}")
