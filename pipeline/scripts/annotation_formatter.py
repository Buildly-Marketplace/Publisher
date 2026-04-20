"""
Annotation Formatting - Convert annotations to styled format with emojis
"""
import re

# Note type categories
INLINE_NOTE_TYPES = {'context', 'contextual', 'historical', 'cultural', 'literary'}
SECTION_NOTE_TYPES = {'science', 'humanist', 'futurist', 'technical', 'philosophy', 'enhanced'}


def parse_annotation_text(annotation_text):
    """
    Parse annotation text into structured list of notes with types.
    
    Returns list of dicts: [{'type': 'Science Note', 'content': '...', 'quote': '...'}, ...]
    """
    if not annotation_text:
        return []
    
    # Clean up the annotation text
    cleaned_text = annotation_text.strip()
    
    # Split into individual points
    points = re.split(r'•\s*\*?\s*', cleaned_text)
    points = [point.strip() for point in points if point.strip()]
    
    parsed_notes = []
    current_note = None
    
    for point in points:
        point = point.strip()
        if not point:
            continue
        
        # Check if this is a note type header (e.g., "Science Note" or "**Science Note**:")
        type_match = re.match(r'\*?\*?([A-Za-z]+\s+Note)\*?\*?:?\s*$', point, re.IGNORECASE)
        if type_match:
            # Start a new note with this type
            if current_note and current_note.get('content'):
                parsed_notes.append(current_note)
            current_note = {'type': type_match.group(1).strip(), 'content': '', 'quote': None}
            continue
        
        # Check if this starts with a note type inline (e.g., "**Science Note**: Content here")
        inline_type_match = re.match(r'\*?\*?([A-Za-z]+\s+Note)\*?\*?:\s*(.+)', point, re.IGNORECASE)
        if inline_type_match:
            if current_note and current_note.get('content'):
                parsed_notes.append(current_note)
            current_note = {
                'type': inline_type_match.group(1).strip(),
                'content': inline_type_match.group(2).strip(),
                'quote': None
            }
            continue
        
        # Check if point ends with (Type Note) marker
        type_suffix_match = re.search(r'\(([A-Za-z]+\s+Note)\)\s*$', point, re.IGNORECASE)
        if type_suffix_match:
            note_type = type_suffix_match.group(1)
            content = point[:type_suffix_match.start()].strip()
            parsed_notes.append({
                'type': note_type,
                'content': content,
                'quote': None
            })
            current_note = None
            continue
        
        # Check if this is a quote line (starts with - " or just a long quote)
        quote_match = re.match(r'^[-–]\s*["\u201c](.+?)["\u201d]', point)
        if quote_match and current_note:
            current_note['quote'] = quote_match.group(1)
            # Check if there's content after the quote
            remaining = point[quote_match.end():].strip()
            if remaining:
                current_note['content'] = (current_note.get('content', '') + ' ' + remaining).strip()
            continue
        
        # Regular content - add to current note or create new one
        if current_note:
            current_note['content'] = (current_note.get('content', '') + ' ' + point).strip()
        else:
            # No current note type - infer from content
            inferred_type = infer_note_type(point)
            parsed_notes.append({
                'type': inferred_type,
                'content': point,
                'quote': None
            })
    
    # Don't forget the last note
    if current_note and current_note.get('content'):
        parsed_notes.append(current_note)
    
    return parsed_notes


def infer_note_type(content):
    """Infer note type from content keywords"""
    content_lower = content.lower()
    
    if any(word in content_lower for word in ['psychology', 'freud', 'emotion', 'feeling', 'alienation', 'identity', 'existential']):
        return 'Humanist Note'
    if any(word in content_lower for word in ['scientific', 'biology', 'physics', 'anatomy', 'medical', 'phenomenon', 'theory']):
        return 'Science Note'
    if any(word in content_lower for word in ['century', 'era', 'period', 'historical', 'society', 'culture']):
        return 'Context Note'
    if any(word in content_lower for word in ['metaphor', 'symbolism', 'theme', 'literary', 'narrative', 'kafka']):
        return 'Literary Note'
    
    return 'Commentary'


