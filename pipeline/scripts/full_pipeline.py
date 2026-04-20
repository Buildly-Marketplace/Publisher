#!/usr/bin/env python3
"""
Full Publishing Pipeline with Stage Tracking
Runs all processing stages and reports progress
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Import all the processing modules
from scripts.ingest_text import ingest_text
from scripts.annotate_text import annotate_sections, annotate_sections_with_context
from scripts.comprehensive_analysis import ComprehensiveAnalyzer
from scripts.build_epub import build_epub
from scripts.config import OPENAI_API_KEY, OLLAMA_SERVERS, AI_PROVIDERS


class PipelineRunner:
    """Runs the full pipeline with stage tracking"""
    
    STAGES = [
        ('ingesting', 'Ingesting & Parsing Text'),
        ('analyzing', 'Analyzing Text (AI Thinking)'),
        ('annotating', 'Generating AI Annotations'),
        ('building', 'Building Enhanced EPUB'),
    ]
    
    def __init__(self, manuscript_path, output_dir="output", cover_path=None, 
                 title_override=None, author_override=None, prefer_ollama=True):
        self.manuscript_path = manuscript_path
        self.output_dir = output_dir
        self.cover_path = cover_path
        self.title_override = title_override
        self.author_override = author_override
        self.prefer_ollama = prefer_ollama
        
        # Derived paths
        self.base_name = Path(manuscript_path).stem
        self.annotation_path = f"annotations/{self.base_name}_notes.json"
        self.enhanced_annotation_path = f"annotations/{self.base_name}_notes_enhanced.json"
        self.book_data_path = f"{output_dir}/{self.base_name}_book_data.json"
        self.epub_path = f"{output_dir}/{self.base_name}_press.epub"
        
        # Results
        self.book_data = None
        self.stage_logs = []
        self.stats = {
            'sections': 0,
            'annotations': 0,
            'chapters': 0,
        }
    
    def log_stage(self, stage, message, status='running'):
        """Log a stage update"""
        entry = {
            'stage': stage,
            'message': message,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.stage_logs.append(entry)
        # Print for subprocess capture
        print(f"STAGE:{stage}:{status}:{message}")
        sys.stdout.flush()
    
    def run_stage_ingest(self):
        """Stage 1: Ingest and parse the manuscript"""
        self.log_stage('ingesting', 'Reading manuscript file...')
        
        self.book_data = ingest_text(self.manuscript_path)
        
        # Apply overrides if provided
        if self.title_override:
            self.book_data['title'] = self.title_override
        if self.author_override:
            self.book_data['author'] = self.author_override
        
        title = self.book_data['title']
        author = self.book_data['author']
        sections = self.book_data['sections']
        
        self.stats['sections'] = len(sections)
        
        self.log_stage('ingesting', f'Parsed "{title}" by {author}: {len(sections)} sections', 'complete')
        
        # Save book_data for later use
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        with open(self.book_data_path, 'w', encoding='utf-8') as f:
            json.dump(self.book_data, f, ensure_ascii=False, indent=2)
        
        return True
    
    def run_stage_analyze(self):
        """Stage 2: Run comprehensive analysis FIRST to understand the text"""
        self.log_stage('analyzing', 'Starting text analysis...')
        
        sections = self.book_data['sections']
        title = self.book_data['title']
        author = self.book_data['author']
        
        # Create a preliminary analysis of the text
        self.log_stage('analyzing', f'AI is reading and analyzing "{title}"...')
        
        try:
            # Build analysis context from the text
            self.analysis_context = self._analyze_text_context(sections, title, author)
            
            self.log_stage('analyzing', f'Analysis complete: {len(self.analysis_context.get("themes", []))} themes identified', 'complete')
            
            # Save analysis for reference
            analysis_path = f"{self.output_dir}/{self.base_name}_analysis.json"
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
            with open(analysis_path, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_context, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.log_stage('analyzing', f'Analysis error (non-fatal): {e}', 'warning')
            self.analysis_context = {
                'themes': [],
                'characters': [],
                'setting': 'Unknown',
                'tone': 'literary',
                'summary': f'A work by {author}'
            }
        
        return True
    
    def _analyze_text_context(self, sections, title, author):
        """Use AI to analyze the text and extract context for annotations"""
        import requests
        from scripts.config import OLLAMA_SERVERS, AI_PROVIDERS
        
        # Combine first few sections for context
        sample_text = "\n\n".join(sections[:min(5, len(sections))])[:3000]
        
        prompt = f"""You are a literary analyst. Analyze this text excerpt from "{title}" by {author}.

TEXT EXCERPT:
{sample_text}

Provide your analysis as you think through it. Show your reasoning process.

