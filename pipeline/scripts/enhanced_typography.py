"""
Enhanced Typography and Styling System for Publisher
Handles retro-futuristic fonts, paragraph structure, and dialog formatting
"""
import re
from pathlib import Path

def get_enhanced_typography_css():
    """
    Generate comprehensive CSS with retro-futuristic typography and improved readability
    """
    css = """
    /* Publisher Enhanced Typography System */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;500;600&family=Space+Grotesk:wght@400;500;700&display=swap');
    
    :root {
        /* Enhanced Color Scheme - Steampunk meets Mid-Century Modern */
        --primary-bg: #0f0f0f;
        --secondary-bg: #1a1a1a;
        --tertiary-bg: #2a2a2a;
        
        /* Steampunk Color Palette */
        --brass-gold: #b8860b;
        --copper-orange: #cd853f;
        --bronze-brown: #8b4513;
        --steam-green: #228b22;
        --emerald-green: #50c878;
        --deep-red: #8b0000;
        --crimson-red: #dc143c;
        --steel-blue: #4682b4;
        --ivory-white: #f5f5dc;
        
        /* Mid-Century Modern Accents */
        --atomic-orange: #ff6b35;
        --mint-green: #40e0d0;
        --sunset-pink: #ff69b4;
        --space-blue: #191970;
        
        /* Text Colors */
        --text-primary: #f5f5dc;
        --text-secondary: #d3d3d3;
        --text-accent: --steam-green;
        
        /* Typography */
        --font-main: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        --font-retro: 'JetBrains Mono', 'Courier New', monospace;
        --font-display: 'Space Grotesk', serif;
        
        /* Enhanced Spacing System */
        --space-xs: 0.5rem;
        --space-sm: 1rem;
        --space-md: 1.5rem;
        --space-lg: 2rem;
        --space-xl: 3rem;
        --space-xxl: 4rem;
        
        /* Page Layout */
        --page-padding: var(--space-xl);
        --content-max-width: 50rem;
        --header-spacing: var(--space-xl);
    }

    body {
        font-family: var(--font-main);
        font-size: 17px;
        line-height: 1.8;
        margin: 0;
        padding: var(--page-padding);
        background: 
            radial-gradient(circle at 25% 75%, var(--bronze-brown) 0%, transparent 50%),
            radial-gradient(circle at 75% 25%, var(--steel-blue) 0%, transparent 50%),
            linear-gradient(135deg, var(--primary-bg) 0%, var(--secondary-bg) 50%, var(--primary-bg) 100%);
        background-attachment: fixed;
        color: var(--text-primary);
        max-width: var(--content-max-width);
        margin: 0 auto;
        min-height: 100vh;
        box-sizing: border-box;
    }

    /* Chapter and Section Headers - Fixed Alignment */
    .chapter-title {
        font-family: var(--font-display);
        font-size: 3rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 4px;
        color: var(--brass-gold);
        text-align: center;
        margin: var(--header-spacing) 0 var(--space-xl) 0;
        padding: var(--space-xl) var(--space-lg);
        border: 3px solid var(--brass-gold);
        border-radius: 15px;
        background: linear-gradient(135deg, 
            var(--primary-bg) 0%, 
            var(--secondary-bg) 30%, 
            var(--tertiary-bg) 70%, 
            var(--primary-bg) 100%);
        box-shadow: 
            0 0 30px rgba(184, 134, 11, 0.4),
            inset 0 0 20px rgba(184, 134, 11, 0.1),
            0 10px 40px rgba(0, 0, 0, 0.6);
        position: relative;
        overflow: hidden;
        /* Fix drop cap alignment */
        line-height: 1.2;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 120px;
    }

    .chapter-title .title-main {
        font-size: 1em;
        margin-bottom: var(--space-xs);
        /* Better letter spacing for "THE STAR" */
        word-spacing: 0.2em;
    }

    .chapter-title .title-subtitle {
        font-size: 0.35em;
        letter-spacing: 2px;
        opacity: 0.8;
        color: var(--copper-orange);
        font-weight: 500;
        margin-top: var(--space-xs);
    }

    .chapter-title::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, 
            transparent, 
            var(--brass-gold), 
            var(--copper-orange),
            var(--brass-gold), 
            transparent);
        animation: steampunk-scan 4s linear infinite;
    }

    .section-title {
        font-family: var(--font-display);
        font-size: 1.8rem;
        font-weight: 600;
        color: var(--copper-orange);
        margin: var(--space-xl) 0 var(--space-lg) 0;
        padding: var(--space-md) 0 var(--space-sm) 0;
        border-bottom: 3px solid var(--copper-orange);
        letter-spacing: 2px;
        text-transform: uppercase;
        position: relative;
    }

    .section-title::after {
        content: '';
        position: absolute;
        bottom: -3px;
        left: 0;
        width: 60px;
        height: 3px;
        background: linear-gradient(90deg, var(--brass-gold), var(--copper-orange));
        border-radius: 3px;
    }

    /* Main Story Text */
    .story-text {
        background: linear-gradient(135deg, #1a1a1a, #2a2a2a);
        border: 2px solid #333;
        border-radius: 8px;
        padding: var(--space-lg);
        margin: var(--space-md) 0;
        box-shadow: 
            0 4px 20px rgba(0, 0, 0, 0.3),
            inset 0 1px 3px rgba(255, 255, 255, 0.1);
        position: relative;
    }

    .story-text::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--accent-blue), transparent);
    }

    /* Paragraph Styling */
    .paragraph {
        margin: var(--space-md) 0;
        text-align: justify;
        text-justify: inter-word;
    }

    .paragraph:first-child {
        margin-top: 0;
    }

    .paragraph:last-child {
        margin-bottom: 0;
    }

    /* Drop Cap for First Paragraph */
    .paragraph.first-paragraph::first-letter {
        font-family: var(--font-display);
        font-size: 4rem;
        font-weight: 700;
        line-height: 1;
        float: left;
        margin: 0.1em 0.1em 0 0;
        color: var(--accent-green);
        text-shadow: 0 0 10px rgba(0, 255, 65, 0.5);
    }

    /* Dialog Styling */
    .dialog {
        font-style: italic;
        color: var(--accent-blue);
        position: relative;
        padding-left: var(--space-md);
        margin: var(--space-sm) 0;
    }

    .dialog::before {
        content: '"';
        position: absolute;
        left: 0;
        top: -0.1em;
        font-size: 1.5em;
        color: var(--accent-blue);
        font-weight: bold;
    }

    .dialog::after {
        content: '"';
        color: var(--accent-blue);
        font-weight: bold;
        margin-left: 0.1em;
    }

    /* Emphasis and Strong Text */
    em {
        color: var(--accent-yellow);
        font-style: italic;
        text-shadow: 0 0 3px rgba(255, 204, 0, 0.3);
    }

    strong {
        color: var(--accent-orange);
        font-weight: 600;
        text-shadow: 0 0 3px rgba(255, 65, 0, 0.3);
    }

    /* Annotator Avatar Annotation System (Steampunk Enhanced) */
    .publisher-annotation {
        background: linear-gradient(135deg, 
            var(--primary-bg) 0%, 
            var(--secondary-bg) 30%, 
            var(--bronze-brown) 50%, 
            var(--secondary-bg) 70%, 
            var(--primary-bg) 100%);
        border: 4px solid var(--brass-gold);
        border-radius: 20px;
        margin: var(--space-xl) 0;
        padding: 0;
        position: relative;
        box-shadow: 
            0 0 30px rgba(184, 134, 11, 0.5),
            inset 0 0 30px rgba(139, 69, 19, 0.2),
            0 12px 40px rgba(0, 0, 0, 0.7);
        color: var(--ivory-white);
        font-family: var(--font-retro);
        overflow: hidden;
        animation: steampunk-glow 8s ease-in-out infinite alternate;
        /* Ensure proper spacing from edges */
        margin-left: var(--space-sm);
        margin-right: var(--space-sm);
    }

    .publisher-annotation::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 6px;
        background: linear-gradient(90deg, 
            var(--brass-gold), 
            var(--copper-orange), 
            var(--deep-red), 
            var(--steel-blue), 
            var(--emerald-green),
            var(--brass-gold));
        background-size: 300% 100%;
        animation: steampunk-rainbow-scan 6s linear infinite;
    }

    .annotation-header {
        background: linear-gradient(135deg, 
            var(--brass-gold) 0%, 
            var(--copper-orange) 50%, 
            var(--bronze-brown) 100%);
        color: var(--primary-bg);
        padding: var(--space-md) var(--space-lg);
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1.8px;
        display: flex;
        align-items: center;
        border-bottom: 3px solid var(--brass-gold);
        font-size: 0.95rem;
        position: relative;
    }

    .annotation-header::after {
        content: '';
        position: absolute;
        bottom: -3px;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--deep-red), transparent);
        animation: steampunk-underline 3s ease-in-out infinite alternate;
    }

    .annotator-avatar {
        width: 64px;
        height: 64px;
        background-image: var(--annotator-avatar-url);
        background-size: cover;
        background-position: center;
        border-radius: 50%;
        border: 5px solid var(--primary-bg);
        margin-right: var(--space-md);
        filter: contrast(1.4) brightness(0.9) sepia(0.3);
        box-shadow: 
            0 0 20px rgba(184, 134, 11, 0.7),
            inset 0 0 15px rgba(0, 0, 0, 0.4),
            0 0 5px var(--brass-gold);
        position: relative;
    }

    .annotator-avatar::before {
        content: '';
        position: absolute;
        top: -5px;
        left: -5px;
        right: -5px;
        bottom: -5px;
        border: 2px solid var(--copper-orange);
        border-radius: 50%;
        opacity: 0.6;
        animation: steampunk-rotate 10s linear infinite;
    }

    .annotation-title {
        flex: 1;
        font-size: 1rem;
        line-height: 1.4;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.7);
    }

    .annotation-content {
        padding: var(--space-lg);
        line-height: 1.7;
        background: linear-gradient(135deg, 
            rgba(0, 0, 0, 0.8) 0%, 
            rgba(139, 69, 19, 0.1) 50%, 
            rgba(0, 0, 0, 0.8) 100%);
        font-size: 1rem;
        border-radius: 0 0 16px 16px;
    }

    .annotation-content ul {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .annotation-content li {
        margin: var(--space-md) 0;
        padding-left: var(--space-lg);
        position: relative;
        border-left: 3px solid transparent;
        padding-bottom: var(--space-sm);
    }

    .annotation-content li::before {
        content: '▶';
        position: absolute;
        left: 0;
        top: 0.1em;
        color: var(--accent-green);
        font-weight: bold;
        font-size: 1.1em;
        animation: blink 2s ease-in-out infinite alternate;
    }

    /* Note Type Styling */
    .science-note { 
        border-left-color: var(--accent-blue) !important; 
    }
    .science-note strong { 
        color: var(--accent-blue); 
    }

    .context-note { 
        border-left-color: var(--accent-yellow) !important; 
    }
    .context-note strong { 
        color: var(--accent-yellow); 
    }

    .futurist-note { 
        border-left-color: var(--accent-orange) !important; 
    }
    .futurist-note strong { 
        color: var(--accent-orange); 
    }

    .humanist-note { 
        border-left-color: var(--accent-purple) !important; 
    }
    .humanist-note strong { 
        color: var(--accent-purple); 
    }

    /* Publisher Branding */
    .publisher-branding {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: var(--space-lg) 0;
        font-family: var(--font-retro);
        color: var(--copper-orange);
        font-size: 1.1rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    .publisher-logo {
        width: 120px;
        height: auto;
        margin-right: var(--space-md);
        filter: brightness(1.1) contrast(1.2);
        animation: steampunk-pulse 4s ease-in-out infinite alternate;
    }

    .publisher-logo-small {
        width: 60px;
        height: auto;
        margin-right: var(--space-sm);
        filter: brightness(1.1) contrast(1.2);
        vertical-align: middle;
    }

    .publisher-edition {
        text-align: center;
        margin: var(--space-xl) 0;
        font-family: var(--font-retro);
        color: var(--brass-gold);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: var(--space-sm);
    }

    /* Animations */
    @keyframes scan {
        0% { left: -100%; }
        100% { left: 100%; }
    }

    @keyframes rainbow-scan {
        0% { background-position: 0% 50%; }
        100% { background-position: 200% 50%; }
    }

    @keyframes subtle-glow {
        from { 
            box-shadow: 0 0 25px rgba(0, 255, 65, 0.4), inset 0 0 25px rgba(0, 255, 65, 0.1), 0 8px 30px rgba(0, 0, 0, 0.6); 
        }
        to { 
            box-shadow: 0 0 35px rgba(0, 255, 65, 0.5), inset 0 0 30px rgba(0, 255, 65, 0.15), 0 10px 40px rgba(0, 0, 0, 0.7); 
        }
    }

    @keyframes blink {
        from { opacity: 1; }
        to { opacity: 0.6; }
    }

    /* Steampunk-specific animations */
    @keyframes steampunk-glow {
        0% { 
            box-shadow: 
                0 0 30px rgba(184, 134, 11, 0.5),
                inset 0 0 30px rgba(139, 69, 19, 0.2),
                0 12px 40px rgba(0, 0, 0, 0.7);
        }
        50% { 
            box-shadow: 
                0 0 45px rgba(184, 134, 11, 0.8),
                inset 0 0 35px rgba(198, 99, 0, 0.3),
                0 12px 40px rgba(0, 0, 0, 0.7);
        }
        100% { 
            box-shadow: 
                0 0 35px rgba(139, 69, 19, 0.6),
                inset 0 0 25px rgba(184, 134, 11, 0.2),
                0 12px 40px rgba(0, 0, 0, 0.7);
        }
    }

    @keyframes steampunk-rainbow-scan {
        0% { background-position: -300% 0; }
        100% { background-position: 300% 0; }
    }

    @keyframes steampunk-underline {
        0% { opacity: 0.3; transform: scaleX(0.8); }
        100% { opacity: 0.8; transform: scaleX(1.2); }
    }

    @keyframes steampunk-rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    @keyframes steampunk-scan {
        0% { 
            background-position: -200% 50%; 
            opacity: 0.3; 
        }
        50% { 
            background-position: 0% 50%; 
            opacity: 0.8; 
        }
        100% { 
            background-position: 200% 50%; 
            opacity: 0.4; 
        }
    }

    /* Responsive Design */
    @media (max-width: 768px) {
        body {
            padding: var(--space-md);
            font-size: 15px;
        }
        
        .chapter-title {
            font-size: 2rem;
            letter-spacing: 2px;
        }
        
        .annotator-avatar {
            width: 48px;
            height: 48px;
        }
    }
    """
    
    return css

