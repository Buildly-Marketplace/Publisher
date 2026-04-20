#!/usr/bin/env python3
"""
Ollama setup helper for Forge Publisher Pipeline
"""
import requests
import subprocess
import sys
from pathlib import Path

# Add the scripts directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from scripts.config import OLLAMA_URL
except ImportError:
    OLLAMA_URL = "http://localhost:11434"

RECOMMENDED_MODELS = [
    {
        "name": "llama3.2",
        "description": "Latest Llama model - excellent for reasoning and text analysis",
        "size": "~7GB",
        "best_for": "Literary analysis, scholarly writing"
    },
    {
        "name": "llama3.1",
        "description": "Proven model with great performance for complex text tasks",
        "size": "~5GB", 
        "best_for": "Academic annotation, contextual analysis"
    },
    {
        "name": "mistral",
        "description": "Excellent French-origin model, great for nuanced text work",
        "size": "~4GB",
        "best_for": "Creative writing, satirical commentary"
    },
    {
        "name": "qwen2.5",
        "description": "Strong Chinese model with excellent text comprehension",
        "size": "~4.5GB",
        "best_for": "Text analysis, structured output"
    }
]

def check_ollama_running():
    """Check if Ollama is running and accessible"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_installed_models():
    """Get list of currently installed models"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            return [model["name"] for model in response.json().get("models", [])]
    except:
        pass
    return []

def install_model(model_name):
    """Install a model using ollama pull"""
    print(f"📥 Installing {model_name}...")
    try:
        result = subprocess.run(
            ["ollama", "pull", model_name], 
            capture_output=True, 
            text=True, 
            timeout=1800  # 30 minutes timeout
        )
        if result.returncode == 0:
            print(f"✅ {model_name} installed successfully!")
            return True
        else:
            print(f"❌ Failed to install {model_name}: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏱️  Installation of {model_name} timed out")
        return False
    except FileNotFoundError:
        print("❌ Ollama CLI not found. Please install Ollama first.")
        return False
    except Exception as e:
        print(f"❌ Error installing {model_name}: {e}")
        return False

def main():
    print("🦙 Ollama Setup Helper for Forge Publisher")
    print("=" * 50)
    
    # Check if Ollama is running
    if not check_ollama_running():
        print(f"❌ Cannot connect to Ollama at {OLLAMA_URL}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Make sure Ollama is installed: https://ollama.ai")
        print("2. Start Ollama: `ollama serve`")
        print("3. Check if the URL is correct in your .env file")
        return
    
    print(f"✅ Ollama is running at {OLLAMA_URL}")
    
    # Get currently installed models
    installed = get_installed_models()
    print(f"\n📦 Currently installed models: {installed if installed else 'None'}")
    
    # Show recommendations
    print("\n🎯 Recommended models for literary annotation work:")
    for i, model in enumerate(RECOMMENDED_MODELS, 1):
        status = "✅ INSTALLED" if any(model["name"] in inst for inst in installed) else "⬇️  AVAILABLE"
        print(f"\n{i}. {model['name']} - {status}")
        print(f"   📝 {model['description']}")
        print(f"   💾 Size: {model['size']}")
        print(f"   🎨 Best for: {model['best_for']}")
    
    # Interactive installation
    print(f"\n{'🎉 You have some models installed!' if installed else '📥 Would you like to install a model?'}")
    
    if not installed:
        print("\nRecommended: Start with llama3.1 for the best balance of performance and size")
        choice = input("Install llama3.1? (y/n): ").strip().lower()
        if choice == 'y':
            install_model("llama3.1")
    else:
        print("\nInstall additional models? Enter model name or 'q' to quit:")
        while True:
            choice = input("Model name: ").strip()
            if choice.lower() in ['q', 'quit', 'exit', '']:
                break
            install_model(choice)
    
    # Final status
    final_models = get_installed_models()
    print(f"\n🎉 Setup complete! Installed models: {final_models}")
    
    if final_models:
        print("\n🚀 You can now run the pipeline:")
        print("   python3 -m scripts.pipeline")
    else:
        print("\n⚠️  No models installed. The pipeline will use demo mode.")

if __name__ == "__main__":
    main()