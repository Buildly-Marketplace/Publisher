#!/usr/bin/env python3
"""
Cover Image Creator - Creates proper EPUB cover from provided image
"""

import os
import base64
from PIL import Image, ImageDraw, ImageFont
import io

def create_cover_image():
    """Create the cover image for EPUB"""
    # Create a placeholder cover image since we need to manually save the attachment
    # This will be replaced when the actual cover is saved
    
    width, height = 800, 1200
    
    # Create steampunk-style cover
    img = Image.new('RGB', (width, height), '#D2691E')  # Soft orange background
    draw = ImageDraw.Draw(img)
    
    # Add gradient effect
    for y in range(height):
        color_intensity = int(210 + (y / height) * 45)  # Gradient from orange to darker
        color = (color_intensity, max(105, color_intensity - 50), 30)
        draw.line([(0, y), (width, y)], fill=color)
    
    # Add title and author
    try:
        # Try to use a nice font
        title_font = ImageFont.truetype("/System/Library/Fonts/Georgia.ttc", 80)
        author_font = ImageFont.truetype("/System/Library/Fonts/Georgia.ttc", 40)
    except:
        # Fallback to default
        title_font = ImageFont.load_default()
        author_font = ImageFont.load_default()
    
    # Add dark overlay for text readability
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 100))
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img)
    
    # Add title
    title_bbox = draw.textbbox((0, 0), "THE STAR", font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    draw.text((title_x, height//3), "THE STAR", fill='#F4E4BC', font=title_font)
    
    # Add author
    author_bbox = draw.textbbox((0, 0), "H.G. WELLS", font=author_font)
    author_width = author_bbox[2] - author_bbox[0]
    author_x = (width - author_width) // 2
    draw.text((author_x, height//3 + 120), "H.G. WELLS", fill='#F4E4BC', font=author_font)
    
    # Add publisher
    pub_text = "PUBLISHER"
    pub_bbox = draw.textbbox((0, 0), pub_text, font=author_font)
    pub_width = pub_bbox[2] - pub_bbox[0]
    pub_x = (width - pub_width) // 2
    draw.text((pub_x, height - 100), pub_text, fill='#CD7F32', font=author_font)
    
    return img

def save_cover_as_jpeg():
    """Save cover as JPEG for EPUB"""
    cover_img = create_cover_image()
    cover_path = "assets/cover.jpg"
    
    # Ensure assets directory exists
    os.makedirs("assets", exist_ok=True)
    
    cover_img.save(cover_path, 'JPEG', quality=90)
    print(f"✅ Cover image saved to: {cover_path}")
    return cover_path

if __name__ == "__main__":
    save_cover_as_jpeg()