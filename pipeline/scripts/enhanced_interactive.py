"""
Publisher Enhanced Interactive Framework
Blitz foundation + Tailwind utilities + Interactive Annotator annotations
"""
import base64
from pathlib import Path

def get_annotator_image_data_uri():
    """Convert annotator.png to data URI for CSS embedding"""
    annotator_path = Path(__file__).parent.parent / "assets" / "annotator.png"
    
    if annotator_path.exists():
        try:
            with open(annotator_path, "rb") as img_file:
                img_data = img_file.read()
                base64_data = base64.b64encode(img_data).decode('utf-8')
                return f"data:image/png;base64,{base64_data}"
        except Exception as e:
            print(f"Warning: Could not load annotator.png: {e}")
    
    return None

def get_enhanced_interactive_css():
    """
    Generate enhanced CSS with Tailwind-inspired utilities and interactive Annotator annotations
    """
    # Get annotator image as data URI
    annotator_data_uri = get_annotator_image_data_uri()
    
    # Generate the base CSS
    base_css = """/*
 * Publisher - Enhanced Interactive Framework
 * Blitz Foundation + Tailwind Utilities + Interactive Steampunk Aesthetics
 */

/* BLITZ FOUNDATION - Reliable base */
html {
    font-size: inherit;
    line-height: inherit;
}

body {
    font-family: inherit;
    font-size: inherit;
    line-height: inherit;
    color: inherit;
    background: inherit;
    margin: 1rem;
    padding: 0;
    position: relative;
}

/* HTML5 block elements for older readers */
article, aside, details, figcaption, figure, footer, header, 
main, nav, section, summary {
    display: block;
}

/* TAILWIND-INSPIRED UTILITIES */
/* Spacing */
.m-0 { margin: 0; }
.m-1 { margin: 0.25rem; }
.m-2 { margin: 0.5rem; }
.m-4 { margin: 1rem; }
.m-8 { margin: 2rem; }

.p-0 { padding: 0; }
.p-1 { padding: 0.25rem; }
.p-2 { padding: 0.5rem; }
.p-4 { padding: 1rem; }
.p-6 { padding: 1.5rem; }
.p-8 { padding: 2rem; }

/* Layout */
.relative { position: relative; }
.absolute { position: absolute; }
.fixed { position: fixed; }
.block { display: block; }
.inline-block { display: inline-block; }
.hidden { display: none; }

/* Flexbox */
.flex { display: flex; }
.flex-col { flex-direction: column; }
.items-center { align-items: center; }
.justify-center { justify-content: center; }
.justify-between { justify-content: space-between; }

/* Text */
.text-center { text-align: center; }
.text-left { text-align: left; }
.text-right { text-align: right; }
.font-bold { font-weight: bold; }
.italic { font-style: italic; }
.uppercase { text-transform: uppercase; }

/* Sizing */
.w-full { width: 100%; }
.h-full { height: 100%; }
.w-8 { width: 2rem; }
.h-8 { height: 2rem; }
.w-12 { width: 3rem; }
.h-12 { height: 3rem; }

/* STEAMPUNK DESIGN SYSTEM */
:root {
    /* Steampunk color palette - respects reading modes */
    --brass: color-mix(in srgb, currentColor 70%, #b8860b 30%);
    --copper: color-mix(in srgb, currentColor 70%, #cd853f 30%);
    --bronze: color-mix(in srgb, currentColor 70%, #8b4513 30%);
    --steam-blue: color-mix(in srgb, currentColor 80%, #4682b4 20%);
    --gear-gray: color-mix(in srgb, currentColor 85%, #696969 15%);
    
    /* Fallbacks for older readers */
    --brass-fallback: rgba(184, 134, 11, 0.3);
    --copper-fallback: rgba(205, 133, 63, 0.3);
    --bronze-fallback: rgba(139, 69, 19, 0.3);
}

/* CHAPTER STYLING */
.chapter-title {
    text-align: center;
    font-size: 2.5em;
    font-weight: bold;
    margin: 2em 0;
    color: currentColor;
    position: relative;
    page-break-before: always;
    break-before: page;
}

.section-title {
    font-size: 1.5em;
    margin: 2em 0 1em 0;
    color: currentColor;
    opacity: 0.9;
    position: relative;
    page-break-after: avoid;
    break-after: avoid;
}

/* INTERACTIVE ANNOTATOR SYSTEM */
.annotator-container {
    position: relative;
    display: inline-block;
}

/* Floating Annotator Icons */
.annotator-icon {{
    display: inline-block;
    width: 1.5em;
    height: 1.5em;
    border: 2px solid var(--brass, var(--brass-fallback));
    border-radius: 50%;
    {annotator_bg}
    background-size: cover;
    background-position: center;
    cursor: pointer;
    position: relative;
    margin: 0 0.25em;
    vertical-align: super;
    transition: all 0.3s ease;
}}

.annotator-icon::before {
    content: "";
}

/* Annotator Icon States */
.annotator-icon:hover,
.annotator-icon:focus {
    transform: scale(1.2);
    filter: brightness(1.2);
}

.annotator-icon.active {
    background: var(--brass, var(--brass-fallback));
    box-shadow: 0 0 10px var(--brass, var(--brass-fallback));
}

/* Annotator Introduction Section - Section-level annotator commentary */
.annotator-introduction {
    display: flex;
    align-items: flex-start;
    margin: 1.5em 0 2em 0;
    padding: 1.2em;
    border-left: 4px solid var(--copper, #cd853f);
    border-radius: 0.5em;
    background: linear-gradient(135deg, rgba(205, 133, 63, 0.08), rgba(184, 134, 11, 0.05));
    page-break-inside: avoid;
    break-inside: avoid;
    font-style: italic;
    color: #2c1810;
    line-height: 1.7;
}

.annotator-introduction p {
    margin: 0;
    padding: 0;
    flex: 1;
}

/* Small Annotator Icon - For section introductions */
.annotator-icon-small {{
    display: inline-block;
    width: 2.5em;
    height: 2.5em;
    min-width: 2.5em;
    min-height: 2.5em;
    margin-right: 1em;
    border: 2px solid var(--brass, #b8860b);
    border-radius: 50%;
    {annotator_bg}
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
    background-color: var(--copper-fallback, rgba(205, 133, 63, 0.2));
    flex-shrink: 0;
    position: relative;
    font-weight: bold;
    font-size: 1.8em;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--brass, #b8860b);
    text-shadow: 0 0 2px rgba(255, 255, 255, 0.8);
}}

.annotator-icon-small::before {{
    content: "B";
    z-index: 1;
}}

/* Animation for small annotator icon */
@supports (animation: annotator-appear 0.5s ease-out) {
    .annotator-introduction {
        animation: annotator-appear 0.5s ease-out;
    }
    
    @keyframes annotator-appear {
        0% {
            opacity: 0;
            transform: translateY(10px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }
}

/* Popup Annotation */
.annotator-popup {
    position: fixed;
    top: 10vh;
    left: 5vw;
    right: 5vw;
    width: 90vw;
    transform: none;
    background: linear-gradient(135deg, #f4f1e8 0%, #f9f6f0 50%, #f2efdf 100%);
    border: 3px solid var(--brass, #b8860b);
    border-radius: 1em;
    padding: 2em;
    z-index: 1000;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
    font-size: 1em;
    line-height: 1.6;
    color: #2c1810;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    max-height: 80vh;
    overflow-y: auto;
}

.annotator-popup.show {
    opacity: 1;
    visibility: visible;
}

.annotator-popup::after {
    display: none;
}

.annotator-popup-header {
    font-weight: bold;
    margin-bottom: 1.5em;
    color: var(--brass, #b8860b);
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 1.2em;
    border-bottom: 2px solid var(--copper, #cd853f);
    padding-bottom: 0.5em;
}

.annotator-popup-title {
    display: flex;
    align-items: center;
    flex: 1;
}

.annotator-popup-close {
    background: none;
    border: 2px solid var(--brass, #b8860b);
    color: var(--brass, #b8860b);
    border-radius: 50%;
    width: 2em;
    height: 2em;
    cursor: pointer;
    font-size: 1em;
    font-weight: bold;
    transition: all 0.2s ease;
}

.annotator-popup-close:hover {
    background: var(--brass, #b8860b);
    color: #f4f1e8;
}

.annotator-popup-avatar {{
    width: 3em;
    height: 3em;
    border-radius: 50%;
    border: 2px solid var(--brass, #b8860b);
    margin-right: 1em;
    {annotator_bg}
    background-size: cover;
    background-position: center;
    flex-shrink: 0;
}}

.annotator-popup-avatar::before {
    content: "";
}

/* Annotation Styling */
.annotation-point {
    margin-bottom: 1.2em;
    padding: 0.8em;
    border-left: 3px solid var(--copper, #cd853f);
    background: rgba(244, 241, 232, 0.5);
    border-radius: 0.5em;
}

.annotation-type {
    display: flex;
    align-items: center;
    margin-bottom: 0.5em;
    font-weight: bold;
    color: var(--brass, #b8860b);
}

.annotation-emoji {
    font-size: 1.2em;
    margin-right: 0.5em;
}

.annotation-content {
    color: #2c1810;
    line-height: 1.5;
}

/* STEAMPUNK ENHANCEMENTS */
@supports (background: linear-gradient(45deg, red, blue)) {
    .steampunk-enhanced .chapter-title {
        background: linear-gradient(45deg, 
            var(--brass, var(--brass-fallback)), 
            var(--copper, var(--copper-fallback)));
        background-clip: text;
        -webkit-background-clip: text;
        color: transparent;
        background-size: 200% 200%;
        animation: steampunk-shimmer 4s ease-in-out infinite;
    }
    
    .steampunk-enhanced .section-title::before {
        content: '⚙ ';
        color: var(--brass, var(--brass-fallback));
    }
    
    .steampunk-enhanced .section-title::after {
        content: ' ⚙';
        color: var(--copper, var(--copper-fallback));
    }
}

/* GLOW ANIMATIONS */
@supports (animation: glow 2s ease-in-out infinite) {
    .annotator-icon {
        animation: annotator-glow 3s ease-in-out infinite alternate;
    }
    
    @keyframes annotator-glow {
        0% { 
            box-shadow: 0 0 5px var(--brass, var(--brass-fallback));
            filter: brightness(1);
        }
        100% { 
            box-shadow: 0 0 15px var(--copper, var(--copper-fallback));
            filter: brightness(1.3);
        }
    }
    
    @keyframes steampunk-shimmer {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
}

/* TRADITIONAL ANNOTATIONS - Fallback */
.publisher-annotation {
    margin: 1.5em 0;
    padding: 1em;
    border-left: 4px solid var(--brass, var(--brass-fallback));
    background: var(--gear-gray, rgba(128, 128, 128, 0.1));
    border-radius: 0.5em;
    page-break-inside: avoid;
    break-inside: avoid;
    position: relative;
}

.annotation-header {
    font-weight: bold;
    margin-bottom: 0.5em;
    color: currentColor;
    display: flex;
    align-items: center;
}

.annotator-avatar {
    display: inline-block;
    width: 2em;
    height: 2em;
    margin-right: 0.5em;
    border: 2px solid var(--brass, var(--brass-fallback));
    border-radius: 50%;
    text-align: center;
    line-height: 1.8em;
    font-size: 0.8em;
    vertical-align: middle;
    background: var(--copper, var(--copper-fallback));
}

.annotator-avatar::before {
    content: "B";
    color: currentColor;
    font-weight: bold;
}

/* BRANDING */
.publisher-edition {
    text-align: center;
    margin: 2em 0;
    font-size: 0.9em;
    color: var(--brass, var(--brass-fallback));
    position: relative;
}

/* RESPONSIVE & ACCESSIBILITY */
@media (max-width: 768px) {
    .annotator-popup {
        max-width: 90vw;
        font-size: 0.8em;
    }
}

@media (prefers-reduced-motion: reduce) {
    .annotator-icon,
    .chapter-title {
        animation: none !important;
        transition: none !important;
    }
}

@media (prefers-contrast: high) {
    .annotator-icon {
        border-width: 3px;
        background: currentColor;
    }
    
    .annotator-popup {
        border-width: 3px;
        background: Canvas;
        color: CanvasText;
    }
}

/* KINDLE COMPATIBILITY */
@media amzn-kf8 {
    .annotator-icon {
        position: static;
        transform: none;
        animation: none;
    }
    
    .annotator-popup {
        position: relative;
        transform: none;
        opacity: 1;
        visibility: visible;
        margin-top: 0.5em;
        margin-bottom: 1em;
    }
    
    .steampunk-enhanced .chapter-title {
        background: none;
        color: currentColor;
    }
}

/* PRINT STYLES */
@media print {
    .annotator-popup {
        position: relative;
        opacity: 1;
        visibility: visible;
        transform: none;
        margin: 1em 0;
        background: #f0f0f0;
        border: 1px solid #333;
    }
    
    .annotator-icon {
        animation: none;
        background: #ddd;
        border: 1px solid #333;
    }
}

/*
 * END ENHANCED FRAMEWORK
 */"""
    
    # Replace annotator image placeholders with actual data URI or fallback
    if annotator_data_uri:
        annotator_bg = f"background-image: url('{annotator_data_uri}');"
    else:
        annotator_bg = "background: var(--copper, #cd853f);"
    
    # Inject annotator image into the CSS
    final_css = base_css.replace('{annotator_bg}', annotator_bg)
    
    return final_css

