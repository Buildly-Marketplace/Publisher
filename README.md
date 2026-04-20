# Forge Publisher

An AI-powered publishing pipeline that transforms plain-text manuscripts into richly styled, annotated EPUB ebooks and audiobooks. Built as part of the [Buildly Forge](https://github.com/buildly-release-management) ecosystem.

## What It Does

Forge Publisher takes a manuscript (plain text) and runs it through an automated pipeline:

1. **Ingest** — Clean and parse text, split into chapters/sections
2. **Analyze** — AI-powered analysis of themes, characters, scientific accuracy
3. **Annotate** — Generate witty, scholarly commentary on each section using a configurable AI persona
4. **Build EPUB** — Produce a styled EPUB with interactive popup annotations, custom covers, and enhanced typography
5. **Generate Audiobook** — Create chapter-by-chapter audio with character-specific TTS voices

Everything is managed through a Django web UI with dashboards, AI provider configuration, and build tracking.

## Features

- **AI Annotation Pipeline** — Ollama (local) or OpenAI for generating literary commentary
- **Interactive EPUB Output** — Steampunk-inspired styling with popup annotations and custom covers
- **Audiobook Generation** — Edge TTS and Coqui XTTS support with per-character voice profiles
- **Django Web Dashboard** — Book management, build tracking, AI provider config, annotation planning
- **Multi-Server Ollama** — Failover across multiple Ollama instances
- **Configurable Branding** — Publisher name, annotator persona, logos, and edition metadata

## Architecture

```
publisher/
├── pipeline/              # EPUB processing engine
│   ├── scripts/           # Python pipeline modules
│   ├── manuscripts/       # Input: plain-text manuscripts
│   ├── annotations/       # Generated: AI annotation JSON
│   └── output/            # Generated: EPUBs, audiobooks, logs
├── ui/                    # Django web application
│   ├── books/             # Django app (models, views, templates)
│   └── publisher_django/  # Django project settings
├── ops/                   # Operations & startup scripts
├── .ai_prompt/            # AI assistant coding standards
└── devdocs/               # Developer documentation
```

## Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) (recommended) or an OpenAI API key
- ffmpeg (for audiobook generation)

### Installation

```bash
git clone <repo-url> publisher
cd publisher

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure the pipeline
cp pipeline/.env.example pipeline/.env
# Edit pipeline/.env with your Ollama URL or OpenAI key
```

### Start the UI

```bash
# Using the ops script (recommended)
./ops/startup.sh start

# Or manually
cd ui
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Then open http://localhost:8000/dashboard/

### Run the Pipeline (CLI)

```bash
cd pipeline

# Process a single manuscript
python -m scripts.pipeline manuscripts/your_book.txt

# Or use the full pipeline with stage tracking
python -m scripts.full_pipeline manuscripts/your_book.txt --output output/
```

## Configuration

### AI Providers

Configure AI providers through the web UI at `/ai/` or via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_URL` | Primary Ollama server | `http://localhost:11434` |
| `OLLAMA_URL2` | Secondary Ollama server (failover) | — |
| `OPEN_API_KEY` | OpenAI API key (fallback) | — |

### Annotation Themes

Select from built-in annotation themes (or create your own) through the web UI when editing a book. Themes control the annotator name, style, colors, and tone. Available presets:

- `bobs_somewhat_humanist` — Dry wit meets scholarly insight (default)
- `scientific_review` — Peer-review style analysis
- `cyberpunk_neon` — Edgy cyberpunk commentary
- `textbook_classic` — Traditional academic annotation

### Branding

Customize your publishing identity in `pipeline/scripts/branding.py` or via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PUBLISHER_NAME` | Your publisher name | `My Press` |
| `ANNOTATOR_NAME` | AI annotator persona name | `Bob the somewhat Humanist` |
| `EDITION_VERSION` | Edition version string | `1.0.3` |
| `EPUB_SUFFIX` | Output filename suffix | `_press` |

### Django Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Secret key (change in production!) | insecure default |
| `DJANGO_DEBUG` | Debug mode | `True` |
| `DJANGO_ALLOWED_HOSTS` | Allowed hosts (comma-separated) | `localhost,127.0.0.1` |

## Web UI Features

- **Dashboard** (`/dashboard/`) — List books, trigger builds, track status
- **Book Management** (`/book/create/`, `/book/<id>/edit/`) — Create/edit books, upload manuscripts and covers
- **EPUB Build** (`/build/<id>/`) — Background build with real-time stage tracking
- **AI Configuration** (`/ai/`) — Add/edit/test AI providers, set primary, discover models
- **Annotation Planning** (`/book/<id>/annotation/`) — Interactive AI chat to plan annotation approach
- **Audiobook Config** (`/audiobook/<id>/`) — Configure voices, upload stingers & music, set legal disclaimer, build audiobooks
- **TTS Configuration** (`/tts/`) — Manage TTS providers (Edge TTS, Coqui XTTS)

## Pipeline Modules

| Module | Purpose |
|--------|---------|
| `pipeline.py` | Main orchestrator — ingest, annotate, build |
| `full_pipeline.py` | Enhanced orchestrator with stage tracking (used by UI) |
| `ingest_text.py` | Text cleaning, chapter splitting |
| `annotate_text.py` | AI annotation generation |
| `comprehensive_analysis.py` | Deep text analysis for scientific accuracy |
| `build_epub.py` | EPUB assembly with styling and covers |
| `audio_generator.py` | TTS engine abstraction (Edge TTS, XTTS, etc.) |
| `generate_audiobook.py` | Full audiobook generation with chapter audio |
| `themes.py` | Configurable annotation theme presets |
| `branding.py` | Centralized publisher branding configuration |
| `config.py` | AI provider config (database or .env fallback) |

## Development

See [devdocs/](devdocs/) for developer documentation including architecture details, open work items, and contribution guidelines.

### Running Tests

```bash
source .venv/bin/activate
cd ui
python manage.py test
```

## License

See [LICENSE](LICENSE) for details.