def get_note_category(note_type):
    """
    Determine if a note should be displayed inline or at section end.
    
    Returns: 'inline' or 'section'
    """
    note_type_lower = note_type.lower()
    
    for inline_type in INLINE_NOTE_TYPES:
        if inline_type in note_type_lower:
            return 'inline'
    
    return 'section'


def separate_annotations_by_placement(annotation_text):
    """
    Parse annotations and separate into inline vs section-end notes.
    
    Returns: {'inline': [...], 'section': [...]}
    """
    parsed = parse_annotation_text(annotation_text)
    
    result = {'inline': [], 'section': []}
    
    for note in parsed:
        category = get_note_category(note.get('type', 'Commentary'))
        result[category].append(note)
    
    return result


def convert_markdown_to_html(text):
    """
    Convert markdown formatting to HTML.
    Handles **bold**, *italic*, and `code` formatting.
    """
    if not text:
        return text
    
    # Convert **bold** to <strong>
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    
    # Convert *italic* to <em> (but not inside already-converted tags)
    text = re.sub(r'(?<![<>])\*([^*]+)\*(?![<>])', r'<em>\1</em>', text)
    
    # Convert `code` to <code>
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    return text


def format_annotation_with_emojis(annotation_text):
    """
    Format annotation text with stylized emojis based on note types
    """
    # Define emoji mappings for different note types
    emoji_mapping = {
        'Science Note': '🔬',
        'Context Note': '📚', 
        'Futurist Note': '🚀',
        'Humanist Note': '👥',
        'Literary Note': '📖',
        'Historical Note': '🏛️',
        'Technical Note': '⚙️',
        'Cultural Note': '🎭',
        'Philosophy Note': '🤔',
        'Commentary': '💭',
        'Enhanced Note': '🧭',
        'Annotator Preface': '🤖',
        'Annotator': '🤖'
    }
    
    # Clean up the annotation text
    cleaned_text = annotation_text.strip()
    
    # Split into individual points
    points = re.split(r'•\s*\*?\s*', cleaned_text)
    points = [point.strip() for point in points if point.strip()]
    
    formatted_points = []
    
    for point in points:
        # Extract the note type and content
        match = re.match(r'\*?\*([^*]+)\*\*?:\s*(.*)', point)
        
        if match:
            note_type = match.group(1).strip()
            content = match.group(2).strip()
            
            # Convert any remaining markdown in content to HTML
            content = convert_markdown_to_html(content)
            
            # Find matching emoji
            emoji = '📝'  # Default emoji
            for key, value in emoji_mapping.items():
                if key.lower() in note_type.lower():
                    emoji = value
                    break
            
            # Format the point
            formatted_point = f"""
                <div class="annotation-point">
                    <div class="annotation-type">
                        <span class="annotation-emoji">{emoji}</span>
                        <strong>{note_type}</strong>
                    </div>
                    <div class="annotation-content">{content}</div>
                </div>
            """
            formatted_points.append(formatted_point.strip())
        else:
            # If no pattern matches, just add as general commentary
            if point:
                # Convert markdown to HTML
                formatted_content = convert_markdown_to_html(point)
                formatted_point = f"""
                    <div class="annotation-point">
                        <div class="annotation-type">
                            <span class="annotation-emoji">💭</span>
                            <strong>Commentary</strong>
                        </div>
                        <div class="annotation-content">{formatted_content}</div>
                    </div>
                """
                formatted_points.append(formatted_point.strip())
    
    return '\n'.join(formatted_points)

def get_annotation_css():
    """
    CSS for styled annotations
    """
    return """
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
    """

if __name__ == "__main__":
    # Test the formatting
    test_annotation = """• * **Science Note**: The discovery of Neptune's erratic motion is attributed to astronomers.
• * **Futurist Note**: The revelation foreshadows discovery of other objects."""
    
    result = format_annotation_with_emojis(test_annotation)
    print("Formatted annotation:")
    print(result)