import os
import sys
from dotenv import load_dotenv
from google import genai

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")

def main():
    client = genai.Client(api_key=API_KEY)
    arg = sys.argv
    if len(arg) == 1:
        print("Please enter a prompt")
        exit(1)
    prompt = arg[1]
    response = client.models.generate_content(model="gemini-2.0-flash-001", contents=prompt)
    print(response.text)
    print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
    print(f"Response tokens: {response.usage_metadata.candidates_token_count}")

if __name__ == "__main__":
    main()
