"""
Publisher Logo Integration
Handles logo display and data URI conversion for branding consistency.
Replace PUBLISHER_LOGO_SVG with your own logo SVG to customize.
"""
import base64
from pathlib import Path

# Default publisher logo as SVG — replace with your own branding
PUBLISHER_LOGO_SVG = """
<svg width="400" height="100" viewBox="0 0 400 100" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="textGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#cd853f"/>
            <stop offset="50%" stop-color="#daa520"/>
            <stop offset="100%" stop-color="#cd853f"/>
        </linearGradient>
    </defs>
    <rect width="400" height="100" rx="8" fill="#1a1a2e"/>
    <text x="200" y="60" font-family="Georgia, serif" font-size="32" font-weight="bold"
          fill="url(#textGrad)" text-anchor="middle">
        Publisher
    </text>
    <text x="200" y="85" font-family="Georgia, serif" font-size="14"
          fill="#888" text-anchor="middle">
        Enhanced Editions
    </text>
</svg>
"""

def get_publisher_logo_data_uri():
    """Get the publisher logo as a data URI for embedding in CSS/HTML"""
    logo_b64 = base64.b64encode(PUBLISHER_LOGO_SVG.encode()).decode()
    return f"data:image/svg+xml;base64,{logo_b64}"

def create_publisher_branding_html(text="Enhanced Edition", size="normal"):
    """Create HTML for publisher branding with logo"""
    logo_uri = get_publisher_logo_data_uri()
    logo_class = "publisher-logo" if size == "normal" else "publisher-logo-small"
    
    return f'''
    <div class="publisher-edition">
        <img src="{logo_uri}" alt="Publisher" class="{logo_class}"/>
        <span>{text}</span>
    </div>
    '''

def get_logo_css_variable():
    """Get CSS variable definition for the logo"""
    logo_uri = get_publisher_logo_data_uri()
    return f"--publisher-logo-url: url('{logo_uri}');"