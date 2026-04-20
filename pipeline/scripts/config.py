import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Configuration settings
OPENAI_API_KEY = os.getenv('OPEN_API_KEY')

# Default Ollama URLs (fallback if database not available)
_DEFAULT_OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
_DEFAULT_OLLAMA_URL2 = os.getenv('OLLAMA_URL2')
_DEFAULT_OLLAMA_URL3 = os.getenv('OLLAMA_URL3')

# These will be populated from database if available
OLLAMA_SERVERS = []
OPENAI_CONFIG = None
AI_PROVIDERS = []

def load_ai_providers_from_db():
    """Load AI provider configuration from Django database"""
    global OLLAMA_SERVERS, OPENAI_CONFIG, AI_PROVIDERS, OPENAI_API_KEY
    
    try:
        # Add Django project to path
        django_path = Path(__file__).parent.parent.parent / 'ui'
        if str(django_path) not in sys.path:
            sys.path.insert(0, str(django_path))
        
        # Setup Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'publisher_django.settings')
        import django
        django.setup()
        
        # Import the model
        from books.models import AIProvider
        
        # Get active providers ordered by priority
        providers = AIProvider.objects.filter(is_active=True).order_by('-is_primary', '-priority')
        
        if providers.exists():
            AI_PROVIDERS = list(providers)
            
            # Build Ollama servers list
            ollama_providers = providers.filter(provider_type='ollama')
            OLLAMA_SERVERS = [p.api_url for p in ollama_providers]
            
            # Get OpenAI config
            openai_provider = providers.filter(provider_type='openai').first()
            if openai_provider:
                OPENAI_CONFIG = {
                    'api_url': openai_provider.api_url,
                    'api_key': openai_provider.api_key,
                    'model': openai_provider.default_model,
                }
                if openai_provider.api_key:
                    OPENAI_API_KEY = openai_provider.api_key
            
            print(f"✅ Loaded {len(AI_PROVIDERS)} AI provider(s) from database:")
            for p in AI_PROVIDERS:
                status = "✓" if p.last_test_success else "?" if p.last_test_success is None else "✗"
                primary = " (PRIMARY)" if p.is_primary else ""
                print(f"   {status} {p.name}: {p.api_url}{primary}")
            return True
        else:
            print("⚠️  No active AI providers in database, using .env fallback")
            return False
            
    except Exception as e:
        print(f"⚠️  Could not load AI providers from database: {e}")
        return False

# Try to load from database
db_loaded = load_ai_providers_from_db()

# Fallback to .env if database not available or empty
if not OLLAMA_SERVERS:
    OLLAMA_SERVERS = [url for url in [_DEFAULT_OLLAMA_URL, _DEFAULT_OLLAMA_URL2, _DEFAULT_OLLAMA_URL3] if url]
    if OLLAMA_SERVERS:
        print(f"📋 Using .env fallback - {len(OLLAMA_SERVERS)} Ollama server(s):")
        for url in OLLAMA_SERVERS:
            print(f"   {url}")

# Validate OpenAI key (warning only, not required)
if not OPENAI_API_KEY:
    print("⚠️  OpenAI API key not configured (Ollama will be used if available)")
else:
    print(f"✅ OpenAI API Key: {'*' * 20}...{OPENAI_API_KEY[-4:]}")