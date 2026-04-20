# Project Overview for AI Assistants

## What is Forge Publisher?

Forge Publisher is an **AI-powered manuscript-to-EPUB publishing pipeline** built as part of the Buildly Forge ecosystem. It provides:

- Text ingestion and chapter splitting from plain-text manuscripts
- AI-generated literary annotations (Ollama or OpenAI)
- Enhanced EPUB building with interactive popup annotations
- Audiobook generation with character-specific TTS voices
- A Django web UI for managing books, builds, and AI configuration

## Technology Stack

```
┌─────────────────────────────────────────────────────────┐
│                     Web UI                               │
│  Django 6.0 + Tailwind CSS (server-rendered templates)  │
├─────────────────────────────────────────────────────────┤
│                   Pipeline                               │
│  Python scripts (run on-demand, not a server)           │
│  ebooklib, Pillow, aiohttp, edge-tts                    │
├─────────────────────────────────────────────────────────┤
│                   Database                               │
│  SQLite (Django ORM)                                     │
├─────────────────────────────────────────────────────────┤
│                   AI Providers                           │
│  Ollama (local LLMs), OpenAI (cloud fallback)           │
└─────────────────────────────────────────────────────────┘
```

## Application Architecture

### Directory Structure

```
publisher/
├── pipeline/              # EPUB processing engine
│   ├── scripts/           # All pipeline modules
│   │   ├── pipeline.py    # Simple CLI orchestrator
│   │   ├── full_pipeline.py # Enhanced orchestrator with stage tracking
│   │   ├── config.py      # AI provider config (DB → .env → defaults)
│   │   ├── branding.py    # Publisher branding configuration
│   │   ├── ingest_text.py # Text cleaning and chapter splitting
│   │   ├── annotate_text.py # AI annotation generation
│   │   ├── build_epub.py  # EPUB assembly
│   │   └── ...            # CSS, covers, audio, utilities
│   ├── manuscripts/       # Input text files
│   ├── annotations/       # Generated annotation JSON
│   └── output/            # Generated EPUBs, audiobooks, logs
├── ui/                    # Django web application
│   ├── books/             # Django app
│   │   ├── models.py      # Book, EPUBBuild, AIProvider, TTS models
│   │   ├── views.py       # Main views (dashboard, build, AI config)
│   │   ├── book_views.py  # Book CRUD views
│   │   └── templates/     # HTML templates
│   └── publisher_django/  # Django project config
├── ops/                   # Startup scripts
└── devdocs/               # Developer docs
```

### Key Design Patterns

#### 1. Pipeline runs on-demand

The pipeline is not a server. The Django UI triggers builds as subprocesses:

```python
# In views.py — builds run the pipeline in a background thread
pipeline_dir = os.path.join(settings.BASE_DIR.parent, 'pipeline')
# ... subprocess call to full_pipeline.py
```

#### 2. AI Config from Database

```python
# config.py loads providers from Django DB first, falls back to .env
from books.models import AIProvider
providers = AIProvider.objects.filter(is_active=True).order_by('-is_primary', '-priority')
```

#### 3. Centralized Branding

```python
# branding.py — all publisher identity in one place
PUBLISHER_NAME = os.getenv("PUBLISHER_NAME", "My Press")
ANNOTATOR_NAME = os.getenv("ANNOTATOR_NAME", "Bob the somewhat Humanist")
```
