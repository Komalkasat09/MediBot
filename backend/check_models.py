import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("ERROR: GOOGLE_API_KEY not found in environment variables!")
    print("Please create a .env file with your API key.")
    exit(1)

genai.configure(api_key=GOOGLE_API_KEY)

print("🔍 Checking available Gemini models...\n")

try:
    # List all available models
    models = genai.list_models()
    
    print("Available models that support generateContent:\n")
    print("-" * 80)
    
    generation_models = []
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            generation_models.append(model)
            print(f"✅ {model.name}")
            print(f"   Display Name: {model.display_name}")
            print(f"   Description: {model.description}")
            print(f"   Input token limit: {model.input_token_limit}")
            print(f"   Output token limit: {model.output_token_limit}")
            print("-" * 80)
    
    if generation_models:
        print(f"\n✨ Found {len(generation_models)} models that support text generation")
        print(f"\n💡 Recommended model to use: {generation_models[0].name}")
    else:
        print("\n❌ No models found that support generateContent")
        print("Please check your API key and make sure it's valid.")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure your API key is correct")
    print("2. Check if you have internet connection")
    print("3. Verify your API key has the necessary permissions")