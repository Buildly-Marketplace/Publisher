import re
import html
from pathlib import Path


def add_paragraph_breaks(text: str) -> str:
    """
    Intelligently add paragraph breaks to text that lacks them.
    Uses dialog patterns, scene changes, and natural reading breaks.
    """
    # If text already has paragraph breaks, return as-is
    if '\n\n' in text:
        return text
    
    # Pattern 1: Dialog - break before opening quotes that follow sentence-ending punctuation
    # Match: '. "Something' or '! "Something' or '? "Something'
    text = re.sub(
        r'([.!?])\s+("|\u201c)([A-Z])',  # \u201c is "
        r'\1\n\n\2\3',
        text
    )
    
    # Pattern 2: Break after closing quotes followed by he/she said patterns and new sentences
    # Match: 'said." The next' or 'replied." When'
    text = re.sub(
        r'(said|replied|answered|called|shouted|whispered|cried|asked|thought|added|exclaimed|muttered)([.!?]"?\s+)([A-Z][a-z])',
        r'\1\2\n\n\3',
        text
    )
    
    # Pattern 3: Scene/time transitions - common transition phrases
    text = re.sub(
        r'([.!?])\s+(The next morning|That evening|Later that day|The following|Meanwhile|Suddenly|At first|Finally|After a while|Soon after|One day|When|That night|It was not until)',
        r'\1\n\n\2',
        text
    )
    
    # Pattern 4: Chapter markers mid-text (Roman numerals)
    text = re.sub(
        r'([.!?]"?)\s+(I{1,3}|IV|V|VI{0,3}|IX|X{1,3})\s+([A-Z][a-z])',
        r'\1\n\n\2\n\n\3',
        text
    )
    
    # Pattern 5: Long sentences followed by "He" or "She" or character names starting new actions
    # This helps break up very long narrative passages
    text = re.sub(
        r'([.!?])\s+(He|She|Gregor|Grete|His father|His mother|His sister|The chief clerk|Mr\. Samsa|Mrs\. Samsa)\s+',
        r'\1\n\n\2 ',
        text
    )
    
    # Clean up any triple+ newlines that may have been created
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text


