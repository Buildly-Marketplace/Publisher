import os
import json
import base64
import requests
from pathlib import Path
from .config import OPENAI_API_KEY, OLLAMA_SERVERS
from .logo_utils import get_publisher_logo_data_uri, create_publisher_branding_html

def create_book_cover_prompt(title, author, summary=""):
    """
    Generate a book cover prompt for the retro-futuristic style
    """
    prompt = f"""
    Create a striking book cover for '{title}' by {author}, Forge Publisher edition.
    
    Style: Retro-futuristic, combining 1950s sci-fi aesthetics with modern design elements.
    Elements to include:
    - Bold, geometric typography for the title
    - Subtle halftone dot patterns and scan lines
    - Color palette: electric green, orange, and black
    - Art deco meets cyberpunk aesthetic
    - Clean, readable layout with vintage sci-fi feel
    - Small Forge Publisher logo/branding
    
    The cover should evoke classic science fiction book covers but with a contemporary twist.
    High contrast, professional book cover design, suitable for EPUB format.
    Size: 800x1200 portrait orientation.
    
    {f'Story context: {summary}' if summary else ''}
    """
    return prompt

def generate_book_cover_ollama(title, author, summary=""):
    """
    Generate book cover description using Ollama and create with DALL-E prompt
    """
    if not OLLAMA_SERVERS:
        return generate_book_cover_openai(title, author, summary)
    
    # Use Ollama to generate a detailed description
    analysis_prompt = f"""
    Analyze the story '{title}' by {author} and create a detailed visual description for a retro-futuristic book cover.
    
    Focus on:
    - Key visual elements from the story
    - Color scheme that matches Forge Publisher brand (electric green, orange, black)
    - Typography style (bold, geometric, sci-fi)
    - Composition and layout
    
    Provide a concise but vivid description for an AI image generator.
    """
    
    for server_url in OLLAMA_SERVERS:
        try:
            response = requests.post(
                f"{server_url}/api/generate",
                json={
                    "model": "llama3.2",  # or best available
                    "prompt": analysis_prompt,
                    "stream": False,
                    "options": {"temperature": 0.8, "num_predict": 200}
                },
                timeout=60
            )
            if response.status_code == 200:
                description = response.json()["response"].strip()
                # Combine with our styling requirements
                cover_prompt = f"""
                {description}
                
                Additional requirements:
                - Retro-futuristic book cover design
                - Bold title typography: '{title}'
                - Author name: 'by {author}'
                - 'Forge Publisher' branding
                - Electric green and orange accent colors
                - Professional book cover layout
                - 800x1200 portrait format
                """
                return cover_prompt
        except Exception as e:
            print(f"⚠️  Ollama server {server_url} failed: {e}")
            continue
    
    # Fallback to OpenAI if Ollama fails
    return generate_book_cover_openai(title, author, summary)

def generate_book_cover_openai(title, author, summary=""):
    """
    Generate book cover using OpenAI
    """
    return create_book_cover_prompt(title, author, summary)

