# Project Status

Current state of Forge Publisher features and known work items.

## Completed Features

### Pipeline
- [x] Text ingestion with Gutenberg header/footer stripping
- [x] Chapter/section splitting with title and author detection
- [x] AI annotation generation via Ollama (multi-server failover)
- [x] AI annotation generation via OpenAI (fallback)
- [x] Demo mode annotations when no AI provider is available
- [x] Comprehensive scientific accuracy analysis
- [x] Enhanced annotation merging (base + analysis)
- [x] EPUB building with steampunk/retro-futuristic CSS theme
- [x] Interactive popup annotation system (CSS + JavaScript)
- [x] Blitz-inspired cross-reader CSS compatibility
- [x] Cover image generation and processing
- [x] Cover image logo overlay
- [x] Annotator avatar integration (Bob icons in text)
- [x] Smart annotation placement algorithm
- [x] Enhanced typography and dialog detection
- [x] Batch manuscript processing
- [x] Audiobook generation with Edge TTS
- [x] Character-specific voice profiles for audiobooks
- [x] Intro/outro bumper support for audiobooks
- [x] Configurable publisher branding

### Django UI
- [x] Book dashboard with build status tracking
- [x] Book CRUD (create, edit, preview, delete)
- [x] Manuscript upload and management
- [x] Cover image upload
- [x] EPUB build trigger with real-time progress
- [x] Build detail view with EPUB download
- [x] AI provider management (add, edit, test, delete)
- [x] AI model discovery from Ollama servers
- [x] Primary provider selection
- [x] Annotation planning with interactive AI chat
- [x] Annotation editor
- [x] Audiobook configuration with character voice mapping
- [x] TTS provider management (Edge TTS, Coqui XTTS)
- [x] Audio asset management (upload intro/outro bumpers)
- [x] Pipeline log tailing API
- [x] Manuscript browser and editor

## Known Issues

- [ ] `comprehensive_analysis.py` has a hardcoded prompt referencing H.G. Wells' "The Star" — should be made generic based on the book being analyzed
- [ ] EPUB identifier is hardcoded as `publisher001` — should be unique per book
- [ ] Build error handling could be more granular — some failures don't report the specific stage that failed
- [ ] The `books_data/` directory structure (per-book folders with versioning) is partially implemented but not fully integrated with the main pipeline
- [ ] Django migrations reference old default values — a squash migration would clean this up

## Future Work

### High Priority
- [ ] Add test suite for pipeline modules (currently no automated tests)
- [ ] Add test suite for Django views
- [ ] Implement proper EPUB validation (epubcheck integration)
- [ ] Add user authentication to the Django UI
- [ ] Make the comprehensive analysis prompt dynamic based on book content (not hardcoded to sci-fi)

### Medium Priority
- [ ] Support for non-Gutenberg input formats (Word, Markdown, HTML)
- [ ] Chapter-level annotation planning (not just section-level)
- [ ] EPUB export with multiple theme options (not just steampunk)
- [ ] Annotation tone/style presets (scholarly, casual, humorous)
- [ ] Batch audiobook generation
- [ ] Progress websockets for real-time build updates (currently polling)
- [ ] Docker/docker-compose setup for deployment

### Low Priority / Nice to Have
- [ ] Multi-language support for annotations
- [ ] Annotation import/export (share annotation sets between books)
- [ ] EPUB reader preview in the web UI
- [ ] Analytics dashboard (build times, annotation counts, etc.)
- [ ] API endpoints for headless pipeline operation
- [ ] Plugin system for custom annotation types
- [ ] Support for Coqui XTTS voice cloning setup wizard