def detect_dialog_and_format_text(text):
    """
    Enhanced text formatting that detects dialog, proper paragraphs, and exposition
    """
    # Split into paragraphs
    paragraphs = re.split(r'\n\s*\n', text.strip())
    formatted_paragraphs = []
    
    for i, para in enumerate(paragraphs):
        para = para.strip()
        if not para:
            continue
            
        # Clean up whitespace
        para = re.sub(r'\s+', ' ', para)
        
        # Detect if this is dialog (contains quotation marks)
        is_dialog = bool(re.search(r'["""].*["""]', para))
        
        # Format based on content type
        if is_dialog:
            # Extract and format dialog
            dialog_content = re.sub(r'^["""]|["""]$', '', para)
            formatted_para = f'<p class="paragraph dialog">{dialog_content}</p>'
        else:
            # Regular exposition paragraph
            css_classes = "paragraph"
            if i == 0:  # First paragraph gets drop cap
                css_classes += " first-paragraph"
            
            formatted_para = f'<p class="{css_classes}">{para}</p>'
        
        formatted_paragraphs.append(formatted_para)
    
    return '\n'.join(formatted_paragraphs)

def create_chapter_structure(sections, title="The Star", author="H.G. Wells"):
    """
    Create a properly structured chapter with enhanced typography
    """
    chapter_html = f"""
    <div class="chapter-title">
        {title}<br>
        <small style="font-size: 0.4em; letter-spacing: 1px; opacity: 0.8;">by {author}</small>
    </div>
    """
    
    for i, section in enumerate(sections):
        section_title = f'<h2 class="section-title">Section {i + 1}</h2>'
        formatted_text = detect_dialog_and_format_text(section)
        
        chapter_html += f"""
        {section_title}
        <div class="story-text">
            {formatted_text}
        </div>
        """
    
    return chapter_html