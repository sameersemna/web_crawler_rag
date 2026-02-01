#!/usr/bin/env python3
"""
Check available Gemini models for your API key
"""
import httpx
import json
import sys

# Read API key from .env
API_KEY = "AIzaSyCG5Ug2VPpHMNgxnw_PSl86Zqc4XFUInJk"

def list_models():
    """List all available Gemini models"""
    url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"
    
    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        print("=" * 60)
        print("AVAILABLE GEMINI MODELS:")
        print("=" * 60)
        
        if "models" in data:
            for model in data["models"]:
                name = model.get("name", "Unknown")
                display_name = model.get("displayName", "")
                supported = model.get("supportedGenerationMethods", [])
                
                print(f"\nModel: {name}")
                print(f"  Display Name: {display_name}")
                print(f"  Supported Methods: {', '.join(supported)}")
                
                if "generateContent" in supported:
                    print(f"  ✅ Can use for generateContent")
        else:
            print("No models found in response")
            print(json.dumps(data, indent=2))
        
        print("\n" + "=" * 60)
        return data
        
    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    list_models()
