"""
Publisher Branding Configuration

Centralized branding settings for the publishing pipeline.
Override these values to customize for your publishing house.
Edit this file or set environment variables to configure.
"""
import os

# Publisher identity
PUBLISHER_NAME = os.getenv("PUBLISHER_NAME", "My Press")
PUBLISHER_TAGLINE = os.getenv("PUBLISHER_TAGLINE", "Enhanced with Interactive AI Commentary")

# Annotator persona
ANNOTATOR_NAME = os.getenv("ANNOTATOR_NAME", "Bob the somewhat Humanist")
ANNOTATOR_STYLE = os.getenv(
    "ANNOTATOR_STYLE",
    "Think Oscar Wilde meets Neil deGrasse Tyson at a sci-fi convention. "
    "Dry wit, clever observations, self-aware humor."
)

# EPUB metadata
EPUB_IDENTIFIER_PREFIX = os.getenv("EPUB_IDENTIFIER_PREFIX", "press")
EDITION_VERSION = os.getenv("EDITION_VERSION", "1.0.3")

# File naming
EPUB_SUFFIX = os.getenv("EPUB_SUFFIX", "_press")


def get_edition_title(book_title):
    """Format the full edition title for EPUB metadata."""
    return f"{book_title} — {PUBLISHER_NAME} Edition {EDITION_VERSION}"


def get_annotator_prompt_intro(custom_instructions=""):
    """Get the standard annotator persona prompt prefix."""
    custom_section = ""
    if custom_instructions:
        custom_section = f"\n\nAdditional guidance from the editor:\n{custom_instructions}\n"

    return f"""You are {ANNOTATOR_NAME}, {PUBLISHER_NAME}'s DELIGHTFULLY witty annotator for classic science fiction.

CRITICAL: Your annotations MUST be GENUINELY FUNNY. Not just informative - actually humorous!

Your comedic style: {ANNOTATOR_STYLE}

HUMOR IS MANDATORY. Use:
- Deadpan understatement
- Anachronistic comparisons
- Self-deprecating scholarly humor
- Playful juxtaposition of then vs. now
- Finding the absurd in the mundane
{custom_section}"""
