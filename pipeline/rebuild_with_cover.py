#!/usr/bin/env python3
"""
Rebuild EPUB with new cover image
Run this after placing your new cover.jpg in assets/
Now supports command-line arguments for dynamic book builds.
"""

import os
import sys
from pathlib import Path
import argparse

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

def rebuild_epub_with_cover(book_title, author, annotation_path, output_path, book_data=None, cover_path=None):
    """Rebuild the EPUB with the specified or default cover image"""
    # Use provided cover_path or default to assets/cover.jpg
    actual_cover_path = cover_path or "assets/cover.jpg"
    if not os.path.exists(actual_cover_path):
        print(f"⚠️  Warning: cover not found at {actual_cover_path}")
        print("   Will attempt to generate a fallback cover.")
        actual_cover_path = None  # Let build_epub generate one
    else:
        # Verify it's an image
        try:
            from PIL import Image
            img = Image.open(actual_cover_path)
            print(f"✅ Cover image found: {img.size} {img.format}")
        except Exception as e:
            print(f"⚠️  Warning: Could not read cover image: {e}")
            actual_cover_path = None
    # Now rebuild the EPUB
    print("\n🚀 Rebuilding EPUB with cover...")
    from build_epub import build_epub
    try:
        build_epub(
            book_title=book_title,
            author=author,
            annotated_json_path=annotation_path,
            output_path=output_path,
            book_data=book_data,
            cover_path=actual_cover_path
        )
        print(f"\n✅ EPUB rebuild complete with new cover!")
        print(f"📁 Output: {output_path}")
        return True
    except Exception as e:
        print(f"❌ ERROR during EPUB build: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    parser = argparse.ArgumentParser(description="Rebuild EPUB with new cover image")
    parser.add_argument('--title', required=True, help='Book title')
    parser.add_argument('--author', required=True, help='Book author')
    parser.add_argument('--annotation', required=True, help='Path to annotation JSON')
    parser.add_argument('--output', required=True, help='Path to output EPUB')
    parser.add_argument('--book_data', default=None, help='(Optional) Path to book_data JSON')
    parser.add_argument('--cover', default=None, help='(Optional) Path to cover image')
    args = parser.parse_args()
    # Optionally load book_data if provided
    book_data = None
    if args.book_data:
        import json
        with open(args.book_data, 'r', encoding='utf-8') as f:
            book_data = json.load(f)
    success = rebuild_epub_with_cover(
        book_title=args.title,
        author=args.author,
        annotation_path=args.annotation,
        output_path=args.output,
        book_data=book_data,
        cover_path=args.cover
    )
    sys.exit(0 if success else 1)
