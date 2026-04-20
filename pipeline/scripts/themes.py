"""
Annotation Theme Presets

Each theme defines:
- Annotator persona (name, style, icon letter)
- Color palette (CSS variables)
- Typography (font families)
- Note types (labels, colors, emojis)
- Visual style (background, borders, animations)

Themes are selected per-book and passed through the build pipeline.
Custom overrides can be applied on top of any preset.
"""

THEMES = {
    "bobs_somewhat_humanist": {
        "name": "Bob's Somewhat Humanist",
        "description": "Steampunk-inspired witty commentary. Think Oscar Wilde meets Neil deGrasse Tyson.",
        "annotator": {
            "name": "Bob the somewhat Humanist",
            "icon_letter": "B",
            "style": (
                "Think Oscar Wilde meets Neil deGrasse Tyson at a sci-fi convention. "
                "Dry wit, clever observations, self-aware humor."
            ),
            "prompt_tone": (
                "Your annotations MUST be GENUINELY FUNNY. Not just informative - actually humorous!\n"
                "Use: deadpan understatement, anachronistic comparisons, self-deprecating scholarly humor, "
                "playful juxtaposition of then vs. now, finding the absurd in the mundane."
            ),
        },
        "colors": {
            "primary": "#B87333",        # copper
            "secondary": "#CD7F32",      # brass
            "accent": "#8C4500",         # bronze
            "highlight": "#4682B4",      # steel-blue
            "background": "#F5F5DC",     # parchment
            "text": "#2C5234",           # deep-green
            "gold": "#FFD700",
        },
        "typography": {
            "body": '"Crimson Text", "Georgia", "Times New Roman", serif',
            "heading": '"Playfair Display", "Georgia", serif',
            "mono": '"JetBrains Mono", "Courier New", monospace',
        },
        "note_types": [
            {"label": "Science Note", "color": "#4682B4", "emoji": "🔬"},
            {"label": "Context Note", "color": "#FFD700", "emoji": "📚"},
            {"label": "Futurist Note", "color": "#CD7F32", "emoji": "🚀"},
            {"label": "Humanist Note", "color": "#9932CC", "emoji": "🎭"},
        ],
        "style": {
            "border_style": "double",
            "border_radius": "8px",
            "annotation_bg": "linear-gradient(135deg, rgba(184, 115, 51, 0.08), rgba(205, 127, 50, 0.05))",
            "heading_shadow": "1px 1px 2px rgba(140, 69, 0, 0.3)",
            "animations": True,
        },
    },

    "scientific_review": {
        "name": "Scientific Review",
        "description": "Clean, academic commentary with a modern science focus. Professional and informative.",
        "annotator": {
            "name": "The Annotator",
            "icon_letter": "A",
            "style": (
                "Precise, evidence-based, and curious. Explain complex ideas accessibly "
                "while maintaining scholarly rigor. Occasional dry humor welcome."
            ),
            "prompt_tone": (
                "Your annotations should be CLEAR and INSIGHTFUL. Focus on accuracy and accessibility.\n"
                "Use: precise scientific language, accessible explanations, evidence-based observations, "
                "connections to current research, and thought-provoking questions."
            ),
        },
        "colors": {
            "primary": "#2563EB",        # blue-600
            "secondary": "#3B82F6",      # blue-500
            "accent": "#1E40AF",         # blue-800
            "highlight": "#10B981",      # emerald-500
            "background": "#F8FAFC",     # slate-50
            "text": "#1E293B",           # slate-800
            "gold": "#F59E0B",           # amber-500
        },
        "typography": {
            "body": '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
            "heading": '"Space Grotesk", "Inter", sans-serif',
            "mono": '"JetBrains Mono", "Fira Code", monospace',
        },
        "note_types": [
            {"label": "Analysis", "color": "#2563EB", "emoji": "🔍"},
            {"label": "Historical Context", "color": "#F59E0B", "emoji": "📖"},
            {"label": "Scientific Note", "color": "#10B981", "emoji": "🧪"},
            {"label": "Discussion", "color": "#8B5CF6", "emoji": "💬"},
        ],
        "style": {
            "border_style": "solid",
            "border_radius": "6px",
            "annotation_bg": "linear-gradient(135deg, rgba(37, 99, 235, 0.05), rgba(59, 130, 246, 0.03))",
            "heading_shadow": "none",
            "animations": False,
        },
    },

    "cyberpunk_neon": {
        "name": "Cyberpunk Neon",
        "description": "Dark terminal aesthetic with neon accents. Sharp, irreverent sci-fi commentary.",
        "annotator": {
            "name": "GHOST://READER",
            "icon_letter": "G",
            "style": (
                "A rogue AI literary critic jacked into the text. Sharp, irreverent, "
                "occasionally philosophical. Speaks in clipped, punchy sentences."
            ),
            "prompt_tone": (
                "Your annotations should be SHARP and PUNCHY. Channel cyberpunk sensibility.\n"
                "Use: clipped sentences, tech metaphors, irreverent observations, "
                "connections to digital culture, and occasional existential musings."
            ),
        },
        "colors": {
            "primary": "#00FF41",        # matrix green
            "secondary": "#FF00FF",      # magenta
            "accent": "#00BFFF",         # deep sky blue
            "highlight": "#FFD700",      # gold
            "background": "#0D0D0D",     # near-black
            "text": "#E0E0E0",           # light gray
            "gold": "#FF6B35",           # neon orange
        },
        "typography": {
            "body": '"JetBrains Mono", "Fira Code", "Courier New", monospace',
            "heading": '"Space Grotesk", "Orbitron", sans-serif',
            "mono": '"JetBrains Mono", "Fira Code", monospace',
        },
        "note_types": [
            {"label": "SCAN://", "color": "#00FF41", "emoji": "🖥️"},
            {"label": "CONTEXT://", "color": "#FF00FF", "emoji": "📡"},
            {"label": "PREDICT://", "color": "#00BFFF", "emoji": "⚡"},
            {"label": "REFLECT://", "color": "#FFD700", "emoji": "🧠"},
        ],
        "style": {
            "border_style": "solid",
            "border_radius": "2px",
            "annotation_bg": "linear-gradient(135deg, rgba(0, 255, 65, 0.06), rgba(255, 0, 255, 0.04))",
            "heading_shadow": "0 0 10px rgba(0, 255, 65, 0.3)",
            "animations": True,
        },
    },

    "textbook_classic": {
        "name": "Textbook Classic",
        "description": "Traditional academic textbook style. Neutral, thorough, educational.",
        "annotator": {
            "name": "Editor",
            "icon_letter": "Ed",
            "style": (
                "Thorough, balanced, and educational. Provide context that enriches understanding "
                "without inserting strong opinions. Let the text speak for itself."
            ),
            "prompt_tone": (
                "Your annotations should be EDUCATIONAL and BALANCED. Write like a quality textbook.\n"
                "Use: clear explanations, relevant context, balanced analysis, "
                "connections to broader themes, and questions that encourage critical thinking."
            ),
        },
        "colors": {
            "primary": "#374151",        # gray-700
            "secondary": "#6B7280",      # gray-500
            "accent": "#1F2937",         # gray-800
            "highlight": "#DC2626",      # red-600 (for important notes)
            "background": "#FFFFFF",     # white
            "text": "#111827",           # gray-900
            "gold": "#B45309",           # amber-700
        },
        "typography": {
            "body": '"Georgia", "Times New Roman", "Palatino", serif',
            "heading": '"Georgia", "Times New Roman", serif',
            "mono": '"Courier New", "Courier", monospace',
        },
        "note_types": [
            {"label": "Editor's Note", "color": "#374151", "emoji": "✏️"},
            {"label": "Historical Note", "color": "#B45309", "emoji": "📜"},
            {"label": "Technical Note", "color": "#DC2626", "emoji": "⚙️"},
            {"label": "Discussion Point", "color": "#059669", "emoji": "💡"},
        ],
        "style": {
            "border_style": "solid",
            "border_radius": "0px",
            "annotation_bg": "rgba(243, 244, 246, 0.8)",
            "heading_shadow": "none",
            "animations": False,
        },
    },
}

