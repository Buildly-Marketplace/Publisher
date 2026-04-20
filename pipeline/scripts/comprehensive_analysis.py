#!/usr/bin/env python3
"""
Comprehensive Text Analysis Script
Analyzes entire text using Ollama LLM for accuracy, scientific validity, and adds detailed annotations
"""

import json
import re
import aiohttp
import asyncio
from pathlib import Path
import os
import random
from .config import OLLAMA_SERVERS

class ComprehensiveAnalyzer:
    def __init__(self, text_file_path, existing_annotations_path):
        self.text_file_path = text_file_path
        self.existing_annotations_path = existing_annotations_path
        self.ollama_servers = list(OLLAMA_SERVERS) if OLLAMA_SERVERS else ["http://localhost:11434"]
        self.model_name = "qwen2.5:7b"
        
    async def analyze_text_comprehensively(self):
        """Analyze the entire text for scientific accuracy and add detailed annotations"""
        print("🔬 Starting comprehensive text analysis...")
        
        # Read the original text
        with open(self.text_file_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
        
        # Load existing annotations
        with open(self.existing_annotations_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        # Extract scientific claims and factual statements for analysis
        analysis_sections = self.extract_key_passages(full_text)
        
        print(f"🎯 Identified {len(analysis_sections)} key passages for analysis")
        
        # Analyze each section with LLM
        enhanced_annotations = []
        
        async with aiohttp.ClientSession() as session:
            for i, passage in enumerate(analysis_sections):
                print(f"🔍 Analyzing passage {i+1}/{len(analysis_sections)}...")
                
                # Generate detailed analysis
                analysis = await self.analyze_passage_accuracy(session, passage)
                
                if analysis and analysis.get('needs_annotation'):
                    enhanced_annotations.append({
                        'text': passage['text'][:100] + "...",
                        'full_text': passage['text'],
                        'line_number': passage['line_number'],
                        'analysis': analysis['analysis'],
                        'accuracy_level': analysis['accuracy_level'],
                        'type': analysis['type'],
                        'annotator_comment': analysis['annotator_comment']
                    })
                
                # Small delay to prevent overwhelming servers
                await asyncio.sleep(0.5)
        
        # Merge with existing annotations
        enhanced_data = self.merge_annotations(existing_data, enhanced_annotations)
        
        # Save enhanced annotations
        enhanced_path = self.existing_annotations_path.replace('.json', '_enhanced.json')
        with open(enhanced_path, 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Comprehensive analysis complete! Added {len(enhanced_annotations)} new annotations")
        print(f"📄 Enhanced annotations saved to: {enhanced_path}")
        
        return enhanced_path
    
    def extract_key_passages(self, text):
        """Extract scientifically relevant passages that need analysis"""
        passages = []
        
        # Split into sentences for detailed analysis
        sentences = re.split(r'[.!?]+', text)
        
        scientific_keywords = [
            'star', 'planet', 'astronomy', 'temperature', 'distance', 'mass',
            'gravity', 'tide', 'ocean', 'atmosphere', 'earth', 'sun', 'moon',
            'space', 'celestial', 'orbit', 'scientific', 'phenomenon', 'heat',
            'light', 'radiation', 'magnetic', 'electromagnetic', 'spectrum'
        ]
        
        line_number = 1
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Skip very short fragments
                
                # Check if sentence contains scientific content
                contains_science = any(keyword.lower() in sentence.lower() 
                                     for keyword in scientific_keywords)
                
                # Also include dramatic claims that might need fact-checking
                contains_claim = any(word in sentence.lower() 
                                   for word in ['never', 'impossible', 'always', 
                                               'greatest', 'terrible', 'enormous',
                                               'unprecedented', 'catastrophe'])
                
                if contains_science or contains_claim:
                    passages.append({
                        'text': sentence,
                        'line_number': line_number,
                        'type': 'scientific' if contains_science else 'dramatic_claim'
                    })
                
                line_number += sentence.count('\n') + 1
        
        return passages[:30]  # Limit to prevent overwhelming analysis
    
    async def analyze_passage_accuracy(self, session, passage):
        """Analyze a specific passage for scientific accuracy using Ollama"""
        server = random.choice(self.ollama_servers)
        
        prompt = f"""
        Analyze this text passage from H.G. Wells' "The Star" for scientific accuracy and interesting facts:
        
        "{passage['text']}"
        
        Consider:
        1. Scientific accuracy (astronomy, physics, etc.)
        2. Historical context (1897 knowledge vs modern understanding)
        3. Interesting scientific facts related to the content
        4. Literary vs. scientific interpretation
        
        Respond in JSON format:
        {{
            "needs_annotation": true/false,
            "analysis": "detailed analysis of accuracy and context",
            "accuracy_level": "accurate/partially_accurate/outdated/fictional",
            "type": "scientific_fact/dramatic_effect/period_knowledge/speculation",
            "annotator_comment": "Annotator's witty annotation for readers (if needs_annotation is true)"
        }}
        """
        
        try:
            async with session.post(
                f"{server}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9
                    }
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    response_text = result.get('response', '')
                    
                    # Try to extract JSON from response
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group())
                        except json.JSONDecodeError:
                            # Fallback if JSON parsing fails
                            return {
                                "needs_annotation": True,
                                "analysis": response_text,
                                "accuracy_level": "unknown",
                                "type": "analysis",
                                "annotator_comment": f"🤔 Interesting point about: {passage['text'][:50]}..."
                            }
                    else:
                        return None
                else:
                    print(f"❌ Server error: {response.status}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error analyzing passage: {e}")
            return None
    
    def merge_annotations(self, existing_data, new_annotations):
        """Merge new comprehensive annotations with existing ones"""
        # Handle the existing format which is a list of sections
        existing_sections = existing_data if isinstance(existing_data, list) else existing_data.get('paragraphs', [])
        
        # Convert to enhanced format
        enhanced_data = {
            'sections': existing_sections,
            'enhanced_annotations': new_annotations,
            'total_original_sections': len(existing_sections),
            'total_new_annotations': len(new_annotations),
            'analysis_metadata': {
                'comprehensive_analysis': True,
                'new_annotations_added': len(new_annotations),
                'analysis_type': 'scientific_accuracy_check'
            }
        }
        
        # Try to match new annotations to existing sections
        for annotation in new_annotations:
            # Find the best section to add this annotation to
            target_section = None
            for i, section in enumerate(existing_sections):
                section_text = section.get('text', '')
                if annotation['full_text'][:50] in section_text:
                    target_section = i
                    break
            
            if target_section is not None:
                # Add to existing section
                if 'enhanced_annotations' not in existing_sections[target_section]:
                    existing_sections[target_section]['enhanced_annotations'] = []
                
                existing_sections[target_section]['enhanced_annotations'].append({
                    'text': annotation['text'],
                    'note': annotation['annotator_comment'],
                    'type': annotation['type'],
                    'accuracy': annotation['accuracy_level'],
                    'analysis': annotation['analysis']
                })
        
        return enhanced_data

async def main():
    """Run comprehensive analysis"""
    analyzer = ComprehensiveAnalyzer(
        text_file_path="manuscripts/the_star.txt",
        existing_annotations_path="annotations/the_star_notes.json"
    )
    
    enhanced_annotations_path = await analyzer.analyze_text_comprehensively()
    
    print(f"\n🎉 Comprehensive analysis complete!")
    print(f"📁 Enhanced annotations: {enhanced_annotations_path}")
    print("\n🔄 Ready to rebuild EPUB with enhanced annotations...")

if __name__ == "__main__":
    asyncio.run(main())