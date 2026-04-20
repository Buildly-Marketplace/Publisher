import os
import time
print(f"[DEBUG] build_epub.py loaded from: {os.path.abspath(__file__)} at {time.ctime(os.path.getmtime(__file__))}")

from ebooklib import epub
import json
import os
import datetime
from pathlib import Path
from scripts.avatar_styling import format_annotation_html, create_annotator_avatar_data_uri
from scripts.enhanced_typography import get_enhanced_typography_css, create_chapter_structure, detect_dialog_and_format_text
from scripts.generate_images import generate_cover_image
from scripts.logo_utils import create_publisher_branding_html, get_publisher_logo_data_uri
from scripts.publisher_blitz import get_publisher_blitz_css, get_blitz_compatible_avatar_html, get_blitz_compatible_branding_html
from scripts.enhanced_interactive import get_enhanced_interactive_css, get_interactive_annotator_html, get_interactive_javascript
from scripts.smart_placement import insert_annotator_icons_in_text, create_enhanced_section_content
from scripts.annotation_system import get_enhanced_interactive_css_with_cover
from scripts.cover_integration import get_cover_image_data_uri
from scripts.annotator_image_utils import get_annotator_image_data_uri
from scripts.cover_processor import process_cover_for_epub
from scripts.themes import get_theme, DEFAULT_THEME

