#!/usr/bin/env python3
"""
Annotation System with Theme Support and EPUB Reader Compatibility
"""
from .themes import get_theme, DEFAULT_THEME, get_theme_css_variables

def get_enhanced_interactive_css_with_cover(annotator_image_data_uri, cover_image_data_uri=None, theme=None):
    """Generate enhanced CSS with annotator image, optional cover image, and theme colors.
    
    Args:
        annotator_image_data_uri: Base64 data URI for the annotator avatar image
        cover_image_data_uri: Base64 data URI for the cover image (optional)
        theme: Theme dict from themes.py (optional, defaults to DEFAULT_THEME)
    """
    if theme is None:
        theme = get_theme()
    
    colors = theme["colors"]
    typo = theme["typography"]
    style = theme["style"]
    annotator = theme["annotator"]
    icon_letter = annotator["icon_letter"]
    
    # Use theme colors with fallbacks
    primary = colors["primary"]
    secondary = colors["secondary"]
    accent = colors["accent"]
    highlight = colors["highlight"]
    background = colors["background"]
    text_color = colors["text"]
    gold = colors["gold"]
    heading_shadow = style["heading_shadow"]
    annotation_bg = style["annotation_bg"]
    border_radius = style["border_radius"]
    
    css_content = f'''
/* PUBLISHER ANNOTATION CSS FRAMEWORK */
/* Theme: {theme["name"]} */

/* CSS Variables for Theme Consistency */
:root {{
    --copper: {primary};
    --brass: {secondary};
    --bronze: {accent};
    --steel-blue: {highlight};
    --parchment: {background};
    --deep-green: {text_color};
    --gold: {gold};
    
    /* Theme semantic variables */
    --theme-primary: {primary};
    --theme-secondary: {secondary};
    --theme-accent: {accent};
    --theme-highlight: {highlight};
    --theme-background: {background};
    --theme-text: {text_color};
    --theme-gold: {gold};
    
    /* Fallbacks for older readers */
    --copper-fallback: {primary};
    --brass-fallback: {secondary};
    --bronze-fallback: {accent};
    --steel-blue-fallback: {highlight};
    --parchment-fallback: {background};
}}

/* Base Typography - Simplified */
html {{
    height: 100%;
}}

body {{
    font-family: {typo['body']};
    line-height: 1.6;
    color: var(--deep-green, {text_color});
    background: var(--parchment, {background});
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}
.steampunk-enhanced {{
    max-width: 800px;
    margin: 0 auto;
    font-size: 1.1em;
    padding: 1em;
    min-height: 100vh;
}}

/* Annotator introductory callouts */
.annotator-introduction {{
    display: flex;
    align-items: flex-start;
    gap: 1em;
    margin: 1.5em 0 2em 0;
    padding: 1.2em;
    border-left: 4px solid var(--copper, var(--copper-fallback));
    border-radius: 8px;
    background: linear-gradient(135deg, rgba(184, 115, 51, 0.08), rgba(205, 127, 50, 0.05));
    font-style: italic;
    line-height: 1.7;
}}

.annotator-introduction p {{
    margin: 0;
}}

.annotator-icon-small {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2.5em;
    height: 2.5em;
    min-width: 2.5em;
    min-height: 2.5em;
    margin-right: 0.25em;
    border: 2px solid var(--brass, var(--brass-fallback));
    border-radius: 50%;
    background-image: url('{annotator_image_data_uri}');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-color: var(--parchment, #F5F5DC);
    color: var(--bronze, var(--bronze-fallback));
    font-weight: bold;
    font-size: 1.4em;
    flex-shrink: 0;
}}

.annotator-icon-small::before {{
    content: "{icon_letter}";
}}

/* Postface container (non-interactive annotator note) */
.annotator-postface {{
    display: flex;
    align-items: flex-start;
    gap: 0.75em;
    margin: 1.5em 0 0 0;
    padding: 1em;
    border-left: 4px solid var(--copper, var(--copper-fallback));
    border-radius: 8px;
    background: linear-gradient(135deg, rgba(184, 115, 51, 0.06), rgba(205, 127, 50, 0.04));
}}

.annotator-postface .annotator-icon-small {{
    pointer-events: none;
    cursor: default;
}}

.annotator-icon-small.static {{
    pointer-events: none;
    cursor: default;
}}

.annotator-postface-text {{
    line-height: 1.6;
}}

/* Headings with Steampunk Flair */
h1, h2, h3, h4, h5, h6 {{
    font-family: {typo['heading']};
    color: var(--bronze, var(--bronze-fallback));
    text-shadow: {heading_shadow};
    margin: 1.5em 0 0.8em 0;
}}

h1 {{
    font-size: 2.5em;
    text-align: center;
    border-bottom: 3px double var(--brass, var(--brass-fallback));
    padding-bottom: 0.5em;
    margin-bottom: 1em;
}}

/* Cover Image Integration - Always include for file-based images */
.cover-page {{
    text-align: center;
    margin: 2em 0;
    padding: 1em;
}}

.cover-image-display {{
    max-width: 90%;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    border: 3px solid var(--brass, var(--brass-fallback));
}}

/* Cover Image Integration */'''

    if cover_image_data_uri:
        css_content += f'''
.cover-image {{
    max-width: 100%;
    height: auto;
    border: 5px solid var(--brass, var(--brass-fallback));
    border-radius: 10px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    background-image: url('{cover_image_data_uri}');
    background-size: cover;
    background-position: center;
    min-height: 400px;
    display: block;
    margin: 0 auto;
}}
'''

    css_content += f'''
/* INTERACTIVE ANNOTATOR SYSTEM - Enhanced for EPUB Compatibility */
.annotator-container {{
    position: relative;
    display: inline-block;
}}

/* Floating Annotator Icons - Using Actual Annotator Image */
.annotator-icon {{
    display: inline-block;
    width: 1.5em;
    height: 1.5em;
    border: 2px solid var(--brass, var(--brass-fallback));
    border-radius: 50%;
    background-image: url('{annotator_image_data_uri}');
    background-size: cover;
    background-position: center;
    cursor: pointer;
    position: relative;
    margin: 0 0.25em;
    vertical-align: super;
    transition: all 0.3s ease;
    z-index: 10;
}}

.annotator-icon::before {{
    content: "";
}}

/* Annotator Icon States */
.annotator-icon:hover,
.annotator-icon:focus {{
    transform: scale(1.2);
    filter: brightness(1.2);
    box-shadow: 0 0 8px var(--brass, var(--brass-fallback));
}}

.annotator-icon:active,
.annotator-icon.active {{
    background-color: var(--brass, var(--brass-fallback));
    box-shadow: 0 0 15px var(--brass, var(--brass-fallback));
}}

/* CSS-Only Popup (Better EPUB Compatibility) */
.annotator-popup {{
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translateX(-50%) translateY(-50%);
    width: 90vw;
    max-width: 600px;
    min-width: 300px;
    background: linear-gradient(135deg, 
        #F4E4BC 0%, 
        #E6C79C 100%);
    border: 3px solid var(--brass, var(--brass-fallback));
    border-radius: 15px;
    padding: 1.5em;
    box-shadow: 
        0 15px 40px rgba(0, 0, 0, 0.5),
        inset 0 1px 0 rgba(255, 255, 255, 0.8);
    z-index: 1000;
    font-size: 0.9em;
    line-height: 1.4;
    color: #1A1A1A;
    
    /* Hidden by default */
    display: none;
    visibility: hidden;
    opacity: 0;
    transition: all 0.3s ease;
}}

/* Show popup on icon hover/focus (CSS-only fallback) */
.annotator-container:hover .annotator-popup,
.annotator-icon:focus + .annotator-popup,
.annotator-popup:hover {{
    display: block;
    visibility: visible;
    opacity: 1;
    transform: translateX(-50%) translateY(-50%);
}}

/* JavaScript-enhanced show state */
.annotator-popup.show {{
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    transform: translateX(-50%) translateY(-50%) !important;
}}

/* Popup Header with Annotator Avatar */
.annotator-popup-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.8em;
    padding-bottom: 0.5em;
    border-bottom: 2px solid var(--brass, var(--brass-fallback));
}}

.annotator-popup-title {{
    display: flex;
    align-items: center;
    font-weight: bold;
    color: var(--bronze, var(--bronze-fallback));
    font-size: 1.1em;
}}

.annotator-popup-avatar {{
    width: 3.5em;
    height: 3.5em;
    border-radius: 50%;
    background-image: url('{annotator_image_data_uri}');
    background-size: cover;
    background-position: center;
    border: 3px solid var(--brass, var(--brass-fallback));
    margin-right: 0.8em;
    display: inline-block;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3);
}}

.annotator-popup-close {{
    background: var(--bronze, var(--bronze-fallback));
    color: white;
    border: none;
    border-radius: 50%;
    width: 1.8em;
    height: 1.8em;
    cursor: pointer;
    font-weight: bold;
    font-size: 1.2em;
    line-height: 1;
    transition: all 0.2s ease;
}}

.annotator-popup-close:hover {{
    background: var(--copper, var(--copper-fallback));
    transform: scale(1.1);
}}

/* Annotation Content */
.annotator-popup-content {{
    max-height: 60vh;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: var(--brass, var(--brass-fallback)) transparent;
}}

.annotation-point {{
    margin-bottom: 1em;
    padding: 1em;
    background: rgba(255, 255, 255, 0.8);
    border-radius: 8px;
    border-left: 4px solid var(--brass, var(--brass-fallback));
}}

.annotation-type {{
    display: flex;
    align-items: center;
    margin-bottom: 0.5em;
    font-weight: bold;
    color: var(--bronze, var(--bronze-fallback));
}}

.annotation-emoji {{
    font-size: 1.2em;
    margin-right: 0.5em;
}}

.annotation-content {{
    color: #000000;
    line-height: 1.6;
    font-weight: 400;
}}

/* INLINE CONTEXT NOTES - Marginal/tooltip notes */
.inline-note-marker {{
    position: relative;
    display: inline;
    cursor: help;
}}

.inline-note-icon {{
    display: inline-block;
    font-size: 0.9em;
    margin: 0 0.2em;
    vertical-align: super;
    padding: 0.1em 0.3em;
    background: rgba(184, 115, 51, 0.15);
    border-radius: 4px;
    border: 1px solid var(--copper, var(--copper-fallback));
    transition: all 0.2s ease;
}}

.inline-note-icon:hover {{
    background: rgba(184, 115, 51, 0.3);
    transform: scale(1.1);
}}

.inline-note-popup {{
    position: absolute;
    left: 0;
    top: 1.5em;
    width: 280px;
    max-width: 90vw;
    padding: 0.8em;
    background: linear-gradient(135deg, #FFF8E7 0%, #F4E4BC 100%);
    border: 2px solid var(--copper, var(--copper-fallback));
    border-radius: 8px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    font-size: 0.85em;
    line-height: 1.5;
    z-index: 100;
    
    /* Hidden by default */
    display: none;
    visibility: hidden;
    opacity: 0;
}}

.inline-note-marker:hover .inline-note-popup,
.inline-note-marker:focus .inline-note-popup {{
    display: block;
    visibility: visible;
    opacity: 1;
}}

.inline-note-popup blockquote {{
    margin: 0.5em 0 0 0;
    padding: 0.5em;
    border-left: 3px solid var(--brass, var(--brass-fallback));
    background: rgba(255, 255, 255, 0.5);
    font-style: italic;
    font-size: 0.95em;
}}

/* Visual Enhancements - Simplified */
.section-content {{
    text-align: justify;
    hyphens: auto;
    min-height: 100vh;
    padding-bottom: 2em;
}}

/* Paragraph Styling */
p {{
    margin: 1em 0;
    text-indent: 1.5em;
}}

p:first-child,
p.no-indent {{
    text-indent: 0;
}}

/* Drop Caps */
.drop-cap:first-letter {{
    float: left;
    font-family: "Playfair Display", serif;
    font-size: 4em;
    line-height: 0.8;
    margin: 0.1em 0.1em 0 0;
    color: var(--bronze, var(--bronze-fallback));
    text-shadow: 2px 2px 4px rgba(140, 69, 0, 0.3);
}}

/* Responsive Design */
@media screen and (max-width: 600px) {{
    body {{
        font-size: 1em;
        padding: 0.5em;
    }}
    
    .annotator-popup {{
        width: 95vw;
        max-width: none;
        font-size: 0.85em;
        padding: 1em;
        top: 50%;
        left: 50%;
        transform: translateX(-50%) translateY(-50%);
    }}
    
    .annotator-popup.show {{
        transform: translateX(-50%) translateY(-50%) !important;
    }}
    
    .annotator-container:hover .annotator-popup,
    .annotator-icon:focus + .annotator-popup,
    .annotator-popup:hover {{
        transform: translateX(-50%) translateY(-50%);
    }}
    
    .annotator-icon {{
        width: 1.3em;
        height: 1.3em;
    }}
    
    h1 {{
        font-size: 2em;
    }}
}}

/* Print Styles */
@media print {{
    .annotator-popup {{
        display: none !important;
    }}
    
    .annotator-icon {{
        background: var(--brass, var(--brass-fallback));
        color: white;
    }}
    
    .annotator-icon::after {{
        content: "[" attr(data-annotation-id) "]";
        font-size: 0.7em;
        font-weight: bold;
    }}
}}

/* Accessibility */
.annotator-icon:focus {{
    outline: 2px solid var(--steel-blue, var(--steel-blue-fallback));
    outline-offset: 2px;
}}

@media (prefers-reduced-motion: reduce) {{
    * {{
        transition: none !important;
        animation: none !important;
    }}
}}

/* High Contrast Mode */
@media (prefers-contrast: high) {{
    .annotator-icon {{
        border-width: 3px;
    }}
    
    .annotator-popup {{
        border-width: 4px;
        background: white;
        color: black;
    }}
}}
'''
    
    return css_content