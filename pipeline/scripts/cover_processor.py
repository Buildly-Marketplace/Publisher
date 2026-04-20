"""
Cover Processor for Publisher
Processes book covers and adds the annotator logo overlay
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io
import base64


def get_annotator_logo_path():
    """Get the path to annotator logo"""
    script_dir = Path(__file__).parent.parent
    # Prioritize Annotator-Badge.png (the official badge logo)
    logo_paths = [
        script_dir / "assets" / "Annotator-Badge.png",
        script_dir / "assets" / "annotator.png",
        script_dir / "assets" / "logo.png",
        script_dir / "assets" / "annotator_avatar.png",
    ]
    for path in logo_paths:
        if path.exists():
            return str(path)
    return None


def process_cover_with_annotator_logo(cover_path, output_path=None, logo_size_ratio=0.15, 
                                  margin_ratio=0.03, logo_opacity=0.9):
    """
    Process a cover image and add the annotator logo to the lower right corner.
    
    Args:
        cover_path: Path to the original cover image
        output_path: Path to save the processed cover (None = same directory with _processed suffix)
        logo_size_ratio: Ratio of logo size relative to cover width (default 15%)
        margin_ratio: Margin from edges as ratio of cover size (default 3%)
        logo_opacity: Opacity of the logo overlay (0.0 to 1.0)
    
    Returns:
        Path to the processed cover image
    """
    if not os.path.exists(cover_path):
        print(f"⚠️  Cover not found: {cover_path}")
        return cover_path  # Return original path
    
    # Find annotator logo
    annotator_logo_path = get_annotator_logo_path()
    if not annotator_logo_path:
        print("⚠️  annotator logo not found, returning original cover")
        return cover_path
    
    try:
        # Load cover image
        cover = Image.open(cover_path).convert("RGBA")
        cover_width, cover_height = cover.size
        
        # Load annotator logo
        annotator_logo = Image.open(annotator_logo_path).convert("RGBA")
        
        # Calculate logo size (proportional to cover width)
        logo_width = int(cover_width * logo_size_ratio)
        logo_height = int(logo_width * annotator_logo.height / annotator_logo.width)
        
        # Resize logo
        annotator_logo = annotator_logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        
        # Apply opacity if needed
        if logo_opacity < 1.0:
            # Split into channels and adjust alpha
            r, g, b, a = annotator_logo.split()
            a = a.point(lambda x: int(x * logo_opacity))
            annotator_logo = Image.merge('RGBA', (r, g, b, a))
        
        # Calculate position (lower right corner with margin)
        margin_x = int(cover_width * margin_ratio)
        margin_y = int(cover_height * margin_ratio)
        
        logo_x = cover_width - logo_width - margin_x
        logo_y = cover_height - logo_height - margin_y
        
        # Create a copy for the processed version
        processed_cover = cover.copy()
        
        # Paste logo with alpha compositing
        processed_cover.paste(annotator_logo, (logo_x, logo_y), annotator_logo)
        
        # Determine output path
        if output_path is None:
            cover_path_obj = Path(cover_path)
            output_path = str(cover_path_obj.parent / f"{cover_path_obj.stem}_processed{cover_path_obj.suffix}")
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save based on format
        if output_path.lower().endswith('.png'):
            processed_cover.save(output_path, 'PNG')
        elif output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
            # Convert to RGB for JPEG
            processed_cover = processed_cover.convert('RGB')
            processed_cover.save(output_path, 'JPEG', quality=95)
        else:
            processed_cover.save(output_path)
        
        print(f"✅ Processed cover with annotator logo: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Error processing cover: {e}")
        return cover_path  # Return original on error


def get_processed_cover_data_uri(cover_path, add_logo=True):
    """
    Get a base64 data URI for the cover, optionally with annotator logo overlay.
    
    Args:
        cover_path: Path to the cover image
        add_logo: Whether to add the annotator logo overlay
    
    Returns:
        Base64 data URI string
    """
    if add_logo:
        # Process in memory without saving
        if not os.path.exists(cover_path):
            return None
        
        annotator_logo_path = get_annotator_logo_path()
        if not annotator_logo_path:
            # Fall back to just the cover
            return _image_to_data_uri(cover_path)
        
        try:
            # Load and process
            cover = Image.open(cover_path).convert("RGBA")
            cover_width, cover_height = cover.size
            
            annotator_logo = Image.open(annotator_logo_path).convert("RGBA")
            
            # Calculate logo size
            logo_width = int(cover_width * 0.15)
            logo_height = int(logo_width * annotator_logo.height / annotator_logo.width)
            annotator_logo = annotator_logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            
            # Position
            margin_x = int(cover_width * 0.03)
            margin_y = int(cover_height * 0.03)
            logo_x = cover_width - logo_width - margin_x
            logo_y = cover_height - logo_height - margin_y
            
            # Composite
            cover.paste(annotator_logo, (logo_x, logo_y), annotator_logo)
            
            # Convert to data URI
            buffer = io.BytesIO()
            if cover_path.lower().endswith('.png'):
                cover.save(buffer, format='PNG')
                mime_type = 'image/png'
            else:
                cover = cover.convert('RGB')
                cover.save(buffer, format='JPEG', quality=90)
                mime_type = 'image/jpeg'
            
            encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return f"data:{mime_type};base64,{encoded}"
            
        except Exception as e:
            print(f"⚠️  Error creating processed cover data URI: {e}")
            return _image_to_data_uri(cover_path)
    else:
        return _image_to_data_uri(cover_path)


def _image_to_data_uri(image_path):
    """Convert an image file to a base64 data URI"""
    if not os.path.exists(image_path):
        return None
    
    try:
        with open(image_path, 'rb') as f:
            data = f.read()
        
        # Determine MIME type
        if image_path.lower().endswith('.png'):
            mime_type = 'image/png'
        elif image_path.lower().endswith('.gif'):
            mime_type = 'image/gif'
        else:
            mime_type = 'image/jpeg'
        
        encoded = base64.b64encode(data).decode('utf-8')
        return f"data:{mime_type};base64,{encoded}"
        
    except Exception as e:
        print(f"⚠️  Error reading image: {e}")
        return None


def process_cover_for_epub(cover_path, output_dir="output"):
    """
    Process a cover for EPUB inclusion: resize if needed, add annotator logo.
    Skips logo overlay if cover appears to already have Publisher branding.
    
    Args:
        cover_path: Path to the original cover
        output_dir: Directory to save the processed cover
    
    Returns:
        Path to the processed cover ready for EPUB
    """
    if not os.path.exists(cover_path):
        print(f"⚠️  Cover not found: {cover_path}")
        return None
    
    # Check if cover already has Publisher branding (skip logo overlay)
    cover_lower = cover_path.lower()
    has_branding = any(keyword in cover_lower for keyword in ['publisher', 'humanist', 'annotator_badge', 'branded'])
    if has_branding:
        print(f"📚 Cover already has Publisher branding, skipping logo overlay")
    
    # Determine output filename
    cover_name = Path(cover_path).stem
    output_path = os.path.join(output_dir, f"{cover_name}_epub_cover.jpg")
    
    try:
        # Load image
        cover = Image.open(cover_path).convert("RGBA")
        original_width, original_height = cover.size
        
        # EPUB recommended cover size: 1400x2100 (or similar 2:3 ratio)
        # Scale to fit within these bounds while maintaining aspect ratio
        max_width = 1400
        max_height = 2100
        
        # Calculate scaling factor
        width_ratio = max_width / original_width
        height_ratio = max_height / original_height
        scale_ratio = min(width_ratio, height_ratio, 1.0)  # Don't upscale
        
        if scale_ratio < 1.0:
            new_width = int(original_width * scale_ratio)
            new_height = int(original_height * scale_ratio)
            cover = cover.resize((new_width, new_height), Image.Resampling.LANCZOS)
            print(f"📐 Resized cover: {original_width}x{original_height} → {new_width}x{new_height}")
        
        # Add annotator logo ONLY if cover doesn't already have branding
        if not has_branding:
            annotator_logo_path = get_annotator_logo_path()
            if annotator_logo_path:
                annotator_logo = Image.open(annotator_logo_path).convert("RGBA")
                
                cover_width, cover_height = cover.size
                logo_width = int(cover_width * 0.12)  # Slightly smaller for EPUB
                logo_height = int(logo_width * annotator_logo.height / annotator_logo.width)
                annotator_logo = annotator_logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            
                margin_x = int(cover_width * 0.03)
                margin_y = int(cover_height * 0.03)
                logo_x = cover_width - logo_width - margin_x
                logo_y = cover_height - logo_height - margin_y
                
                cover.paste(annotator_logo, (logo_x, logo_y), annotator_logo)
                print("🤖 Added annotator logo to cover")
        
        # Convert to RGB for JPEG output
        cover_rgb = cover.convert('RGB')
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save
        cover_rgb.save(output_path, 'JPEG', quality=92)
        print(f"✅ Processed EPUB cover: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"❌ Error processing cover for EPUB: {e}")
        return cover_path  # Return original as fallback


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process book covers with annotator logo")
    parser.add_argument("--input", "-i", required=True, help="Input cover image path")
    parser.add_argument("--output", "-o", help="Output path (optional)")
    parser.add_argument("--epub", action="store_true", help="Process for EPUB inclusion")
    
    args = parser.parse_args()
    
    if args.epub:
        result = process_cover_for_epub(args.input, args.output or "output")
    else:
        result = process_cover_with_annotator_logo(args.input, args.output)
    
    print(f"Result: {result}")