def build_epub(book_title, author, annotated_json_path, output_path, book_data=None, cover_path=None, theme_slug=None):
    """Build enhanced EPUB with theming and proper typography"""
    theme = get_theme(theme_slug)
    annotator = theme["annotator"]
    edition_version = "1.0.3"
    build_timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Get annotator avatar image data URI
    print(f"🤖 Loading annotator avatar for theme '{theme['name']}'...")
    annotator_image_data_uri = get_annotator_image_data_uri()
    
    # Get cover image - prioritize provided cover_path, then fall back to defaults
    print("🎨 Loading cover image...")
    cover_image_path = None
    
    # Priority order for cover:
    # 1. Explicitly provided cover_path
    # 2. Book-specific cover in assets (e.g., assets/metamorphosis_cover.png)
    # 3. Default cover (assets/cover.jpg)
    if cover_path and os.path.exists(cover_path):
        cover_image_path = cover_path
        print(f"📚 Using provided cover: {cover_path}")
    else:
        # Try to find book-specific cover
        book_slug = Path(annotated_json_path).stem.replace('_notes_enhanced', '').replace('_notes', '')
        possible_covers = [
            f"images/{book_slug}_cover.png",
            f"images/{book_slug}_cover.jpg",
            f"assets/images/{book_slug}_cover.png",
            f"assets/images/{book_slug}_cover.jpg",
            f"assets/{book_slug}_cover.png",
            f"assets/{book_slug}_cover.jpg",
            f"assets/{book_slug}.png",
            f"assets/{book_slug}.jpg",
            "assets/cover.jpg",
            "assets/cover.png",
        ]
        for possible_cover in possible_covers:
            if os.path.exists(possible_cover):
                cover_image_path = possible_cover
                print(f"📚 Found cover: {possible_cover}")
                break
    
    # Process cover with publisher logo overlay
    cover_image_data_uri = None
    processed_cover_path = None
    
    if cover_image_path:
        # Process cover to add publisher logo
        output_dir = str(Path(output_path).parent)
        processed_cover_path = process_cover_for_epub(cover_image_path, output_dir)
        
        if processed_cover_path and os.path.exists(processed_cover_path):
            cover_image_data_uri = get_cover_image_data_uri(processed_cover_path)
            print(f"✅ Cover image loaded with logo from {processed_cover_path}")
        else:
            # Fall back to original cover
            cover_image_data_uri = get_cover_image_data_uri(cover_image_path)
            processed_cover_path = cover_image_path
            print(f"✅ Cover image loaded from {cover_image_path}")
    else:
        print(f"⚠️  No cover image found, generating fallback cover")
        # Generate fallback book cover
        generated_cover = generate_cover_image(book_title, author, output_dir="images")
        if generated_cover and os.path.exists(generated_cover):
            processed_cover_path = generated_cover
    
    # Check for enhanced annotations first
    # Handle both "the_star_notes.json" and "the_star_notes_enhanced.json" paths
    if annotated_json_path.endswith('_enhanced.json'):
        # Already the enhanced path
        enhanced_json_path = annotated_json_path
    else:
        # Generate the enhanced path
        enhanced_json_path = annotated_json_path.replace('.json', '_enhanced.json')
    
    if os.path.exists(enhanced_json_path):
        print("🔬 Using enhanced annotations with comprehensive analysis")
        with open(enhanced_json_path, 'r', encoding='utf-8') as f:
            enhanced_data = json.load(f)
        # Handle both dict and list formats for enhanced_data
        if isinstance(enhanced_data, dict):
            data = enhanced_data.get('sections', enhanced_data)
        elif isinstance(enhanced_data, list):
            data = enhanced_data
        else:
            raise ValueError("Enhanced annotation file must be a dict or list.")
    else:
        print("📄 Using standard annotations")
        with open(annotated_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

    def compose_section_annotations(section_data):
        """Flatten base annotations plus enhanced analysis into one formatted string."""
        base_annotations = (section_data.get('annotation') or '').strip()
        enhanced_annotations = section_data.get('enhanced_annotations') or []

        blocks = []

        if base_annotations:
            blocks.append(base_annotations)

        for enhanced in enhanced_annotations:
            note_text = (enhanced.get('note') or '').strip()
            analysis_text = (enhanced.get('analysis') or '').strip()
            annotator_followup = (enhanced.get('bob_comment') or enhanced.get('annotator_comment') or '').strip()
            accuracy_text = (enhanced.get('accuracy') or '').strip()
            type_text = (enhanced.get('type') or 'Enhanced Note').replace('_', ' ')

            # Skip boilerplate "Interesting point" stubs
            lowered_note = note_text.lower()
            if lowered_note.startswith('🤔 interesting point') or lowered_note.startswith('interesting point'):
                continue

            detail_parts = [part for part in [note_text or analysis_text, annotator_followup] if part]
            if accuracy_text:
                detail_parts.append(f"[accuracy: {accuracy_text}]")

            if detail_parts:
                detail = ' '.join(detail_parts)
                blocks.append(f"• **Enhanced Note ({type_text})**: {detail}")

        return '\n'.join(blocks)

    def normalize_annotator_comment(raw_comment: str) -> str:
        """Remove leading annotator name prefix so we can add our own label."""
        text = (raw_comment or '').strip()
        if not text:
            return ''
        lowered = text.lower()
        # Strip common prefixes including the current theme's annotator name
        prefixes = [
            f"{annotator['name'].lower()} says:",
            f"{annotator['name'].lower()} says",
            "bob the somewhat humanist says:",
            "bob says:",
            "bob says",
            "the annotator says:",
            "editor says:",
        ]
        for prefix in prefixes:
            if lowered.startswith(prefix):
                text = text[len(prefix):].lstrip()
                break
        return text

    book = epub.EpubBook()
    book.set_identifier("publisher001")
    book.set_title(f"{book_title} — Publisher's Edition {edition_version}")
    book.set_language('en')
    book.add_author(author)
    
    # Add cover image to EPUB if available
    # Use processed cover if available
    actual_cover_path = processed_cover_path if processed_cover_path and os.path.exists(processed_cover_path) else cover_image_path
    if actual_cover_path and os.path.exists(actual_cover_path):
        with open(actual_cover_path, 'rb') as cover_file:
            cover_img = cover_file.read()
        
        # Determine image format for proper extension
        cover_ext = Path(actual_cover_path).suffix.lower()
        if cover_ext in ['.png']:
            cover_filename = "images/cover.png"
        else:
            cover_filename = "images/cover.jpg"
        
        # Set cover image (this automatically adds it to the manifest)
        book.set_cover(cover_filename, cover_img)
        print(f"✅ Cover image added to EPUB: {actual_cover_path}")
    else:
        print("⚠️  No cover image available for EPUB")
    
    # Use Enhanced Interactive CSS framework with cover image
    interactive_css = get_enhanced_interactive_css_with_cover(annotator_image_data_uri, cover_image_data_uri, theme=theme)
    
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=interactive_css)
    book.add_item(nav_css)
    
    # Create enhanced chapter content
    chapters = []
    
    # Add title page with enhanced interactive branding and cover image
    cover_html = ""
    if cover_image_data_uri:
        cover_html = f'<div class="cover-page"><img src="images/cover.jpg" alt="Book Cover" class="cover-image-display"/></div>'
    
    title_page_content = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"/>
        <title>Title Page</title>
        <link href="style/nav.css" rel="stylesheet" type="text/css"/>
    </head>
    <body class="steampunk-enhanced">
        {cover_html}
        <div class="chapter-title">
            {book_title}<br>
            <small style="font-size: 0.4em; letter-spacing: 1px; opacity: 0.8;">by {author}</small>
        </div>
        <div class="publisher-edition">
            <strong>Publisher's Edition {edition_version}</strong><br>
            <em>Enhanced with Interactive AI Commentary</em><br>
            <small style="opacity:0.7;">Built on {build_timestamp}</small>
        </div>
        <div class="publisher-intro" style="margin: 2em 0; padding: 1.2em; border-left: 4px solid var(--theme-primary, #cd853f); background: rgba(205,133,63,0.08); border-radius: 0.5em; line-height: 1.7;">
            <h3 style="margin-top:0;">A Note from {annotator['name']}</h3>
            <p>Welcome to our iterative enhanced press editions. Each build refines typography, annotations, and interactive commentary. Use the annotator callouts to explore insights and reflections as you read.</p>
            <p>We present <em>{book_title}</em> by {author} in this Publisher's Edition {edition_version}. Future iterations will continue to sharpen readability, accessibility, and the balance between story and commentary.</p>
            <p style="margin-bottom:0;">Tip: Tap the annotator icons for inline insights, or skim the introductions at the start of each chapter to set the scene. Enjoy the journey.</p>
        </div>
        {get_interactive_javascript()}
    </body>
    </html>"""
    
    title_page = epub.EpubHtml(title="Title Page", file_name="title_page.xhtml", lang="en")
    title_page.content = title_page_content
    title_page.add_item(nav_css)
    book.add_item(title_page)
    chapters.append(title_page)
    
    # Process content sections with enhanced interactivity
    sections = data if isinstance(data, list) else data.get('paragraphs', [])
    
    for i, section_data in enumerate(sections):
        section_text = section_data.get('text', '')
        annotator_comment = section_data.get('Bob', section_data.get('bob_comment', section_data.get('annotator_comment', '')))
        annotations = compose_section_annotations(section_data)
        
        if section_text.strip():
            # Enhanced section processing with interactivity
            content_parts = []
            
            # Add section title for numbered sections
            if i > 0:  # Skip title for first section
                content_parts.append(f'<h2 class="section-title">Section {i + 1}</h2>')
            
            enhanced_content = insert_annotator_icons_in_text(section_text.strip(), annotations, i)
            content_parts.append(f'<div class="section-content steampunk-enhanced">{enhanced_content}</div>')

            # Add annotator postface after the section content (non-interactive icon)
            normalized_comment = normalize_annotator_comment(annotator_comment)
            if normalized_comment:
                postface_html = (
                    '<div class="annotator-postface">'
                    '<span class="annotator-icon-small static"></span>'
                    f'<div class="annotator-postface-text"><strong>{annotator["name"]} says:</strong> {normalized_comment}</div>'
                    '</div>'
                )
                content_parts.append(postface_html)
            
            content = '\n'.join(content_parts)
            
            # Create chapter with enhanced structure
            chapter_html = f"""<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8"/>
                <title>Chapter {i + 1}</title>
                <link href="style/nav.css" rel="stylesheet" type="text/css"/>
            </head>
            <body class="steampunk-enhanced">
                {content}
                {get_interactive_javascript()}
            </body>
            </html>"""
            
            chapter = epub.EpubHtml(title=f"Chapter {i + 1}", file_name=f"chap_{i+1:03d}.xhtml", lang="en")
            chapter.content = chapter_html
            chapter.add_item(nav_css)
            book.add_item(chapter)
            chapters.append(chapter)

    # Build proper TOC and spine
    book.toc = chapters
    nav = epub.EpubNav()
    book.add_item(nav)
    book.add_item(epub.EpubNcx())
    
    book.spine = ['nav'] + chapters

    epub.write_epub(output_path, book, {})
    print(f"✅ EPUB created: {output_path}")
