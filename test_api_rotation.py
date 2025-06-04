#!/usr/bin/env python
# test_api_rotation.py
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to the Python path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.rag_system.model import ModelManager, APIKeyManager

# Load environment variables
load_dotenv()

def test_api_key_rotation():
    """Test that API keys are properly rotated."""
    print("Testing API key rotation...")
    
    # Create the key manager directly to check key loading
    key_manager = APIKeyManager.from_env_vars("GOOGLE_API_KEY")
    keys_found = len(key_manager.api_keys)
    
    print(f"Found {keys_found} API keys")
    if keys_found == 0:
        print("ERROR: No API keys found. Make sure they are properly set in .env file")
        return
    
    # Test rotation
    print("\nTesting rotation of keys:")
    for i in range(keys_found + 2):  # Test a few more times than keys to verify rotation
        key = key_manager.get_next_key()
        masked_key = key[:4] + "..." + key[-4:] if len(key) > 8 else "****"
        print(f"Rotation {i+1}: Using key {masked_key}")
        
    # Test with ModelManager
    print("\nTesting ModelManager integration:")
    model_manager = ModelManager(model_name="gemini-1.5-flash", temperature=0.0)
    
    # Get LLM multiple times to verify rotation
    for i in range(3):
        print(f"\nGetting LLM instance {i+1}...")
        llm = model_manager.get_llm()
        print(f"LLM created with model {model_manager.model_name}")
        
    print("\nAPI key rotation test completed")

if __name__ == "__main__":
    test_api_key_rotation()
