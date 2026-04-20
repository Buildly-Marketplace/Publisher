"""
Avatar and annotation styling for Publisher
Handles Annotator avatar integration and retro-futuristic annotation boxes
"""
import base64
from pathlib import Path
from io import BytesIO

def create_annotator_avatar_data_uri(image_path=None):
    """
    Create a data URI for Annotator avatar. 
    If no image provided, uses a default retro avatar placeholder.
    """
    if image_path and Path(image_path).exists():
        # Read the actual image file
        with open(image_path, 'rb') as img_file:
            img_data = img_file.read()
            img_b64 = base64.b64encode(img_data).decode()
            # Determine format from file extension
            ext = Path(image_path).suffix.lower()
            if ext in ['.png']:
                mime_type = 'image/png'
            elif ext in ['.jpg', '.jpeg']:
                mime_type = 'image/jpeg'
            elif ext in ['.gif']:
                mime_type = 'image/gif'
            else:
                mime_type = 'image/png'
            return f"data:{mime_type};base64,{img_b64}"
    else:
        # Fallback: Create a simple SVG avatar placeholder
        svg_avatar = """
        <svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <pattern id="dots" patternUnits="userSpaceOnUse" width="4" height="4">
                    <circle cx="2" cy="2" r="1" fill="#333"/>
                </pattern>
            </defs>
            <circle cx="32" cy="32" r="30" fill="url(#dots)" stroke="#000" stroke-width="2"/>
            <circle cx="24" cy="26" r="3" fill="#000"/>
            <circle cx="40" cy="26" r="3" fill="#000"/>
            <path d="M20 44 Q32 52 44 44" stroke="#000" stroke-width="2" fill="none"/>
        </svg>
        """.strip()
        svg_b64 = base64.b64encode(svg_avatar.encode()).decode()
        return f"data:image/svg+xml;base64,{svg_b64}"

def get_retro_futuristic_css():
    """
    Generate CSS for retro-futuristic annotation boxes with Annotator avatar
    """
    annotator_avatar_uri = create_annotator_avatar_data_uri()
    
    css = f"""
    /* Publisher Retro-Futuristic Annotation Styles */
    body {{ 
        font-family: 'Georgia', serif; 
        line-height: 1.8; 
        margin: 2em; 
        background: linear-gradient(45deg, #f8f8f8 25%, transparent 25%), 
                   linear-gradient(-45deg, #f8f8f8 25%, transparent 25%), 
                   linear-gradient(45deg, transparent 75%, #f8f8f8 75%), 
                   linear-gradient(-45deg, transparent 75%, #f8f8f8 75%);
        background-size: 20px 20px;
        background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
    }}

    h1, h2 {{ 
        font-family: 'Courier New', monospace; 
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #2a4d3a;
        border-bottom: 3px solid #2a4d3a;
        padding-bottom: 0.5em;
    }}

    .story-text {{
        background: #fff;
        padding: 1.5em;
        margin: 1em 0;
        border: 2px solid #333;
        border-radius: 5px;
        box-shadow: 4px 4px 0px #ccc;
    }}

    .publisher-annotation {{
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%);
        border: 3px solid #00ff41;
        border-radius: 12px;
        margin: 2em 0;
        padding: 0;
        position: relative;
        box-shadow: 
            0 0 20px rgba(0, 255, 65, 0.3),
            inset 0 0 20px rgba(0, 255, 65, 0.1),
            4px 4px 15px rgba(0, 0, 0, 0.5);
        color: #00ff41;
        font-family: 'Courier New', monospace;
        overflow: hidden;
    }}

    .publisher-annotation::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #00ff41, #ff4100, #4100ff, #00ff41);
        animation: scan 3s linear infinite;
    }}

    @keyframes scan {{
        0% {{ transform: translateX(-100%); }}
        100% {{ transform: translateX(100%); }}
    }}

    .annotation-header {{
        background: linear-gradient(90deg, #00ff41, #00cc33);
        color: #000;
        padding: 0.8em 1em;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        display: flex;
        align-items: center;
        border-bottom: 2px solid #00ff41;
    }}

    .annotator-avatar {{
        width: 48px;
        height: 48px;
        background-image: url('{annotator_avatar_uri}');
        background-size: cover;
        background-position: center;
        border-radius: 50%;
        border: 3px solid #00ff41;
        margin-right: 1em;
        filter: contrast(1.2) brightness(0.9);
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.5);
    }}

    .annotation-title {{
        flex: 1;
        font-size: 0.9em;
    }}

    .annotation-content {{
        padding: 1.5em;
        line-height: 1.6;
        background: rgba(0, 0, 0, 0.8);
    }}

    .annotation-content ul {{
        list-style: none;
        padding: 0;
        margin: 0;
    }}

    .annotation-content li {{
        margin: 1em 0;
        padding-left: 1.5em;
        position: relative;
    }}

    .annotation-content li::before {{
        content: '→';
        position: absolute;
        left: 0;
        color: #00ff41;
        font-weight: bold;
        font-size: 1.2em;
    }}

    .annotation-content strong {{
        color: #ff4100;
        text-shadow: 0 0 5px rgba(255, 65, 0, 0.5);
    }}

    /* Different note types get different accents */
    .science-note {{ border-left: 4px solid #00ccff; }}
    .context-note {{ border-left: 4px solid #ffcc00; }}
    .futurist-note {{ border-left: 4px solid #ff4100; }}
    .humanist-note {{ border-left: 4px solid #cc00ff; }}

    /* Retro terminal effect */
    .publisher-annotation {{
        text-shadow: 0 0 5px currentColor;
    }}

    /* Subtle animation for the whole annotation */
    .publisher-annotation {{
        animation: subtle-glow 4s ease-in-out infinite alternate;
    }}

    @keyframes subtle-glow {{
        from {{ box-shadow: 0 0 20px rgba(0, 255, 65, 0.3), inset 0 0 20px rgba(0, 255, 65, 0.1), 4px 4px 15px rgba(0, 0, 0, 0.5); }}
        to {{ box-shadow: 0 0 30px rgba(0, 255, 65, 0.4), inset 0 0 25px rgba(0, 255, 65, 0.15), 6px 6px 20px rgba(0, 0, 0, 0.6); }}
    }}
    """
    
    return css

def format_annotation_html(annotation_text, section_number):
    """
    Convert annotation text to HTML with Annotator avatar and retro styling
    """
    # Parse the annotation text to identify note types
    lines = annotation_text.strip().split('\n')
    formatted_notes = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('•') or line.startswith('-'):
            # Remove bullet and process
            content = line[1:].strip()
            
            # Determine note type and add appropriate styling
            note_class = ""
            if "Science Note" in content:
                note_class = "science-note"
            elif "Context Note" in content:
                note_class = "context-note"
            elif "Futurist Note" in content:
                note_class = "futurist-note"
            elif "Humanist Note" in content:
                note_class = "humanist-note"
            
            formatted_notes.append(f'<li class="{note_class}">{content}</li>')
        elif line:
            # Handle non-bullet lines
            formatted_notes.append(f'<li>{line}</li>')
    
    annotation_html = f"""
    <div class="publisher-annotation">
        <div class="annotation-header">
            <div class="annotator-avatar"></div>
            <div class="annotation-title">
                Publisher Commentary • Section {section_number + 1}
            </div>
        </div>
        <div class="annotation-content">
            <ul>
                {''.join(formatted_notes)}
            </ul>
        </div>
    </div>
    """
    
    return annotation_html