"""
Smart Annotator Icon Placement System
Strategically places interactive Annotator annotations throughout text
"""
import re
from .annotation_formatter import (
    format_annotation_with_emojis,
    separate_annotations_by_placement,
    parse_annotation_text
)

# Emoji mapping for note types
NOTE_TYPE_EMOJIS = {
    'science note': '🔬',
    'context note': '📚',
    'contextual note': '📚',
    'futurist note': '🚀',
    'humanist note': '👥',
    'literary note': '📖',
    'historical note': '🏛️',
    'technical note': '⚙️',
    'cultural note': '🎭',
    'philosophy note': '🤔',
    'commentary': '💭',
}


def get_note_emoji(note_type):
    """Get emoji for a note type"""
    note_type_lower = note_type.lower()
    return NOTE_TYPE_EMOJIS.get(note_type_lower, '💭')


def detect_dialog_and_format_text(text):
    """Simple dialog detection fallback"""
    return text


def create_inline_note_html(note, note_index):
    """
    Create HTML for an inline context note (appears as margin note or tooltip).
    These are shown beside the text they reference.
    """
    emoji = get_note_emoji(note.get('type', 'Context Note'))
    content = note.get('content', '')
    quote = note.get('quote', '')
    
    # Create a compact inline note
    return f'''<span class="inline-note-marker" data-note="{note_index}" title="{content[:100]}...">
        <span class="inline-note-icon">{emoji}</span>
        <span class="inline-note-popup">
            <strong>{note.get('type', 'Note')}:</strong> {content}
            {f'<blockquote>"{quote}"</blockquote>' if quote else ''}
        </span>
    </span>'''


def insert_annotator_icons_in_text(text, annotation, section_index=0):
    """
    Place Annotator annotations AFTER the section content (postface style).
    Annotator's commentary follows the text, never inline or before.
    Preserves paragraph structure and converts to HTML paragraphs.
    """
    # Parse annotations into categories
    separated = separate_annotations_by_placement(annotation) if annotation else {'inline': [], 'section': []}
    inline_notes = separated.get('inline', [])
    section_notes = separated.get('section', [])
    all_notes = section_notes + inline_notes  # Combine all notes for end placement
    
    # First, split text into paragraphs by double line breaks
    paragraphs = re.split(r'\n\n+', text.strip())
    
    # If we have only one large "paragraph", try to split by dialog patterns
    if len(paragraphs) == 1 and len(paragraphs[0]) > 500:
        single_text = paragraphs[0]
        split_patterns = [
            r'([.!?])\s+(")',
            r'(said\.|replied\.|asked\.)\s+([A-Z])',
        ]
        for pattern in split_patterns:
            single_text = re.sub(pattern, r'\1\n\n\2', single_text)
        paragraphs = re.split(r'\n\n+', single_text)
    
    if not paragraphs:
        return ""
    
    # Process each paragraph (just wrap in <p> tags, no inline icons)
    processed_paragraphs = []
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        processed_paragraphs.append(f"<p>{paragraph}</p>")
    
    # Add Annotator annotation icon at the END of all paragraphs (postface style)
    if all_notes:
        section_annotation = '\n'.join([
            f"• **{n.get('type', 'Note')}**: {n.get('content', '')}"
            for n in all_notes
        ])
        annotator_html = get_interactive_annotator_html(section_annotation, section_index, 'end')
        # Append Annotator after the last paragraph
        if processed_paragraphs:
            processed_paragraphs[-1] = processed_paragraphs[-1] + f" {annotator_html}"

    return '\n'.join(processed_paragraphs)

def get_interactive_annotator_html(annotation_text, index=0, placement="default"):
    """
    Generate interactive Annotator annotation with floating icon and popup
    Enhanced with placement-specific styling and emoji formatting
    """
    placement_class = f"annotator-placement-{placement}" if placement != "default" else ""
    
    # Format the annotation text with emojis
    formatted_annotation = format_annotation_with_emojis(annotation_text)
    
    return f"""<span class="annotator-container {placement_class}">
        <span class="annotator-icon" 
              onclick="toggleAnnotation({index})" 
              onkeydown="if(event.key==='Enter'||event.key===' ')toggleAnnotation({index})"
              tabindex="0"
              role="button"
              aria-label="Annotator's Commentary {index + 1}"
              data-annotation-id="{index}"
              title="Click for Annotator's insights"></span>
        <div class="annotator-popup" id="annotation-popup-{index}">
            <div class="annotator-popup-header">
                <div class="annotator-popup-title">
                    <span class="annotator-popup-avatar"></span>
                    Annotator's Commentary #{index + 1}
                </div>
                <button class="annotator-popup-close" onclick="closeAnnotation({index})" aria-label="Close">×</button>
            </div>
            <div class="annotator-popup-content">
                {formatted_annotation}
            </div>
        </div>
    </span>"""

def create_enhanced_section_content(text, annotation, section_index):
    """
    Create enhanced section with strategic Annotator placement and steampunk styling
    """
    # Process text for dialog and paragraph structure
    formatted_text = detect_dialog_and_format_text(text)
    
    # Insert interactive Annotator icons
    enhanced_text = insert_annotator_icons_in_text(formatted_text, annotation, section_index)
    
    return enhanced_text