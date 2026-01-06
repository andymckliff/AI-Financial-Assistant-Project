import os
from google import genai

# Initialize client with API key from environment
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("⚠️  WARNING: GEMINI_API_KEY environment variable not set")
    print("Set it with: export GEMINI_API_KEY='your-key-here'")
    client = None
else:
    client = genai.Client(api_key=api_key)

def get_gemini_response(prompt: str) -> str:
    """Call Gemini API and return text response."""
    if client is None:
        print("ERROR: Gemini client not initialized. Set GEMINI_API_KEY environment variable.")
        return None
    
    try:
        # Ensure prompt is a string
        if isinstance(prompt, bytes):
            prompt = prompt.decode('utf-8')
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        return response.text if response and hasattr(response, 'text') else None
    except Exception as e:
        print(f"Gemini API error: {e}")
        import traceback
        traceback.print_exc()
        return None