def get_interactive_annotator_html(annotation_text, index=0, position="after"):
    """
    Generate interactive annotator annotation with floating icon and popup
    """
    return f"""
    <span class="annotation-popup-container">
        <span class="annotator-icon" 
              onclick="toggleAnnotation({index})" 
              onkeydown="if(event.key==='Enter'||event.key===' ')toggleAnnotation({index})"
              tabindex="0"
              role="button"
              aria-label="Annotator's Commentary {index + 1}"
              data-annotation-id="{index}"></span>
        <div class="annotator-popup" id="annotation-popup-{index}">
            <div class="annotator-popup-header">
                <span class="annotator-popup-avatar"></span>
                Annotator's Commentary #{index + 1}
            </div>
            <div class="annotator-popup-content">
                {annotation_text}
            </div>
        </div>
    </span>"""

def get_interactive_javascript():
    """
    Generate JavaScript for interactive Annotator annotations
    """
    return """
    <script>
    // Annotator Interaction System
    function toggleAnnotation(id) {
        const popup = document.getElementById('annotation-popup-' + id);
        const icon = document.querySelector('[data-annotation-id="' + id + '"]');
        
        if (!popup || !icon) return;
        
        // Close all other popups first
        closeAllAnnotations();
        
        // Toggle current popup
        if (!popup.classList.contains('show')) {
            popup.classList.add('show');
            icon.classList.add('active');
            
            // Auto-close after 15 seconds
            setTimeout(() => {
                if (popup.classList.contains('show')) {
                    popup.classList.remove('show');
                    icon.classList.remove('active');
                }
            }, 15000);
        }
    }
    
    function closeAnnotation(id) {
        const popup = document.getElementById('annotation-popup-' + id);
        const icon = document.querySelector('[data-annotation-id="' + id + '"]');
        
        if (popup && icon) {
            popup.classList.remove('show');
            icon.classList.remove('active');
        }
    }
    
    function closeAllAnnotations() {
        const popups = document.querySelectorAll('.annotator-popup');
        const icons = document.querySelectorAll('.annotator-icon');
        
        popups.forEach(popup => popup.classList.remove('show'));
        icons.forEach(icon => icon.classList.remove('active'));
    }
    
    // Close popup when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.annotator-container')) {
            closeAllAnnotations();
        }
    });
    
    // Keyboard accessibility
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closeAllAnnotations();
        }
    });
    
    // Touch support for mobile
    document.addEventListener('touchstart', function(event) {
        if (!event.target.closest('.annotator-container')) {
            closeAllAnnotations();
        }
    });
    </script>"""