def generate_cover_image(title, author, summary="", output_dir="images"):
    """
    Generate the actual book cover image
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print("🎨 Generating book cover...")
    
    # Get cover prompt (try Ollama first, fallback to direct prompt)
    try:
        cover_prompt = generate_book_cover_ollama(title, author, summary)
    except:
        cover_prompt = create_book_cover_prompt(title, author, summary)
    
    print(f"🖼️  Cover prompt: {cover_prompt[:100]}...")
    
    # For now, create a text-based cover since we can't use DALL-E without credits
    # You can replace this with actual DALL-E API call when ready
    cover_path = create_text_based_cover(title, author, output_dir)
    
    return cover_path

def create_text_based_cover(title, author, output_dir="images"):
    """
    Create a text-based cover design using HTML/CSS and save as image placeholder
    """
    # Get the Publisher logo for the cover
    logo_data_uri = get_publisher_logo_data_uri()
    
    cover_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                width: 600px;
                height: 800px;
                background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0a0a0a 100%);
                font-family: 'Arial', sans-serif;
                color: #00ff41;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                position: relative;
                overflow: hidden;
            }}
            
            .cover-bg {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: 
                    radial-gradient(circle at 20% 80%, #00ff41 0%, transparent 50%),
                    radial-gradient(circle at 80% 20%, #ff4100 0%, transparent 50%),
                    repeating-linear-gradient(
                        90deg,
                        transparent,
                        transparent 10px,
                        rgba(0, 255, 65, 0.1) 11px,
                        rgba(0, 255, 65, 0.1) 12px
                    );
                opacity: 0.3;
            }}
            
            .title {{
                font-size: 48px;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 4px;
                margin: 20px 0;
                text-shadow: 
                    0 0 10px #00ff41,
                    0 0 20px #00ff41,
                    0 0 30px #00ff41;
                z-index: 1;
                line-height: 1.1;
            }}
            
            .author {{
                font-size: 24px;
                color: #ff4100;
                margin: 20px 0;
                letter-spacing: 2px;
                text-shadow: 0 0 5px #ff4100;
                z-index: 1;
            }}
            
            .publisher {{
                position: absolute;
                bottom: 40px;
                font-size: 16px;
                color: #00ccff;
                letter-spacing: 3px;
                text-transform: uppercase;
                font-weight: bold;
            }}
            
            .decorative-border {{
                position: absolute;
                border: 3px solid #00ff41;
                width: calc(100% - 60px);
                height: calc(100% - 60px);
                top: 30px;
                left: 30px;
                box-shadow: 
                    inset 0 0 20px rgba(0, 255, 65, 0.3),
                    0 0 20px rgba(0, 255, 65, 0.3);
            }}
        </style>
    </head>
    <body>
        <div class="cover-bg"></div>
        <div class="decorative-border"></div>
        <div class="title">{title}</div>
        <div class="author">by {author}</div>
        <div class="publisher">
            <img src="{logo_data_uri}" alt="Publisher" style="height: 40px; margin-right: 10px; vertical-align: middle;"/>
            Forge Publisher
        </div>
    </body>
    </html>
    """
    
    # Save HTML cover
    cover_html_path = Path(output_dir) / "book_cover.html"
    with open(cover_html_path, 'w', encoding='utf-8') as f:
        f.write(cover_html)
    
    print(f"📚 Book cover HTML created: {cover_html_path}")
    print("💡 To convert to image, use a tool like wkhtmltopdf or browser screenshot")
    
    return str(cover_html_path)

# Paths
ANNOTATIONS_JSON = "annotations/the_star_notes.json"
IMAGES_DIR = "images"
NUM_IMAGES = 3  # Reduced for more focused illustrations

def generate_chapter_illustration_prompts(book_data, num_images=3):
    """
    Generate prompts for chapter illustrations based on book content
    """
    sections = book_data.get('sections', [])
    title = book_data.get('title', 'Unknown Title')
    
    prompts = []
    total_sections = len(sections)
    
    if total_sections == 0:
        return prompts
    
    # Select key sections for illustrations
    interval = max(1, total_sections // num_images)
    
    for i in range(0, total_sections, interval):
        if len(prompts) >= num_images:
            break
            
        section = sections[i]
        # Create more detailed prompt
        prompt = f"""
        Create a retro-futuristic illustration for a scene from '{title}'.
        
        Text excerpt: "{section[:300]}..."
        
        Style requirements:
        - Vintage sci-fi aesthetic with modern touches
        - Color palette: electric green, orange, deep blacks
        - Art style: Mix of 1950s sci-fi art and contemporary digital art
        - High contrast, dramatic lighting
        - Detailed but not cluttered
        - Suitable for book illustration
        
        The illustration should capture the mood and key visual elements of this scene
        while maintaining the Forge Publisher retro-futuristic brand aesthetic.
        """
        prompts.append(prompt)
    
    return prompts

if __name__ == "__main__":
    # This will be called from the main pipeline
    print("🎨 Image generation script ready")
    print("📖 Use generate_cover_image() and generate_chapter_illustration_prompts() functions")
