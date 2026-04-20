#!/usr/bin/env python3
"""
Cover Image Integration Utility
Integrates the provided steampunk cover art into the EPUB generation
"""

import os
import base64
from PIL import Image
import io

def process_cover_image(cover_path, output_path):
    """Process and optimize the cover image for EPUB"""
    try:
        # Open and optimize the cover image
        with Image.open(cover_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Resize if too large (EPUB readers prefer reasonable sizes)
            max_size = (800, 1200)  # Common EPUB cover size
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save optimized version
            img.save(output_path, 'JPEG', quality=85, optimize=True)
            print(f"Cover image saved to: {output_path}")
            
    except Exception as e:
        print(f"Error processing cover image: {e}")

def get_cover_image_data_uri(image_path):
    """Convert cover image to base64 data URI"""
    try:
        with open(image_path, 'rb') as img_file:
            img_data = img_file.read()
            b64_data = base64.b64encode(img_data).decode('utf-8')
            return f"data:image/jpeg;base64,{b64_data}"
    except Exception as e:
        print(f"Error converting cover to data URI: {e}")
        return None

if __name__ == "__main__":
    # Process the cover image
    import sys
    if len(sys.argv) >= 3:
        cover_input = sys.argv[1]
        cover_output = sys.argv[2]
    else:
        cover_input = "assets/cover.jpg"
        cover_output = "assets/cover_optimized.jpg"
    
    if os.path.exists(cover_input):
        process_cover_image(cover_input, cover_output)
        data_uri = get_cover_image_data_uri(cover_output)
        if data_uri:
            print(f"Cover data URI length: {len(data_uri)} characters")
    else:
        print(f"Cover image not found at: {cover_input}")