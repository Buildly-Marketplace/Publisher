import os
import subprocess

MANUSCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'manuscripts')
SCRIPTS_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')

# List all .txt files in manuscripts directory
manuscripts = [f for f in os.listdir(MANUSCRIPTS_DIR) if f.endswith('.txt')]


def process_manuscript(manuscript):
    manuscript_path = os.path.join(MANUSCRIPTS_DIR, manuscript)
    book_name = os.path.splitext(manuscript)[0]
    print(f"Processing: {manuscript}")
    try:
        # Step 1: Ingest text
        ingest_script = os.path.join(SCRIPTS_DIR, 'ingest_text.py')
        subprocess.run(['python3', ingest_script, manuscript_path], check=True)

        # Step 2: Annotate text
        annotate_script = os.path.join(SCRIPTS_DIR, 'annotate_text.py')
        subprocess.run(['python3', annotate_script, manuscript_path], check=True)

        # Step 3: Build EPUB
        build_epub_script = os.path.join(SCRIPTS_DIR, 'build_epub.py')
        output_epub = os.path.join(OUTPUT_DIR, f'{book_name}_press.epub')
        subprocess.run(['python3', build_epub_script, manuscript_path, output_epub], check=True)

        print(f"Finished: {manuscript}\n")
    except subprocess.CalledProcessError as e:
        print(f"Error processing {manuscript}: {e}")
    except Exception as e:
        print(f"Unexpected error with {manuscript}: {e}")

if __name__ == "__main__":
    for manuscript in manuscripts:
        process_manuscript(manuscript)
    print("All manuscripts processed.")
