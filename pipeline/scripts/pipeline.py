from scripts.ingest_text import ingest_text
from scripts.annotate_text import annotate_sections
from scripts.build_epub import build_epub
from scripts.config import OPENAI_API_KEY, OLLAMA_SERVERS
from scripts.generate_images import generate_cover_image

import os
import sys
from pathlib import Path

def run_pipeline(manuscript_path, prefer_ollama=True):
   """Run the complete publishing pipeline with enhanced features"""
   print("🚀 Starting publishing pipeline...")
   print(f"🦙 AI Service Priority: {'Ollama (with demo fallback)' if prefer_ollama else 'OpenAI'}")

   # Ingest and process text with enhanced structure
   print(f"📚 Processing text: {manuscript_path}")
   book_data = ingest_text(manuscript_path)

   title = book_data["title"]
   author = book_data["author"]
   sections = book_data["sections"]

   print(f"📖 Book: '{title}' by {author}")
   print(f"📄 Processed {len(sections)} sections")

   # Auto-generate output paths based on manuscript filename
   base_name = Path(manuscript_path).stem
   annotation_path = f"annotations/{base_name}_notes_enhanced.json"
   epub_path = f"output/{base_name}_press.epub"
   book_data_path = f"output/{base_name}_book_data.json"

   # Save book_data for later use (e.g., by rebuild_with_cover.py)
   import json
   with open(book_data_path, 'w', encoding='utf-8') as f:
      json.dump(book_data, f, ensure_ascii=False, indent=2)

   # Generate annotations
   print(f"🤖 Generating AI annotations to {annotation_path} ...")
   annotate_sections(sections, out_path=annotation_path, prefer_ollama=prefer_ollama)

   # Generate book cover and illustrations
   print("🎨 Creating visual elements...")
   cover_path = generate_cover_image(title, author, output_dir="images")

   # Build final enhanced EPUB
   print(f"📚 Building enhanced EPUB: {epub_path} ...")
   build_epub(title, author, annotation_path, epub_path, book_data)

   print(f"""
   🎉 Pipeline complete!

   📁 Generated files:
   📚 EPUB: {epub_path}
   🎨 Cover: {cover_path}
   📝 Annotations: {annotation_path}

   ✨ Features included:
   🤵 Annotator avatar annotations
   🎭 Retro-futuristic styling  
   📖 Enhanced typography
   🗣️ Dialog formatting
   📄 Proper paragraph structure
   🎨 Custom book cover
   """)

if __name__ == "__main__":
   import argparse
   parser = argparse.ArgumentParser(description="Forge Publisher EPUB Pipeline")
   parser.add_argument("--input", "-i", type=str, required=True, help="Path to manuscript text file")
   parser.add_argument("--openai", action="store_true", help="Force use of OpenAI instead of Ollama")
   args = parser.parse_args()
   run_pipeline(args.input, prefer_ollama=not args.openai)
