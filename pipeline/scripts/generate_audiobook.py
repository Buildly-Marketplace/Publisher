#!/usr/bin/env python3
"""
Audiobook Generation Script
Generates audio for a book using TTS providers.
Called as a background process from the Django UI.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.audio_generator import AudioGenerator, VoiceConfig, setup_metamorphosis_voices
import re


def preprocess_text_for_tts(text: str, use_ssml: bool = True) -> str:
    """Preprocess text to improve TTS pronunciation and pacing.
    
    Fixes common issues like:
    - Abbreviations being read as sentences (H.G. Wells)
    - Excessive pauses in titles
    - Adds natural pauses for better flow
    """
    # Fix common author/name abbreviations
    text = re.sub(r'\bH\.\s*G\.\s*Wells\b', 'H G Wells', text)
    text = re.sub(r'\bH\.\s*G\.\b', 'H G', text)
    text = re.sub(r'\bJ\.\s*R\.\s*R\.\s*Tolkien\b', 'J R R Tolkien', text)
    text = re.sub(r'\bC\.\s*S\.\s*Lewis\b', 'C S Lewis', text)
    text = re.sub(r'\bE\.\s*E\.\s*Cummings\b', 'E E Cummings', text)
    
    # Fix common title abbreviations
    text = re.sub(r'\bMr\.\s', 'Mister ', text)
    text = re.sub(r'\bMrs\.\s', 'Missus ', text)
    text = re.sub(r'\bDr\.\s', 'Doctor ', text)
    text = re.sub(r'\bSt\.\s', 'Saint ', text)
    text = re.sub(r'\bvs\.\s', 'versus ', text)
    text = re.sub(r'\betc\.', 'etcetera', text)
    text = re.sub(r'\be\.g\.', 'for example', text)
    text = re.sub(r'\bi\.e\.', 'that is', text)
    
    # Fix initials pattern (single letters followed by period)
    # Match patterns like "A. B. Name" but not sentence ends
    text = re.sub(r'\b([A-Z])\.\s+(?=[A-Z])', r'\1 ', text)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def text_to_ssml(text: str, voice_style: str = None, rate: str = '-5%') -> str:
    """Convert plain text to SSML for more natural TTS.
    
    Adds:
    - Natural pauses after sentences and commas
    - Emphasis on quoted speech
    - Proper prosody for audiobook reading
    - Voice style if specified (e.g., 'newscast', 'narration-professional')
    """
    # Escape XML special characters
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    # Add natural pauses after sentence endings
    # Longer pause after periods (end of sentence)
    text = re.sub(r'([.!?])\s+', r'\1<break time="400ms"/> ', text)
    
    # Medium pause after colons and semicolons
    text = re.sub(r'([;:])\s+', r'\1<break time="250ms"/> ', text)
    
    # Short pause after commas
    text = re.sub(r',\s+', r',<break time="150ms"/> ', text)
    
    # Add pause after em-dashes
    text = re.sub(r'—\s*', r'<break time="200ms"/>—<break time="200ms"/>', text)
    text = re.sub(r'--\s*', r'<break time="200ms"/>—<break time="200ms"/>', text)
    
    # Add slight emphasis to quoted speech (dialogue)
    def add_dialogue_prosody(match):
        quote = match.group(1)
        return f'<prosody pitch="+2%">"{quote}"</prosody>'
    text = re.sub(r'"([^"]+)"', add_dialogue_prosody, text)
    
    # Wrap in SSML speak tags with prosody
    style_attr = f' style="{voice_style}"' if voice_style else ''
    ssml = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
    <prosody rate="{rate}"{style_attr}>
        {text}
    </prosody>
</speak>'''
    
    return ssml


def load_book_data(book_title: str, pipeline_dir: str) -> dict:
    """Load book data from JSON file or annotations"""
    # Try to find book data
    output_dir = os.path.join(pipeline_dir, 'output')
    
    # Look for book_data.json
    book_slug = book_title.lower().replace(' ', '_')
    data_file = os.path.join(output_dir, f'{book_slug}_book_data.json')
    
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            book_data = json.load(f)
        
        # Normalize sections to dict format
        sections = book_data.get('sections', [])
        normalized_sections = []
        for section in sections:
            if isinstance(section, dict):
                normalized_sections.append({
                    'text': section.get('text', ''),
                    'annotation': section.get('Bob', section.get('annotation', ''))
                })
            else:
                # Plain string section
                normalized_sections.append({
                    'text': str(section),
                    'annotation': ''
                })
        book_data['sections'] = normalized_sections
        return book_data
    
    # Try annotations file
    annotations_dir = os.path.join(pipeline_dir, 'annotations')
    annotation_file = os.path.join(annotations_dir, f'{book_slug}_notes_enhanced.json')
    
    if os.path.exists(annotation_file):
        with open(annotation_file, 'r') as f:
            annotations_data = json.load(f)
            # Handle both dict with 'sections' key and flat list formats
            if isinstance(annotations_data, dict):
                sections_list = annotations_data.get('sections', [])
            else:
                sections_list = annotations_data
            
            # Convert to book data format and filter out frontmatter
            import re
            sections = []
            in_content = False
            for ann in sections_list:
                text = ann.get('text', '') if isinstance(ann, dict) else str(ann)
                annotation = ann.get('Bob', ann.get('annotation', '')) if isinstance(ann, dict) else ''
                
                # Skip sections until we find actual chapter content
                if not in_content:
                    # Check for Gutenberg header markers
                    if 'Project Gutenberg' in text or 'gutenberg.org' in text.lower():
                        continue
                    # Check for chapter markers
                    if re.search(r'^(CHAPTER|Chapter|PART|Part|BOOK|Book|SECTION|Section)\s+[IVX0-9]+', text.strip()):
                        in_content = True
                    # Check for title-only sections (short, no punctuation)
                    elif len(text.strip()) < 150 and not re.search(r'[.!?]$', text.strip()):
                        continue
                    # If it's substantial content, start here
                    elif len(text.strip()) > 200 and re.search(r'[.!?]', text):
                        in_content = True
                
                if in_content:
                    sections.append({
                        'text': text,
                        'annotation': annotation
                    })
            
            return {
                'title': book_title,
                'sections': sections
            }
    
    # Try manuscript file
    manuscripts_dir = os.path.join(pipeline_dir, 'manuscripts')
    manuscript_file = os.path.join(manuscripts_dir, f'{book_slug}.txt')
    
    if os.path.exists(manuscript_file):
        with open(manuscript_file, 'r') as f:
            text = f.read()
            
            # Skip Project Gutenberg header - look for START marker
            start_markers = [
                '*** START OF THE PROJECT GUTENBERG EBOOK',
                '*** START OF THIS PROJECT GUTENBERG EBOOK',
                '*END*THE SMALL PRINT',
            ]
            for marker in start_markers:
                if marker in text:
                    text = text.split(marker, 1)[1]
                    break
            
            # Skip Project Gutenberg footer
            end_markers = [
                '*** END OF THE PROJECT GUTENBERG EBOOK',
                '*** END OF THIS PROJECT GUTENBERG EBOOK',
                'End of the Project Gutenberg',
            ]
            for marker in end_markers:
                if marker in text:
                    text = text.split(marker, 1)[0]
                    break
            
            # Find the first chapter marker and skip everything before it
            import re
            chapter_match = re.search(r'\n\s*(CHAPTER [IVX0-9]+|Chapter [IVX0-9]+|CHAPTER ONE|Chapter One)', text)
            if chapter_match:
                text = text[chapter_match.start():]
            
            # Split into paragraphs as sections
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            
            # Skip sections that are clearly title/frontmatter
            # Check for common patterns that indicate non-content sections
            processed_paragraphs = []
            in_content = False
            for p in paragraphs:
                p_stripped = p.strip()
                # Skip until we find Chapter marker or substantial content
                if not in_content:
                    # Look for chapter markers
                    if re.search(r'^(CHAPTER|Chapter|PART|Part|BOOK|Book|SECTION|Section)\s+[IVX0-9]+', p_stripped):
                        in_content = True
                    # Skip very short lines at the start (likely titles/author)
                    elif len(p_stripped) < 100 and not re.search(r'[.!?]$', p_stripped):
                        continue
                    # If it's long enough and ends with punctuation, probably content
                    elif len(p_stripped) > 200:
                        in_content = True
                
                if in_content:
                    processed_paragraphs.append(preprocess_text_for_tts(p))
            
            return {
                'title': book_title,
                'sections': [{'text': p, 'annotation': ''} for p in processed_paragraphs[:50]]  # Limit for testing
            }
    
    return None


def get_audiobook_version(book_title: str) -> str:
    """Get the next version number for audiobook based on existing successful builds.
    
    Returns version string like '1.0.0', '1.0.1', etc.
    """
    try:
        # Import Django to query existing builds
        import django
        django_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                  'ui')
        sys.path.insert(0, django_dir)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'publisher_django.settings')
        django.setup()
        
        from books.models import AudioBuild, Book
        
        # Find the book
        book = Book.objects.filter(title__iexact=book_title).first()
        if book:
            # Count successful builds
            successful_builds = AudioBuild.objects.filter(
                book=book, 
                status='success'
            ).count()
            return f"1.0.{successful_builds}"
        return "1.0.0"
    except Exception as e:
        print(f"   ⚠️ Could not determine version: {e}")
        return "1.0.0"


def update_build_status(build_id: int, status: str, current_section: int = None, 
                        total_sections: int = None, error_message: str = None,
                        output_path: str = None, duration: int = None, file_size: int = None):
    """Update the AudioBuild record in Django"""
    # Import Django settings
    import django
    django_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                              'ui')
    sys.path.insert(0, django_dir)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'publisher_django.settings')
    django.setup()
    
    from books.models import AudioBuild
    from django.utils import timezone
    
    try:
        build = AudioBuild.objects.get(id=build_id)
        build.status = status
        
        if current_section is not None:
            build.current_section = current_section
        if total_sections is not None:
            build.total_sections = total_sections
        if error_message is not None:
            build.error_message = error_message
        if output_path is not None:
            build.output_path = output_path
        if duration is not None:
            build.duration_seconds = duration
        if file_size is not None:
            build.file_size = file_size
        
        if status in ('success', 'failed'):
            build.completed_at = timezone.now()
        
        build.save()
        print(f"[STATUS] Updated build {build_id}: {status}")
    except Exception as e:
        print(f"[ERROR] Could not update build status: {e}")


def generate_audiobook(build_id: int, book_title: str, provider_type: str = 'pyttsx3',
                       server_url: str = None, narrator_config: dict = None,
                       annotator_config: dict = None, include_annotations: bool = True,
                       style_prompt: str = None, legal_disclaimer: str = None,
                       bumper_path: str = None, outro_path: str = None,
                       start_section: int = 1, end_section: int = None,
                       annotator_intro_stinger: str = None, annotator_outro_stinger: str = None):
    """Generate audiobook for a book
    
    Args:
        build_id: AudioBuild ID for status updates
        book_title: Title of book to generate
        provider_type: TTS provider (pyttsx3, edge-tts, gtts, etc)
        server_url: URL for server-based TTS providers
        narrator_config: Voice config dict for narrator
        annotator_config: Voice config dict for annotator annotations
        include_annotations: Whether to include annotator annotations
        style_prompt: Voice style/tone instructions (e.g. "read in a humorous tone")
        legal_disclaimer: Legal disclaimer text to read at the start
        bumper_path: Path to intro bumper audio file
        outro_path: Path to outro audio file  
        start_section: Section number to start narration from (1-indexed)
        end_section: Section number to end narration at (inclusive)
        annotator_intro_stinger: Path to audio file to play before annotator's annotations
        annotator_outro_stinger: Path to audio file to play after annotator's annotations
    """
    
    print(f"\n{'='*60}")
    print(f"🎙️ AUDIOBOOK GENERATION")
    print(f"{'='*60}")
    print(f"Book: {book_title}")
    print(f"Build ID: {build_id}")
    print(f"Provider: {provider_type}")
    print(f"Include Annotations: {include_annotations}")
    if style_prompt:
        print(f"Style Prompt: {style_prompt[:50]}...")
    if legal_disclaimer:
        print(f"Legal Disclaimer: Yes")
    if bumper_path:
        print(f"Intro Bumper: {bumper_path}")
    if outro_path:
        print(f"Outro: {outro_path}")
    if annotator_intro_stinger or annotator_outro_stinger:
        print(f"Annotator Stingers: intro={bool(annotator_intro_stinger)}, outro={bool(annotator_outro_stinger)}")
    if start_section > 1 or end_section:
        print(f"Section Range: {start_section} to {end_section or 'end'}")
    print(f"{'='*60}\n")
    
    pipeline_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Load book data
    print("📚 Loading book data...")
    book_data = load_book_data(book_title, pipeline_dir)
    
    if not book_data:
        error_msg = f"Could not find book data for '{book_title}'"
        print(f"❌ {error_msg}")
        update_build_status(build_id, 'failed', error_message=error_msg)
        return False
    
    sections = book_data.get('sections', [])
    total_sections = len(sections)
    print(f"   Found {total_sections} sections")
    
    # Filter sections by start/end range
    if start_section > 1 or end_section:
        original_count = len(sections)
        start_idx = max(0, start_section - 1)  # Convert to 0-indexed
        end_idx = end_section if end_section else len(sections)
        sections = sections[start_idx:end_idx]
        print(f"   Filtered to sections {start_section}-{end_idx}: {len(sections)} sections")
    
    # Update build with total sections (after filtering)
    update_build_status(build_id, 'generating', current_section=0, total_sections=len(sections))
    
    # Initialize audio generator
    print(f"\n🔧 Initializing {provider_type} TTS...")
    try:
        generator = AudioGenerator(
            provider=provider_type,
            server_url=server_url,
            sample_rate=24000  # Consistent sample rate for all providers
        )
    except Exception as e:
        error_msg = f"Failed to initialize TTS: {e}"
        print(f"❌ {error_msg}")
        update_build_status(build_id, 'failed', error_message=error_msg)
        return False
    
    # Set up voices
    if narrator_config:
        narrator_voice = VoiceConfig(**narrator_config)
        generator.set_narrator_voice(narrator_voice)
    
    if annotator_config:
        annotator_voice = VoiceConfig(**annotator_config)
        generator.set_annotation_voice(annotator_voice)
    
    # Store style prompt for voice modulation (used by some providers)
    if style_prompt:
        generator.style_prompt = style_prompt
        print(f"   Style prompt set: {style_prompt[:50]}...")
    
    # Set up character voices for known books
    if 'metamorphosis' in book_title.lower():
        setup_metamorphosis_voices(generator)
    
    # Get version number for this audiobook
    version = get_audiobook_version(book_title)
    print(f"\n📦 Audiobook Version: v{version}")
    
    # Create version-specific output directory
    book_slug = book_title.lower().replace(' ', '_')
    output_dir = os.path.join(pipeline_dir, 'output', 'audiobooks', book_slug, f'v{version}')
    os.makedirs(output_dir, exist_ok=True)
    
    # Store version info for filename
    version_suffix = f"_v{version.replace('.', '_')}"
    
    # List to collect all audio segments (bumper, legal, content, outro)
    audio_files = []
    
    # Add intro bumper if provided
    if bumper_path and os.path.exists(bumper_path):
        print(f"\n🎵 Adding intro bumper: {bumper_path}")
        audio_files.append(bumper_path)
    
    # Generate legal disclaimer audio if provided
    if legal_disclaimer and legal_disclaimer.strip():
        print(f"\n⚖️ Generating legal disclaimer audio...")
        try:
            disclaimer_path = os.path.join(output_dir, '000_legal_disclaimer.wav')
            # Use narrator voice for disclaimer
            narrator_voice = generator.narrator_voice or VoiceConfig(
                name='narrator', voice_id='en-US-GuyNeural'
            )
            audio_bytes = generator.synthesize_text(legal_disclaimer, narrator_voice)
            
            # Validate audio bytes before saving
            if not audio_bytes or len(audio_bytes) < 1000:
                raise ValueError(f"TTS returned invalid audio ({len(audio_bytes) if audio_bytes else 0} bytes)")
            
            # Check it's not all zeros (corrupt TTS output)
            if all(b == 0 for b in audio_bytes[:100]):
                raise ValueError("TTS returned empty/corrupt audio (all zeros)")
            
            # Save audio bytes to file
            with open(disclaimer_path, 'wb') as f:
                f.write(audio_bytes)
            
            audio_files.append(disclaimer_path)
            print(f"   ✓ Legal disclaimer generated ({len(audio_bytes)} bytes)")
        except Exception as e:
            print(f"   ⚠️ Could not generate disclaimer: {e}")
    
    # Generate audio for each section
    print(f"\n🎤 Generating audio...")
    total_duration = 0
    total_sections = len(sections)
    
    for i, section in enumerate(sections):
        section_num = i + 1
        print(f"\n   📢 Section {section_num}/{total_sections}...")
        
        try:
            # Get section text
            if isinstance(section, dict):
                section_text = section.get('text', '')
                annotation = section.get('annotation', '') if include_annotations else ''
            else:
                section_text = str(section)
                annotation = ''
            
            if not section_text.strip():
                print(f"      ⏭️ Skipping empty section")
                continue
            
            # Generate section audio
            audio_path = generator.generate_section_audio(
                section_text=section_text,
                section_index=section_num,
                output_dir=output_dir,
                include_annotations=include_annotations and bool(annotation),
                annotation_text=annotation,
                annotator_intro_stinger=annotator_intro_stinger,
                annotator_outro_stinger=annotator_outro_stinger
            )
            
            audio_files.append(audio_path)
            
            # Estimate duration (rough: 150 words/minute)
            word_count = len(section_text.split()) + len(annotation.split())
            section_duration = int(word_count / 2.5)  # seconds
            total_duration += section_duration
            
            # Update progress
            update_build_status(build_id, 'generating', current_section=section_num)
            
            print(f"      ✓ Generated: {os.path.basename(audio_path)}")
            
        except Exception as e:
            print(f"      ⚠️ Error: {e}")
            # Continue with next section
    
    # Add outro if provided
    if outro_path and os.path.exists(outro_path):
        print(f"\n🎵 Adding outro: {outro_path}")
        audio_files.append(outro_path)
    
    # Validate audio files before concatenation - remove invalid/corrupt files
    valid_audio_files = []
    for audio_file in audio_files:
        if not os.path.exists(audio_file):
            print(f"   ⚠️ Skipping missing file: {audio_file}")
            continue
        file_size = os.path.getsize(audio_file)
        if file_size < 1000:
            print(f"   ⚠️ Skipping tiny file ({file_size} bytes): {os.path.basename(audio_file)}")
            continue
        # Check file isn't all zeros (corrupt)
        with open(audio_file, 'rb') as f:
            header = f.read(100)
            if all(b == 0 for b in header):
                print(f"   ⚠️ Skipping corrupt file (all zeros): {os.path.basename(audio_file)}")
                continue
        valid_audio_files.append(audio_file)
    
    audio_files = valid_audio_files
    
    # Combine audio files (if we have multiple)
    print(f"\n🔗 Combining {len(audio_files)} valid audio files...")
    update_build_status(build_id, 'combining')
    
    # Include version in output filename
    final_output = os.path.join(output_dir, f'{book_slug}_audiobook{version_suffix}.wav')
    
    try:
        if len(audio_files) == 1:
            # Just rename/copy single file
            import shutil
            shutil.copy(audio_files[0], final_output)
        elif len(audio_files) > 1:
            # Use ffmpeg to concatenate with proper sample rate handling
            # This avoids sample rate mismatches between bumper/outro and TTS audio
            import wave
            
            # Check if ffmpeg is available for proper concatenation
            ffmpeg_check = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
            
            if ffmpeg_check.returncode == 0:
                # Use ffmpeg concat filter to properly resample and combine
                # First, normalize all files to same sample rate (24000 Hz, mono)
                normalized_files = []
                for i, audio_file in enumerate(audio_files):
                    normalized_path = os.path.join(output_dir, f'_normalized_{i}.wav')
                    resample_cmd = [
                        'ffmpeg', '-y', '-i', audio_file,
                        '-ar', '24000',  # Match TTS sample rate
                        '-ac', '1',      # Mono
                        '-acodec', 'pcm_s16le',
                        normalized_path
                    ]
                    result = subprocess.run(resample_cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        normalized_files.append(normalized_path)
                        print(f"   ✓ Normalized: {os.path.basename(audio_file)}")
                    else:
                        print(f"   ⚠️ Could not normalize {audio_file}: {result.stderr}")
                        # Fall back to original file
                        normalized_files.append(audio_file)
                
                # Create concat file list for ffmpeg
                concat_list_path = os.path.join(output_dir, '_concat_list.txt')
                with open(concat_list_path, 'w') as f:
                    for nf in normalized_files:
                        f.write(f"file '{nf}'\n")
                
                # Concatenate using ffmpeg with proper audio processing to prevent clicks
                # Using audio re-encoding with highpass filter to remove DC offset
                # and ensure smooth transitions between segments
                concat_cmd = [
                    'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                    '-i', concat_list_path,
                    '-af', 'highpass=f=20,apad=pad_dur=0.05,afade=t=in:st=0:d=0.05',  # Remove DC offset, add tiny padding, fade in
                    '-ar', '24000',
                    '-ac', '1',
                    '-acodec', 'pcm_s16le',
                    final_output
                ]
                result = subprocess.run(concat_cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"   ⚠️ FFmpeg concat failed: {result.stderr}")
                    raise Exception("FFmpeg concatenation failed")
                
                # Cleanup normalized temp files
                for nf in normalized_files:
                    if '_normalized_' in nf:
                        try:
                            os.remove(nf)
                        except:
                            pass
                try:
                    os.remove(concat_list_path)
                except:
                    pass
                    
            else:
                # Fallback: use wave module (may have sample rate issues)
                print("   ⚠️ FFmpeg not available, using wave module (may have sample rate issues)")
                with wave.open(final_output, 'wb') as output_wav:
                    for i, audio_file in enumerate(audio_files):
                        try:
                            with wave.open(audio_file, 'rb') as input_wav:
                                if i == 0:
                                    output_wav.setparams(input_wav.getparams())
                                output_wav.writeframes(input_wav.readframes(input_wav.getnframes()))
                        except Exception as e:
                            print(f"   ⚠️ Could not add {audio_file}: {e}")
        else:
            raise Exception("No audio files generated")
        
        # Get WAV file size
        wav_size = os.path.getsize(final_output)
        print(f"   WAV size: {wav_size / (1024*1024):.2f} MB")
        
        # Convert to MP3 if FFmpeg is available
        mp3_output = final_output.replace('.wav', '.mp3')
        converted_to_mp3 = False
        
        try:
            print("\n🔄 Converting to MP3...")
            update_build_status(build_id, 'encoding')
            
            # Check if ffmpeg is available
            result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
            if result.returncode == 0:
                # Convert WAV to MP3 with good quality
                ffmpeg_cmd = [
                    'ffmpeg', '-y',  # Overwrite output
                    '-i', final_output,  # Input WAV
                    '-codec:a', 'libmp3lame',
                    '-qscale:a', '2',  # High quality VBR
                    '-ar', '44100',  # Sample rate
                    mp3_output
                ]
                
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and os.path.exists(mp3_output):
                    converted_to_mp3 = True
                    final_output = mp3_output
                    print(f"   ✅ MP3 created: {mp3_output}")
                    
                    # Clean up WAV file to save space
                    try:
                        os.remove(final_output.replace('.mp3', '.wav'))
                    except:
                        pass
                else:
                    print(f"   ⚠️ FFmpeg failed: {result.stderr}")
            else:
                print("   ℹ️ FFmpeg not available, keeping WAV format")
                print("   Install with: brew install ffmpeg")
        except Exception as e:
            print(f"   ⚠️ MP3 conversion error: {e}")
        
        # Get final file size
        file_size = os.path.getsize(final_output)
        
        print(f"\n✅ Audiobook generated successfully!")
        print(f"   Output: {final_output}")
        print(f"   Size: {file_size / (1024*1024):.2f} MB")
        print(f"   Duration: ~{total_duration // 60} minutes")
        
        # Update build as complete
        update_build_status(
            build_id, 'success',
            output_path=final_output,
            duration=total_duration,
            file_size=file_size
        )
        
        return True
        
    except Exception as e:
        error_msg = f"Failed to combine audio: {e}"
        print(f"❌ {error_msg}")
        update_build_status(build_id, 'failed', error_message=error_msg)
        return False


def main():
    parser = argparse.ArgumentParser(description='Generate audiobook from book data')
    parser.add_argument('--build-id', type=int, required=True, help='AudioBuild ID')
    parser.add_argument('--book-title', type=str, required=True, help='Book title')
    parser.add_argument('--provider', type=str, default='pyttsx3', 
                        choices=['personaplex', 'riva', 'edge-tts', 'pyttsx3', 'gtts'],
                        help='TTS provider')
    parser.add_argument('--server-url', type=str, help='TTS server URL')
    parser.add_argument('--no-annotations', action='store_true', help='Exclude annotations')
    parser.add_argument('--narrator-config', type=str, help='JSON narrator voice config')
    parser.add_argument('--annotator-config', type=str, help='JSON annotator voice config')
    
    # New options
    parser.add_argument('--style-prompt', type=str, help='Voice style/tone instructions')
    parser.add_argument('--legal-disclaimer', type=str, help='Legal disclaimer text to read at start')
    parser.add_argument('--bumper', type=str, help='Path to intro bumper audio file')
    parser.add_argument('--outro', type=str, help='Path to outro audio file')
    parser.add_argument('--start-section', type=int, default=1, help='Section to start narration from')
    parser.add_argument('--end-section', type=int, help='Section to end narration at')
    parser.add_argument('--annotator-intro-stinger', type=str, help='Path to audio stinger before annotator annotations')
    parser.add_argument('--annotator-outro-stinger', type=str, help='Path to audio stinger after annotator annotations')
    
    args = parser.parse_args()
    
    # Parse voice configs if provided
    narrator_config = json.loads(args.narrator_config) if args.narrator_config else None
    annotator_config = json.loads(args.annotator_config) if args.annotator_config else None
    
    success = generate_audiobook(
        build_id=args.build_id,
        book_title=args.book_title,
        provider_type=args.provider,
        server_url=args.server_url,
        narrator_config=narrator_config,
        annotator_config=annotator_config,
        include_annotations=not args.no_annotations,
        style_prompt=args.style_prompt,
        legal_disclaimer=args.legal_disclaimer,
        bumper_path=args.bumper,
        outro_path=args.outro,
        start_section=args.start_section,
        end_section=args.end_section,
        annotator_intro_stinger=args.annotator_intro_stinger,
        annotator_outro_stinger=args.annotator_outro_stinger,
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
