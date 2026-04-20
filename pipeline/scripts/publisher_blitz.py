"""
Publisher Blitz-Inspired CSS Framework
Generate Blitz-compatible CSS for robust EPUB styling
"""

def get_publisher_blitz_css():
    """
    Generate Blitz-inspired CSS that works across all EPUB reading systems
    Following Blitz principles: inherit, build don't override, don't fight readers, have fun
    """
    return """/*
 * Publisher - EPUB CSS Framework
 * Inspired by Blitz eBook Framework principles
 * 
 * The 4 Principles:
 * 1. Embrace inheritance and cascade
 * 2. Build and refine, don't style and undo
 * 3. Don't fight, skirt around reading systems
 * 4. Have fun with steampunk aesthetics!
 */

/* RESET & FOUNDATION */
/* Based on Blitz reset principles but with steampunk theme */

/* Ensure compatibility across reading systems */
html {
    /* Don't override user font settings */
    font-size: inherit;
    line-height: inherit;
}

body {
    /* Use reader's default fonts as base */
    font-family: inherit;
    font-size: inherit;
    line-height: inherit;
    color: inherit;
    background: inherit;
    /* Ensure proper margins */
    margin: 1rem;
    padding: 0;
}

/* HTML5 block elements for older readers */
article, aside, details, figcaption, figure, footer, header, 
main, nav, section, summary {
    display: block;
}

/* TYPOGRAPHY FOUNDATION */
/* Let reading systems handle base typography */
h1, h2, h3, h4, h5, h6 {
    /* Use relative units for scalability */
    margin: 1.5em 0 0.5em 0;
    font-weight: bold;
    line-height: 1.2;
    page-break-after: avoid;
    break-after: avoid;
}

p {
    margin: 0 0 1em 0;
    text-indent: 0;
    orphans: 2;
    widows: 2;
}

/* CHAPTER TITLES */
.chapter-title {
    text-align: center;
    font-size: 2.5em;
    font-weight: bold;
    margin: 2em 0;
    /* Use currentColor to respect reading modes */
    color: currentColor;
    /* Subtle enhancement that won't break in night mode */
    opacity: 0.9;
    page-break-before: always;
    break-before: page;
}

.section-title {
    font-size: 1.5em;
    margin: 2em 0 1em 0;
    color: currentColor;
    opacity: 0.8;
    page-break-after: avoid;
    break-after: avoid;
}

/* ANNOTATOR ANNOTATIONS - Blitz Compatible */
/* Designed to work in all reading modes */
.publisher-annotation {
    /* Use relative units and inheritance */
    margin: 1.5em 0;
    padding: 1em;
    /* Subtle border that works in light/dark modes */
    border-left: 4px solid currentColor;
    /* Background that respects reading modes */
    background-color: rgba(128, 128, 128, 0.1);
    opacity: 0.9;
    font-size: 0.9em;
    line-height: 1.4;
    page-break-inside: avoid;
    break-inside: avoid;
}

.annotation-header {
    font-weight: bold;
    margin-bottom: 0.5em;
    color: currentColor;
    display: block; /* Fallback for non-flex readers */
}

.annotation-content {
    color: currentColor;
    line-height: 1.5;
}

.annotator-avatar {
    /* Simple, scalable avatar that works everywhere */
    display: inline-block;
    width: 2em;
    height: 2em;
    margin-right: 0.5em;
    /* Use border instead of complex backgrounds */
    border: 2px solid currentColor;
    border-radius: 1em; /* Safe fallback to 50% */
    /* Simple text-based avatar */
    text-align: center;
    line-height: 1.8em;
    font-size: 0.8em;
    vertical-align: middle;
}

.annotator-avatar::before {
    content: "B";
    color: currentColor;
    font-weight: bold;
}

/* DIALOG FORMATTING */
.dialog {
    margin: 0.5em 0;
    text-indent: 1em;
}

.dialog-speaker {
    font-weight: bold;
    color: currentColor;
}

/* LISTS */
ul, ol {
    margin: 1em 0;
    padding-left: 2em;
}

li {
    margin: 0.5em 0;
}

/* IMAGES */
img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0 auto;
}

figure {
    margin: 1em 0;
    text-align: center;
}

figcaption {
    font-size: 0.9em;
    color: currentColor;
    opacity: 0.7;
    margin-top: 0.5em;
}

/* NULLRECORDS BRANDING */
.publisher-branding,
.publisher-edition {
    text-align: center;
    margin: 2em 0;
    font-size: 0.9em;
    color: currentColor;
    opacity: 0.8;
}

.publisher-logo,
.publisher-logo-small {
    max-width: 120px;
    height: auto;
    display: block;
    margin: 0 auto 1em auto;
}

.publisher-logo-small {
    max-width: 60px;
}

/* UTILITIES - Blitz Style */
.text-center { text-align: center; }
.text-left { text-align: left; }
.text-right { text-align: right; }

.font-small { font-size: 0.8em; }
.font-large { font-size: 1.2em; }

.margin-top { margin-top: 2em; }
.margin-bottom { margin-bottom: 2em; }

.no-indent { text-indent: 0; }

/* READING SYSTEM COMPATIBILITY */
/* Following Blitz's approach to RS-specific fixes */

/* Kindle-specific improvements */
@media amzn-kf8 {
    .publisher-annotation {
        /* Kindle needs simpler styling */
        border: 1px solid;
        background: none;
        margin: 1em 0;
        padding: 0.5em;
    }
    
    .annotator-avatar::before {
        content: "[B]";
        font-size: 0.8em;
    }
    
    .chapter-title {
        font-size: 2em; /* Smaller for Kindle */
    }
}

/* iBooks/Apple Books adjustments */
@media screen and (-webkit-min-device-pixel-ratio: 0) {
    .publisher-annotation {
        /* Enhanced styling for webkit-based readers */
        border-radius: 0.5em;
    }
}

/* Print styles */
@media print {
    .publisher-annotation {
        border: 2px solid #666;
        background: #f0f0f0;
    }
    
    .annotator-avatar {
        border: 1px solid #333;
        background: #f9f9f9;
    }
}

/* Accessibility - High contrast mode support */
@media (prefers-contrast: high) {
    .publisher-annotation {
        border-width: 3px;
        background: none;
    }
    
    .annotator-avatar {
        border-width: 3px;
    }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
    * {
        animation: none !important;
        transition: none !important;
    }
}

/* 
 * Progressive Enhancement Layer
 * Only applied if reading system supports it - Blitz approach
 */
@supports (display: flex) {
    .annotation-header {
        display: flex;
        align-items: center;
    }
    
    .publisher-edition {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5em;
    }
    
    .publisher-logo,
    .publisher-logo-small {
        display: inline-block;
        margin: 0;
    }
}

@supports (border-radius: 50%) {
    .annotator-avatar {
        border-radius: 50%;
    }
}

/* 
 * Steampunk Enhancement Layer 
 * Applied only for capable reading systems - respects reading modes
 */
@supports (background: linear-gradient(45deg, red, blue)) and (not (prefers-color-scheme: dark)) {
    /* Only apply in light mode to respect dark/night reading modes */
    .publisher-enhanced .chapter-title {
        background: linear-gradient(45deg, 
            rgba(184, 134, 11, 0.1), 
            rgba(205, 133, 63, 0.1));
        padding: 0.2em;
    }
}

@supports (box-shadow: 0 0 10px rgba(0,0,0,0.1)) and (not (prefers-color-scheme: dark)) {
    .publisher-enhanced .publisher-annotation {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
}

/* Ensure no layout breaks in any reading system */
* {
    box-sizing: border-box;
}

/* Prevent widows/orphans where supported */
p, li, dt, dd {
    orphans: 2;
    widows: 2;
}

/* Page break controls */
.page-break-before { page-break-before: always; break-before: page; }
.page-break-after { page-break-after: always; break-after: page; }
.no-page-break { page-break-inside: avoid; break-inside: avoid; }

/* Safe font fallbacks following Blitz principles */
.font-serif { font-family: serif; }
.font-sans { font-family: sans-serif; }
.font-mono { font-family: monospace; }

/*
 * End of Publisher Blitz Framework
 * Total approach: Inherit -> Reset -> Build -> Enhance
 */"""

def get_blitz_compatible_avatar_html(annotation_text, index=0):
    """
    Generate Blitz-compatible HTML for Annotator annotations
    No complex CSS dependencies, works across all readers
    """
    return f"""<div class="publisher-annotation">
    <div class="annotation-header">
        <span class="annotator-avatar"></span>
        <strong>Annotator's Commentary #{index + 1}</strong>
    </div>
    <div class="annotation-content">
        {annotation_text}
    </div>
</div>"""

def get_blitz_compatible_branding_html():
    """
    Generate simple, cross-platform branding HTML
    """
    return """<div class="publisher-edition">
    <strong>Publisher Edition</strong>
    <br>
    <em>Enhanced with AI Commentary</em>
</div>"""