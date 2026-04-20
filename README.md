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
- **Audiobook Config** (`/audiobook/<id>/`) — Configure character voices, build audiobooks
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
| `audio_generator.py` | Audiobook generation with character voices |
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
# Forge Communicator

![License](https://img.shields.io/badge/license-Buildly%20Forge-blue)

A modern, real-time team communication platform built with FastAPI, HTMX, and WebSockets. Features Slack-like channels, threading, Buildly Labs integration, and white-label branding support.

## Features

- **Real-time messaging** with WebSocket support
- **Message threading** for organized conversations
- **Channels** - Public and private channels per workspace
- **Multi-workspace** - Users can belong to multiple workspaces
- **OAuth Support** - Google and Buildly Labs SSO
- **White-label branding** - Customizable colors, logos, and themes
- **Dark mode** - Beautiful futuristic dark theme by default
- **Buildly Labs Integration** - Sync products and artifacts
- **Push notifications** - Web push via VAPID
- **Search** - Full-text search across messages

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis (optional, for caching)

### Installation

1. **Clone and install dependencies:**

   ```bash
   git clone https://github.com/buildly/ForgeCommunicator.git
   cd ForgeCommunicator
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Set up your environment:**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the database:**

   ```bash
   # Using Docker
   docker run -d --name forge-db \
     -e POSTGRES_USER=forge \
     -e POSTGRES_PASSWORD=forge \
     -e POSTGRES_DB=forge_communicator \
     -p 5432:5432 postgres:14
   ```

4. **Run the application:**

   ```bash
   uvicorn app.main:app --reload
   ```

5. **Open** http://localhost:8000

---

## Admin Setup

### Setting Up Your First Platform Admin

ForgeCommunicator uses environment variables to designate platform administrators. This is more secure than hardcoded credentials.

**Before your first deployment:**

1. Set the `PLATFORM_ADMIN_EMAILS` environment variable with your admin email(s):

   ```bash
   # Single admin
   PLATFORM_ADMIN_EMAILS=admin@yourcompany.com

   # Multiple admins (comma-separated)
   PLATFORM_ADMIN_EMAILS=admin@yourcompany.com,devops@yourcompany.com
   ```

2. Start the application and **register** with one of those email addresses

3. You will automatically have platform admin access!

### What Can Platform Admins Do?

- Access the **Admin Dashboard** at `/admin`
- Manage all users across the platform
- View and manage all workspaces
- Configure branding and themes at `/admin/config/branding`
- Toggle user admin status
- Deactivate/reactivate user accounts

### Adding More Admins Later

**Option 1:** Add their email to `PLATFORM_ADMIN_EMAILS` before they register

**Option 2:** Existing platform admin can grant admin access:
1. Go to `/admin/users`
2. Find the user
3. Click "Toggle Admin"

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://forge:forge@localhost:5432/forge_communicator` |
| `SECRET_KEY` | Session encryption key | (required in production) |
| `PLATFORM_ADMIN_EMAILS` | Comma-separated admin emails | `""` |
| `REGISTRATION_MODE` | `open`, `invite_only`, or `closed` | `open` |

### Branding

| Variable | Description | Default |
|----------|-------------|---------|
| `BRAND_NAME` | Product name | `Communicator` |
| `BRAND_COMPANY` | Company name | `Buildly` |
| `BRAND_LOGO_URL` | Logo URL | `/static/forge-logo.png` |
| `BRAND_PRIMARY_COLOR` | Primary theme color | `#3b82f6` |
| `BRAND_SECONDARY_COLOR` | Secondary color | `#0f172a` |
| `BRAND_ACCENT_COLOR` | Accent color | `#a855f7` |

### OAuth Providers

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth secret |
| `GOOGLE_REDIRECT_URI` | Callback URL |
| `BUILDLY_CLIENT_ID` | Buildly Labs OAuth client ID |
| `BUILDLY_CLIENT_SECRET` | Buildly Labs OAuth secret |

---

## Development

### Seed Demo Data

```bash
python scripts/seed.py
```

This creates demo users (alice, bob, carol) and a sample workspace.

### Run Tests

```bash
pytest
```

### Project Structure

```
app/
├── models/          # SQLAlchemy models
├── routers/         # FastAPI route handlers
├── services/        # Business logic
├── templates/       # Jinja2 templates
└── static/          # CSS, JS, images
```

---

## Deployment

### Docker

```bash
docker build -t forge-communicator .
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e SECRET_KEY=your-secret-key \
  -e PLATFORM_ADMIN_EMAILS=admin@yourcompany.com \
  forge-communicator
```

### Railway / Render / Fly.io

Set the environment variables in your platform's dashboard and deploy.

---

## License

This project uses the Buildly Forge License.

- Free for personal, educational, and evaluation use  
- Commercial use requires a license from Buildly  
- Converts to Apache 2.0 two years after purchase  

See [LICENSE.md](./LICENSE.md) for details.

For commercial use: https://buildly.io/licensing

---

Built with love by [Buildly](https://buildly.io)
