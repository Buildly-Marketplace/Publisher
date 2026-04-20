# Architecture

## System Overview

Forge Publisher is a two-component system:

1. **Pipeline** (`pipeline/`) — Python modules that process manuscripts into EPUBs and audiobooks
2. **UI** (`ui/`) — Django web application for managing books, triggering builds, and configuring AI

The pipeline is **not** a server. It runs on-demand as a subprocess when the Django UI triggers a build. Only the Django UI runs as a persistent service.

## Data Flow

```
Manuscript (plain text)
    │
    ▼
┌─────────────────────┐
│  ingest_text.py      │  Clean text, detect title/author, split into sections
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  annotate_text.py    │  Generate AI commentary (Ollama or OpenAI)
└─────────┬───────────┘
          │
          ▼
┌──────────────────────────┐
│  comprehensive_analysis.py│  Scientific accuracy checks, enhanced annotations
└─────────┬────────────────┘
          │
          ▼
┌─────────────────────┐
│  build_epub.py       │  Assemble EPUB with CSS, covers, interactive popups
└─────────┬───────────┘
          │
          ▼
    Enhanced EPUB
          │
          ▼ (optional)
┌─────────────────────┐
│  audio_generator.py  │  Generate audiobook with TTS voices
└─────────┬───────────┘
          │
          ▼
    Audiobook (MP3/WAV)
```

## Pipeline Scripts

### Core Pipeline

| Script | Role |
|--------|------|
| `pipeline.py` | Simple CLI orchestrator — runs ingest → annotate → build |
| `full_pipeline.py` | Enhanced orchestrator with `PipelineRunner` class and stage tracking. Used by the Django UI to run builds with progress reporting |
| `config.py` | AI provider configuration. Loads from Django database first, falls back to `.env` |
| `branding.py` | Centralized publisher branding (name, persona, edition metadata) |

### Text Processing

| Script | Role |
|--------|------|
| `ingest_text.py` | Cleans Project Gutenberg headers/footers, detects title/author, splits into chapters. Handles both plain text and HTML-formatted input |
| `annotate_text.py` | Generates annotations using the configured AI annotator persona. Supports Ollama (multi-server with failover) and OpenAI. Includes demo mode fallback |
| `comprehensive_analysis.py` | Deep analysis of scientific claims, historical accuracy, and literary themes. Produces enhanced annotation JSON |

### EPUB Building

| Script | Role |
|--------|------|
| `build_epub.py` | Main EPUB assembly. Creates chapters, applies CSS, embeds covers and annotation popups |
| `publisher_blitz.py` | Blitz-inspired EPUB CSS framework for cross-reader compatibility |
| `enhanced_bob_system.py` | Steampunk CSS theme with cover image integration |
| `enhanced_interactive.py` | Interactive popup CSS and JavaScript for annotation display |
| `enhanced_typography.py` | Typography enhancements, dialog detection, chapter structure |
| `smart_placement.py` | Algorithm for placing annotation icons within text flow |
| `avatar_styling.py` | Annotator avatar base64 encoding and CSS styling |
| `annotation_formatter.py` | Format annotation data for display in EPUB |

### Visual Assets

| Script | Role |
|--------|------|
| `generate_images.py` | AI-generated cover images |
| `cover_integration.py` | Cover image processing and optimization for EPUB |
| `cover_processor.py` | Cover image processing with logo overlay |
| `create_cover.py` | Programmatic cover image creation |
| `logo_utils.py` | Publisher logo SVG and data URI utilities |
| `bob_image_utils.py` | Annotator avatar image data URI utilities |

### Audio

| Script | Role |
|--------|------|
| `audio_generator.py` | Audiobook generation with character-specific voices |
| `generate_audiobook.py` | Extended audiobook generation with intro/outro bumpers |

### Utilities

| Script | Role |
|--------|------|
| `batch_process_manuscripts.py` | Process all manuscripts in the `manuscripts/` directory |

## Django UI

### Models

| Model | Purpose |
|-------|---------|
| `Book` | Core book record — title, author, status, manuscript/cover paths |
| `EPUBBuild` | Build record — tracks stage, progress, output path, logs |
| `AIProvider` | AI provider config — Ollama/OpenAI URL, API key, model, priority |
| `TTSProvider` | TTS provider config — Edge TTS or Coqui XTTS |
| `VoiceProfile` | Voice configuration for TTS |
| `CharacterVoiceMapping` | Maps book characters to voice profiles |
| `AudioBuild` | Audiobook build record with status tracking |

### Key Views

| View | URL | Purpose |
|------|-----|---------|
| `book_dashboard` | `/dashboard/` | Main dashboard — list books, trigger builds |
| `book_create` | `/book/create/` | Create new book with manuscript upload |
| `book_edit` | `/book/<id>/edit/` | Edit book metadata and manuscript |
| `build_epub_view` | `/build/<id>/` | Trigger and track EPUB build |
| `build_detail` | `/build-detail/<id>/` | View build results, download EPUB |
| `ai_config` | `/ai/` | Manage AI providers |
| `annotation_planning` | `/book/<id>/annotation/` | Interactive AI annotation planning |
| `audiobook_config` | `/audiobook/<id>/` | Configure voices and build audiobook |
| `tts_config` | `/tts/` | Manage TTS providers |

### Template Structure

Templates are in `ui/books/templates/` using a base template with Tailwind CSS styling. The UI uses server-rendered HTML (no SPA framework).

## Configuration Hierarchy

AI provider configuration uses a priority system:

1. **Django Database** — AI providers configured through the web UI (`/ai/`)
2. **Environment Variables** — `.env` file in the `pipeline/` directory
3. **Defaults** — `http://localhost:11434` for Ollama

The `config.py` module loads from the database first. If Django is not available or no providers are configured, it falls back to `.env` values.