Think step by step:
1. What are the main THEMES? (list 3-5)
2. Who are the main CHARACTERS? (list names and brief roles)
3. What is the SETTING? (time period, location, atmosphere)
4. What is the TONE? (mood, style)
5. What SCIENTIFIC or FACTUAL elements should be noted?
6. What makes this text INTERESTING or SIGNIFICANT?

End with a JSON summary:
```json
{{
  "themes": ["theme1", "theme2", ...],
  "characters": ["character1", "character2", ...],
  "setting": "description of setting",
  "tone": "description of tone",
  "scientific_elements": ["element1", "element2", ...],
  "summary": "2-3 sentence summary"
}}
```"""

        # Get servers and models from database config
        servers_to_try = []
        if AI_PROVIDERS:
            # Use database-configured providers (Ollama type)
            for provider in AI_PROVIDERS:
                if hasattr(provider, 'provider_type') and provider.provider_type == 'ollama':
                    servers_to_try.append({
                        'url': provider.api_url,
                        'model': provider.default_model,
                        'name': provider.name
                    })
        
        # Fallback to OLLAMA_SERVERS if no database providers
        if not servers_to_try and OLLAMA_SERVERS:
            servers_to_try = [{'url': url, 'model': 'llama3.2:1b', 'name': url} for url in OLLAMA_SERVERS]
        
        if not servers_to_try:
            print("AI_THINKING: No AI servers configured!")
            print("AI_THINKING: Configure providers at http://localhost:8000/ai/")
            sys.stdout.flush()
            # Return offline fallback
            return self._offline_analysis(sections, title, author)
        
        # Try each configured server
        server_available = False
        for server_config in servers_to_try:
            server_url = server_config['url']
            model = server_config['model']
            server_name = server_config.get('name', server_url)
            
            try:
                print(f"AI_THINKING: Testing connection to {server_name} ({server_url})...")
                sys.stdout.flush()
                
                # Quick connectivity check first (3 second timeout)
                check_response = requests.get(f"{server_url}/api/tags", timeout=3)
                if check_response.status_code != 200:
                    print(f"AI_THINKING: Server {server_name} not responding, trying next...")
                    sys.stdout.flush()
                    continue
                
                print(f"AI_THINKING: Connected to {server_name}! Using model: {model}")
                sys.stdout.flush()
                server_available = True
                
                response = requests.post(
                    f"{server_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": True,  # Stream to show thinking
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 1000
                        }
                    },
                    timeout=60,
                    stream=True
                )
                
                if response.status_code == 200:
                    full_response = ""
                    print("AI_THINKING: ")
                    sys.stdout.flush()
                    
                    # Stream the response to show AI thinking
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                text = chunk.get('response', '')
                                full_response += text
                                print(text, end='', flush=True)
                            except:
                                pass
                    
                    print("\nAI_THINKING_COMPLETE")
                    sys.stdout.flush()
                    
                    # Extract JSON from response
                    import re
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', full_response, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group(1))
                        except:
                            pass
                    
                    # Fallback: try to find any JSON object
                    json_match = re.search(r'\{[^{}]*"themes"[^{}]*\}', full_response, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group())
                        except:
                            pass
                    
                    # Return basic analysis from text
                    return {
                        'themes': ['transformation', 'alienation', 'family'],
                        'characters': [],
                        'setting': 'Unknown',
                        'tone': 'literary',
                        'scientific_elements': [],
                        'summary': f'Analysis of {title} by {author}',
                        'raw_analysis': full_response
                    }
                    
            except Exception as e:
                print(f"AI_THINKING: Server {server_name} unavailable: {e}")
                sys.stdout.flush()
                continue
        
        # Fallback if no servers available
        return self._offline_analysis(sections, title, author)
    
    def _offline_analysis(self, sections, title, author):
        """Perform offline analysis when no AI servers are available"""
        print("AI_THINKING: ⚠️ No AI servers available - using offline analysis mode")
        print("AI_THINKING: Configure providers at http://localhost:8000/ai/")
        print("AI_THINKING: ")
        print("AI_THINKING: [OFFLINE MODE] Analyzing text structure...")
        print(f"AI_THINKING: - Title: {title}")
        print(f"AI_THINKING: - Author: {author}")
        print(f"AI_THINKING: - Sections: {len(sections)}")
        sys.stdout.flush()
        
        # Try to extract some basic info from the text itself
        all_text = " ".join(sections[:5])[:2000].lower()
        
        # Simple keyword-based theme detection
        themes = []
        theme_keywords = {
            'transformation': ['transform', 'change', 'became', 'metamorphosis', 'converted'],
            'alienation': ['alone', 'isolated', 'stranger', 'foreign', 'outcast'],
            'family': ['family', 'father', 'mother', 'sister', 'brother', 'parent'],
            'identity': ['who am i', 'identity', 'self', 'person'],
            'death': ['death', 'died', 'dying', 'dead', 'mortality'],
            'love': ['love', 'loved', 'heart', 'beloved'],
            'society': ['society', 'social', 'people', 'world'],
            'nature': ['nature', 'natural', 'animal', 'creature'],
        }
        for theme, keywords in theme_keywords.items():
            if any(kw in all_text for kw in keywords):
                themes.append(theme)
                print(f"AI_THINKING: [OFFLINE] Detected theme: {theme}")
                sys.stdout.flush()
        
        if not themes:
            themes = ['literary fiction', 'human condition']
        
        print("AI_THINKING: ")
        print("AI_THINKING: [OFFLINE MODE] Analysis complete")
        print("AI_THINKING_COMPLETE")
        sys.stdout.flush()
        
        return {
            'themes': themes[:5],
            'characters': [],
            'setting': 'To be determined',
            'tone': 'literary',
            'scientific_elements': [],
            'summary': f'{title} by {author} - offline analysis',
            'offline_mode': True
        }
    
    def run_stage_annotate(self):
        """Stage 3: Generate AI annotations using analysis context"""
        self.log_stage('annotating', 'Connecting to AI service...')
        
        sections = self.book_data['sections']
        
        self.log_stage('annotating', f'Annotating {len(sections)} sections with analysis context...')
        
        # Generate annotations with context from analysis
        Path("annotations").mkdir(parents=True, exist_ok=True)
        annotated = annotate_sections_with_context(
            sections, 
            out_path=self.annotation_path, 
            prefer_ollama=self.prefer_ollama,
            analysis_context=getattr(self, 'analysis_context', None)
        )
        
        self.stats['annotations'] = len(annotated)
        
        self.log_stage('annotating', f'Generated {len(annotated)} annotations', 'complete')
        return True
    
    def run_stage_build(self):
        """Stage 4: Build the enhanced EPUB"""
        self.log_stage('building', 'Assembling EPUB structure...')
        
        title = self.book_data['title']
        author = self.book_data['author']
        
        # Use enhanced annotations if available
        annotation_file = self.enhanced_annotation_path
        if not os.path.exists(annotation_file):
            annotation_file = self.annotation_path
        
        self.log_stage('building', f'Using annotations from {annotation_file}')
        
        # Build EPUB
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        build_epub(
            book_title=title,
            author=author,
            annotated_json_path=annotation_file,
            output_path=self.epub_path,
            book_data=self.book_data,
            cover_path=self.cover_path
        )
        
        # Get stats
        if os.path.exists(self.epub_path):
            import zipfile
            try:
                with zipfile.ZipFile(self.epub_path, 'r') as z:
                    chapters = [f for f in z.namelist() if 'chap_' in f and f.endswith('.xhtml')]
                    self.stats['chapters'] = len(chapters)
            except:
                pass
        
        self.log_stage('building', f'EPUB created: {self.epub_path}', 'complete')
        return True
    
    def run(self):
        """Run the full pipeline"""
        print(f"PIPELINE:START:{self.manuscript_path}")
        sys.stdout.flush()
        
        try:
            # Stage 1: Ingest
            if not self.run_stage_ingest():
                return False
            
            # Stage 2: Analyze FIRST (understand the text)
            if not self.run_stage_analyze():
                return False
            
            # Stage 3: Annotate (using analysis context)
            if not self.run_stage_annotate():
                return False
            
            # Stage 4: Build EPUB
            if not self.run_stage_build():
                return False
            
            print(f"PIPELINE:COMPLETE:{self.epub_path}")
            print(f"STATS:{json.dumps(self.stats)}")
            sys.stdout.flush()
            return True
            
        except Exception as e:
            print(f"PIPELINE:ERROR:{str(e)}")
            sys.stdout.flush()
            return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Forge Publisher Full Pipeline")
    parser.add_argument("--input", "-i", required=True, help="Path to manuscript")
    parser.add_argument("--output", "-o", default="output", help="Output directory")
    parser.add_argument("--cover", "-c", help="Path to cover image")
    parser.add_argument("--title", "-t", help="Override book title")
    parser.add_argument("--author", "-a", help="Override book author")
    parser.add_argument("--openai", action="store_true", help="Use OpenAI instead of Ollama")
    
    args = parser.parse_args()
    
    runner = PipelineRunner(
        manuscript_path=args.input,
        output_dir=args.output,
        cover_path=args.cover,
        title_override=args.title,
        author_override=args.author,
        prefer_ollama=not args.openai
    )
    
    success = runner.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