def clean_gutenberg_text(text: str) -> str:
    """Clean Project Gutenberg text and preserve paragraph structure.
    Handles both plain text and HTML-formatted manuscripts.
    """
    # Remove Gutenberg header/footer
    start = re.search(r"\*\*\* START OF.*?\*\*\*", text)
    end = re.search(r"\*\*\* END OF.*?\*\*\*", text)
    if start and end:
        text = text[start.end():end.start()]
    
    # Check if text appears to be HTML-formatted (contains HTML tags)
    is_html = bool(re.search(r'<[^>]+>', text))
    
    if is_html:
        # Convert HTML paragraph tags to double line breaks
        text = re.sub(r'</p>\s*<p[^>]*>', '\n\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<p[^>]*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
        
        # Convert <br> tags to single line breaks
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        
        # Remove other HTML tags but preserve content
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities (&ldquo; -> ", &mdash; -> —, etc.)
        text = html.unescape(text)
    
    # Clean up but preserve paragraph breaks
    text = re.sub(r'\r\n', '\n', text)  # Normalize line endings
    text = re.sub(r'\n{3,}', '\n\n', text)  # Normalize multiple line breaks to double
    text = re.sub(r'[ \t]+', ' ', text)  # Normalize spaces
    text = text.strip()
    
    # If text lacks paragraph breaks (e.g., from single <p> tag), add them intelligently
    if '\n\n' not in text and len(text) > 1000:
        print("📝 Adding intelligent paragraph breaks...")
        text = add_paragraph_breaks(text)
    
    return text

def is_chapter_marker(text: str) -> bool:
    """Check if text is a chapter marker (Roman numerals, 'Chapter X', etc.)"""
    text = text.strip()
    # Roman numerals (I, II, III, IV, V, etc.)
    if re.match(r'^[IVXLC]+\.?$', text, re.IGNORECASE):
        return True
    # Chapter headers
    if re.match(r'^(Chapter|Part|Book|Section|Act)\s+[\dIVXLC]+', text, re.IGNORECASE):
        return True
    # Just a number
    if re.match(r'^\d+\.?$', text):
        return True
    return False

def split_into_chapters_and_paragraphs(text: str, max_section_length: int = 8000):
    """
    Split text into chapter-based sections (NOT paragraph-level).
    Aims for ~20-50 sections per book, keeping chapters cohesive.
    Only subdivides very long chapters.
    """
    # First, normalize line breaks and clean up the text
    text = re.sub(r'\r\n', '\n', text)  # Normalize Windows line endings
    text = re.sub(r'\r', '\n', text)    # Normalize Mac line endings
    
    # Detect chapter boundaries with various patterns
    chapter_patterns = [
        r'\n\n+(CHAPTER\s+[IVXLC\d]+[^\n]*)\n',  # CHAPTER I, CHAPTER 1, etc
        r'\n\n+(BOOK\s+[IVXLC\d]+[^\n]*)\n',      # BOOK I
        r'\n\n+(PART\s+[IVXLC\d]+[^\n]*)\n',      # PART I, PART ONE
        r'\n\n+([IVXLC]+\.?\s*\n)',                # Roman numerals alone (I., II., etc)
        r'\n\n+(\d+\.?\s*\n)',                     # Numbers alone (1., 2., etc)
    ]
    
    # Try to split by chapter markers
    chapters = []
    remaining_text = text
    
    for pattern in chapter_patterns:
        matches = list(re.finditer(pattern, remaining_text, re.IGNORECASE))
        if len(matches) >= 3:  # Need at least 3 chapter markers to trust this pattern
            print(f"📚 Found {len(matches)} chapters using pattern")
            
            # Split at chapter boundaries
            last_end = 0
            for match in matches:
                # Add text before this chapter marker (if any)
                if match.start() > last_end:
                    pre_text = remaining_text[last_end:match.start()].strip()
                    if pre_text and len(pre_text) > 100:  # Skip tiny fragments
                        chapters.append(pre_text)
                last_end = match.start()
            
            # Add the final chunk
            if last_end < len(remaining_text):
                final_text = remaining_text[last_end:].strip()
                if final_text:
                    chapters.append(final_text)
            break
    
    # If no clear chapter structure, fall back to paragraph grouping
    if not chapters:
        print("📝 No clear chapter markers, grouping paragraphs...")
        paragraphs = re.split(r'\n\n+', text)
        
        current_section = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding this paragraph exceeds max, start new section
            if current_section and len(current_section + "\n\n" + para) > max_section_length:
                chapters.append(current_section.strip())
                current_section = para
            else:
                current_section = (current_section + "\n\n" + para).strip() if current_section else para
        
        if current_section:
            chapters.append(current_section.strip())
    
    # Subdivide any chapters that are too long
    final_sections = []
    for chapter in chapters:
        if len(chapter) > max_section_length * 2:
            # Split long chapters at paragraph boundaries
            sub_sections = split_long_chapter(chapter, max_section_length)
            final_sections.extend(sub_sections)
        else:
            final_sections.append(chapter)
    
    print(f"📄 Created {len(final_sections)} sections (target: 20-50)")
    return final_sections


def split_long_chapter(text: str, max_length: int):
    """Split a long chapter into smaller sections at paragraph boundaries"""
    paragraphs = re.split(r'\n\n+', text)
    sections = []
    current = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        if current and len(current + "\n\n" + para) > max_length:
            sections.append(current.strip())
            current = para
        else:
            current = (current + "\n\n" + para).strip() if current else para
    
    if current:
        sections.append(current.strip())
    
    return sections


def split_by_sentences(text: str, max_section_length: int = 1500):
    """
    Split text by sentences when no paragraph breaks exist.
    Prioritizes CHAPTER detection over character limits.
    Detects chapter markers (Roman numerals like 'II', 'III') mid-text.
    """
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # First, detect and insert chapter breaks
    # Pattern matches Roman numerals (I, II, III, IV, V, etc.) that appear to start a new chapter
    # They typically follow a period/sentence end and precede text that starts a new narrative
    # Match patterns like: "quiet. II It was" or "again. III No-one"
    text = re.sub(
        r'([.!?]["\']*)\s+(I{1,3}|IV|V|VI{0,3}|IX|X{1,3})\s+([A-Z][a-z])',
        r'\1\n\n===CHAPTER:\2===\n\n\3',
        text
    )
    
    # Also match chapter markers at the very start: "I One morning"
    text = re.sub(
        r'^(I{1,3}|IV|V|VI{0,3}|IX|X{1,3})\s+([A-Z][a-z])',
        r'===CHAPTER:\1===\n\n\2',
        text
    )
    
    # Also handle "Chapter X" style markers
    text = re.sub(
        r'([.!?]["\']*)\s+(Chapter\s+\d+|Part\s+\d+)\s+',
        r'\1\n\n===CHAPTER:\2===\n\n',
        text,
        flags=re.IGNORECASE
    )
    
    # Now split by chapter markers first
    chapter_parts = re.split(r'===CHAPTER:([^=]+)===', text)
    
    # chapter_parts will be: [intro_text, chapter1_num, chapter1_text, chapter2_num, chapter2_text, ...]
    sections = []
    
    if len(chapter_parts) > 1:
        # We found chapters - process each one
        print(f"📚 Detected {(len(chapter_parts)-1)//2} chapter(s)")
        
        # Handle any intro text before first chapter
        intro = chapter_parts[0].strip()
        if intro:
            # Split intro by sentences if too long
            intro_sections = split_long_text_by_sentences(intro, max_section_length * 3)
            sections.extend(intro_sections)
        
        # Process each chapter
        for i in range(1, len(chapter_parts), 2):
            chapter_num = chapter_parts[i].strip()
            chapter_text = chapter_parts[i + 1].strip() if i + 1 < len(chapter_parts) else ""
            
            if chapter_text:
                # For chapters, use larger sections (3x max_section_length)
                # This keeps chapters more intact while still allowing some breaking for very long chapters
                chapter_sections = split_long_text_by_sentences(
                    f"Chapter {chapter_num}\n\n{chapter_text}", 
                    max_section_length * 3  # Allow ~4500 chars per section within chapters
                )
                sections.extend(chapter_sections)
    else:
        # No chapters found - fall back to sentence-based splitting
        sections = split_long_text_by_sentences(text, max_section_length)
    
    return sections


def split_long_text_by_sentences(text: str, max_section_length: int):
    """
    Helper function to split long text into sections by sentence boundaries.
    """
    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    
    sections = []
    current_section = ""
    
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        
        # Would adding this sentence exceed max length?
        if current_section and len(current_section + " " + sent) > max_section_length:
            sections.append(current_section.strip())
            current_section = sent
        else:
            if current_section:
                current_section += " " + sent
            else:
                current_section = sent
    
    # Don't forget the last section
    if current_section:
        sections.append(current_section.strip())
    
    return sections

def extract_title_and_author(text: str):
    """
    Extract title and author from the text if possible.
    Handles formats like:
    - "Title by Author"
    - "Title by Author Translated by..."
    - "TITLE or ALTERNATE_TITLE" followed by "WORKS of AUTHOR"
    - Standard Gutenberg headers
    """
    title = "Untitled"  # Default if extraction fails
    author = "Unknown Author"
    
    # Look for patterns in the first 1000 characters
    text_sample = text[:1000].strip()
    lines = text_sample.split('\n')
    
    # Pattern 1: "TITLE or ALTERNATE" on first line, "WORKS of AUTHOR" nearby
    # Example: "OFF ON A COMET or HECTOR SERVADAC" + "WORKS of JULES VERNE"
    first_line = lines[0].strip() if lines else ""
    if re.match(r'^[A-Z][A-Z\s]+(?:\s+or\s+[A-Z\s]+)?$', first_line):
        # Title is on first line (possibly with "or ALTERNATE")
        title_match = re.match(r'^([A-Z][A-Z\s]+?)(?:\s+or\s+[A-Z\s]+)?$', first_line)
        if title_match:
            title = title_match.group(1).strip()
        
        # Look for "WORKS of AUTHOR" pattern in subsequent lines
        for line in lines[1:10]:
            author_match = re.match(r'^(?:WORKS\s+of|by)\s+([A-Z][A-Za-z\s\.]+)$', line.strip(), re.IGNORECASE)
            if author_match:
                author = author_match.group(1).strip()
                break
    
    # Pattern 2: "Title by Author" at the start
    # Match: "Metamorphosis by Franz Kafka Translated by..."
    if title == "Untitled":
        match = re.match(r'^([A-Za-z][A-Za-z\s\'\-]+?)\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text_sample)
        if match:
            title = match.group(1).strip()
            author = match.group(2).strip()
    
    # Pattern 3: Try other common patterns
    if title == "Untitled":
        title_patterns = [
            r'Title:\s*([^\n]+).*?Author:\s*([^\n]+)',
            r'^THE\s+([A-Z][A-Za-z\s]+?)(?:\s+by\s+([A-Z][A-Za-z\s\.]+))?',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text_sample, re.IGNORECASE | re.MULTILINE)
            if match:
                potential_title = match.group(1).strip()
                if len(potential_title) < 50 and len(potential_title) > 2:
                    title = potential_title
                    if len(match.groups()) > 1 and match.group(2):
                        author = match.group(2).strip()
                    break
    
    # Clean up title and author
    title = re.sub(r'\s+', ' ', title).strip().title()
    author = re.sub(r'\s+', ' ', author).strip().title()
    
    return title, author


def strip_front_matter(text: str) -> str:
    """
    Strip publisher info, copyright, introductions, and other front matter.
    Find the actual story start marked by BOOK I, Chapter I, I, etc.
    """
    # Look for common story start markers
    story_start_patterns = [
        r'\n\n(BOOK\s+I\.?\s*\n)',  # "BOOK I" or "BOOK I."
        r'\n\n(PART\s+(ONE|I)\.?\s*\n)',  # "PART ONE" or "PART I"
        r'\n\n(CHAPTER\s+(ONE|I|1)\.?\s*\n)',  # "CHAPTER ONE/I/1"
        r'\n\n(I\.\s*\n[A-Z])',  # Roman numeral I followed by text
        r'\n\n([IVX]+\.\s*\n)',  # Any Roman numeral section marker
        r'\n\n(PROLOGUE\.?\s*\n)',  # PROLOGUE
    ]
    
    for pattern in story_start_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Keep the marker and everything after
            start_pos = match.start()
            print(f"📜 Found story start at position {start_pos}: {text[start_pos:start_pos+50]!r}...")
            return text[start_pos:].strip()
    
    # If no clear story start found, try to strip common front matter sections
    # Look for "INTRODUCTION" or "PREFACE" and skip past it
    intro_patterns = [
        r'INTRODUCTION[^\n]*\n.*?(?=\n\n[A-Z]{3,})',  # Introduction section
        r'PREFACE[^\n]*\n.*?(?=\n\n[A-Z]{3,})',  # Preface section
    ]
    
    for pattern in intro_patterns:
        match = re.search(pattern, text[:5000], re.IGNORECASE | re.DOTALL)
        if match:
            # Find the end of the introduction
            intro_end = match.end()
            remaining = text[intro_end:].strip()
            if remaining:
                print(f"📜 Stripped introduction, continuing from: {remaining[:50]!r}...")
                return remaining
    
    return text

def ingest_text(file_path: str):
    """
    Enhanced text ingestion with proper structure preservation
    """
    text = Path(file_path).read_text(encoding='utf-8')
    
    # Extract metadata before cleaning (from full text including front matter)
    title, author = extract_title_and_author(text)
    
    # Clean Gutenberg formatting
    clean_text = clean_gutenberg_text(text)
    
    # Strip front matter (publisher info, copyright, introductions)
    story_text = strip_front_matter(clean_text)
    
    # Split into well-structured sections
    sections = split_into_chapters_and_paragraphs(story_text)
    
    print(f"📖 Extracted: '{title}' by {author}")
    print(f"📄 Created {len(sections)} sections")
    
    return {
        "title": title,
        "author": author,
        "sections": sections
    }