DEFAULT_THEME = "bobs_somewhat_humanist"


def get_theme(theme_slug=None):
    """Get a theme config by slug. Falls back to default."""
    if theme_slug and theme_slug in THEMES:
        return THEMES[theme_slug]
    return THEMES[DEFAULT_THEME]


def get_theme_choices():
    """Return choices suitable for Django model field."""
    return [(slug, t["name"]) for slug, t in THEMES.items()]


def get_theme_css_variables(theme):
    """Generate CSS custom property declarations from a theme's color palette."""
    colors = theme["colors"]
    return f"""
:root {{
    --theme-primary: {colors['primary']};
    --theme-secondary: {colors['secondary']};
    --theme-accent: {colors['accent']};
    --theme-highlight: {colors['highlight']};
    --theme-background: {colors['background']};
    --theme-text: {colors['text']};
    --theme-gold: {colors['gold']};
}}"""


def get_annotator_prompt(theme, custom_instructions=""):
    """Build the full annotator system prompt from a theme."""
    ann = theme["annotator"]
    notes = theme["note_types"]
    note_list = "\n".join(
        f"• **{n['label']}**: Provide commentary through this lens"
        for n in notes
    )
    custom_section = ""
    if custom_instructions:
        custom_section = f"\n\nAdditional guidance from the editor:\n{custom_instructions}\n"

    return f"""You are {ann['name']}, the annotator for this edition.

Your style: {ann['style']}

{ann['prompt_tone']}
{custom_section}
For each section, provide 2-3 concise commentary notes using these lenses:
{note_list}

IMPORTANT: Your annotations MUST directly reference specific content from each section.
Quote or paraphrase specific phrases, events, or imagery from the text."""
