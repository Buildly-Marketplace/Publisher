import json
import requests
import asyncio
import aiohttp
import concurrent.futures
from openai import OpenAI
from pathlib import Path
from .config import OPENAI_API_KEY, OLLAMA_SERVERS, AI_PROVIDERS, OPENAI_CONFIG
import random
import time

def get_openai_client():
    """Create OpenAI client with API key from config (database or .env)"""
    if OPENAI_CONFIG and OPENAI_CONFIG.get('api_key'):
        return OpenAI(
            api_key=OPENAI_CONFIG['api_key'],
            base_url=OPENAI_CONFIG.get('api_url', 'https://api.openai.com/v1')
        )
    return OpenAI(api_key=OPENAI_API_KEY)

def get_available_ollama_servers():
    """Check which Ollama servers are available and return them with their models"""
    available_servers = []
    
    # Get servers from config (database or .env fallback)
    servers_to_check = OLLAMA_SERVERS if OLLAMA_SERVERS else []
    
    if not servers_to_check:
        print("⚠️  No Ollama servers configured.")
        print("   Configure AI providers at: http://localhost:8000/ai/")
        return available_servers
    
    for server_url in servers_to_check:
        try:
            # Use short timeout (3 seconds) for quick fallback
            response = requests.get(f"{server_url}/api/tags", timeout=3)
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_servers.append({
                    "url": server_url,
                    "models": [model["name"] for model in models],
                    "model_count": len(models)
                })
                print(f"✅ Server {server_url}: {len(models)} models available")
            else:
                print(f"⚠️  Server {server_url}: responded with status {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"⏱️  Server {server_url}: connection timeout (server unreachable)")
        except requests.exceptions.ConnectionError:
            print(f"🔌 Server {server_url}: connection refused (server offline or network issue)")
        except Exception as e:
            print(f"❌ Server {server_url}: {e}")
    
    if not available_servers:
        print("")
        print("💡 TIP: No Ollama servers available. The pipeline will use demo mode.")
        print("   Configure AI providers at: http://localhost:8000/ai/")
        print("   Or run Ollama locally: https://ollama.ai")
        print("")
    
    return available_servers

def get_best_ollama_model(server_url=None):
    """Get the best available model for literary annotation work"""
    # Preferred models in order of preference for literary/annotation work
    preferred_models = [
        "qwen2.5",         # Best for witty, concise literary annotations
        "llama3.2",        # Latest Llama model
        "llama3.1",        # Excellent for reasoning and text analysis
        "llama3",          # Good general model
        "mistral",         # Good alternative
        "codellama",       # Good for structured output
        "phi3",            # Efficient smaller model
        "gemma2",          # Good Google model
    ]
    
    # Use the first available server if none specified
    if not server_url and OLLAMA_SERVERS:
        server_url = OLLAMA_SERVERS[0]
    elif not server_url:
        return "llama3.1"
    
    try:
        # Get available models
        response = requests.get(f"{server_url}/api/tags", timeout=10)
        if response.status_code == 200:
            available_models = [model["name"] for model in response.json().get("models", [])]
            
            # Find the best available model
            for preferred in preferred_models:
                for available in available_models:
                    if preferred in available.lower():
                        print(f"🎯 Selected model: {available} on {server_url}")
                        return available, server_url
            
            # If no preferred model found, use the first available
            if available_models:
                model = available_models[0]
                print(f"🎯 Using available model: {model} on {server_url}")
                return model, server_url
        
        print("⚠️  No models found, using default")
        return "llama3.1", server_url
        
    except Exception as e:
        print(f"⚠️  Could not check available models on {server_url}: {e}")
        return "llama3.1", server_url

def generate_annotation_ollama(section_text: str, model: str = None, server_url: str = None, custom_instructions: str = "") -> str:
    """Generate annotation using Ollama local LLM with server selection"""
    if model is None or server_url is None:
        model, server_url = get_best_ollama_model(server_url)
    
    custom_section = ""
    if custom_instructions:
        custom_section = f"\n\nAdditional guidance from the editor:\n{custom_instructions}\n"
    
    prompt = f"""You are the publisher's DELIGHTFULLY witty annotator for classic science fiction.

CRITICAL: Your annotations MUST be GENUINELY FUNNY. Not just informative - actually humorous!

Your comedic style: Think Oscar Wilde meets Neil deGrasse Tyson at a sci-fi convention. Dry wit, clever observations, self-aware humor. You find absurdity in the human condition and gentle irony in how wrong (or right) old predictions were.

HUMOR TECHNIQUES TO USE:
- Deadpan understatement ("Well, that escalated predictably")
- Anachronistic comparisons ("Like tweeting, but with more morse code")
- Self-deprecating scholarly humor
- Playful juxtaposition of then vs. now
- Finding the absurd in the mundane
{custom_section}
For this text, provide commentary in this EXACT format:

1. **Annotator says**: Your genuinely funny one-liner reaction. Make the reader chuckle! (1 sentence, actually be witty!)
2. ONE of these (pick the most relevant, 1-2 sentences WITH HUMOR built in):
   • **Science Note**: Amusing observation about the science - laugh at dated theories or marvel at prescient ones
   • **Context Note**: Historical tidbit delivered with a wry twist or ironic observation
   • **Futurist Note**: Tongue-in-cheek comparison to modern life - "they predicted X but got Y"
   • **Humanist Note**: Self-aware insight about human nature that's both true and funny

THE CARDINAL RULE: If it's not at least a little funny, rewrite it until it is. Wit over word count, always.

Text:
{section_text}

Your annotation:"""
    
    try:
        response = requests.post(
            f"{server_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.8,  # Slightly higher for more creative responses
                    "top_p": 0.9,
                    "num_predict": 350
                }
            },
            timeout=120
        )
        response.raise_for_status()
        result = response.json()["response"].strip()
        
        # Clean up the response if needed
        if result and not result.startswith("•"):
            # If the model didn't format properly, try to extract useful content
            lines = result.split('\n')
            formatted_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith("•"):
                    formatted_lines.append(f"• {line}")
                elif line:
                    formatted_lines.append(line)
            result = '\n'.join(formatted_lines) if formatted_lines else result
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Ollama request failed with model {model} on {server_url}: {e}")
        raise Exception(f"Ollama connection failed: {e}")

def generate_annotation_openai(section_text: str, custom_instructions: str = "") -> str:
    """Generate annotation using OpenAI API"""
    client = get_openai_client()
    
    custom_section = ""
    if custom_instructions:
        custom_section = f"\n\nAdditional guidance from the editor:\n{custom_instructions}\n"
    
    prompt = f"""You are the publisher's DELIGHTFULLY witty annotator for classic science fiction.

CRITICAL: Your annotations MUST be GENUINELY FUNNY. Not just informative - actually humorous!

Your comedic style: Think Oscar Wilde meets Neil deGrasse Tyson at a sci-fi convention. Dry wit, clever observations, self-aware humor.

HUMOR IS MANDATORY. Use:
- Deadpan understatement
- Anachronistic comparisons  
- Self-deprecating scholarly humor
- Playful juxtaposition of then vs. now
{custom_section}
For this text, provide commentary:
1. **Annotator says**: Your genuinely funny one-liner! Make the reader chuckle! (1 sentence)
2. ONE note WITH HUMOR (1-2 sentences): Science, Context, Futurist, or Humanist Note

If it's not funny, rewrite it. Wit over word count.

Text:
{section_text}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8  # Higher for more creative/funny responses
    )
    return response.choices[0].message.content.strip()

def generate_annotation_demo(section_text: str) -> str:
    """Generate demo annotation for testing when AI services are unavailable.
    Attempts to reference specific content from the section with HUMOR."""
    import re
    
    text_lower = section_text.lower()
    notes = []
    
    # Extract a notable quote from the text (first dialogue or interesting phrase)
    dialogue_match = re.search(r'[""]([^""]{20,80})[""]', section_text)
    quote = dialogue_match.group(1) if dialogue_match else None
    
    # Look for character names (capitalized words that appear multiple times)
    words = re.findall(r'\b[A-Z][a-z]+\b', section_text)
    char_candidates = [w for w in set(words) if words.count(w) >= 2 and w not in ['The', 'He', 'She', 'It', 'And', 'But', 'This', 'That', 'When', 'What', 'How']]
    character = char_candidates[0] if char_candidates else None
    
    # Look for transformation/change themes - WITH HUMOR
    if any(word in text_lower for word in ['transform', 'change', 'became', 'awoke', 'found himself', 'vermin', 'insect', 'creature']):
        notes.append("• **Annotator says**: Nothing says 'bad morning' quite like waking up as a different species. We've all had Mondays like this, metaphorically speaking.")
        if quote:
            notes.append(f'• **Humanist Note**: The passage\'s focus on transformation—"{quote[:40]}..."—is basically every teenager\'s Monday morning, except with more legs.')
        else:
            notes.append("• **Humanist Note**: Transformation anxiety is universal—we've all feared waking up one day and not recognizing ourselves. Though usually with fewer antennae.")
    
    # Look for family/relationship themes - WITH HUMOR
    elif any(word in text_lower for word in ['family', 'father', 'mother', 'sister', 'brother', 'parent']):
        notes.append("• **Annotator says**: Family: can't live with 'em, can't metamorphose away from 'em.")
        if character:
            notes.append(f"• **Humanist Note**: The dynamics surrounding {character} prove that awkward family dinners transcend species barriers. At least they still set a place at the table.")
        else:
            notes.append("• **Humanist Note**: Nothing tests familial love quite like unexpected body horror. Thanksgiving dinners will never seem as awkward again.")
    
    # Look for work/duty themes - WITH HUMOR
    elif any(word in text_lower for word in ['work', 'job', 'office', 'boss', 'travel', 'business', 'duty', 'clerk']):
        notes.append("• **Annotator says**: The real horror isn't the transformation—it's missing work. Some fears are timeless.")
        notes.append("• **Futurist Note**: A century later and we're still anxious about disappointing our bosses. At least remote work means no one can see if you've sprouted extra limbs.")
    
    # Look for emotional/psychological themes - WITH HUMOR
    elif any(word in text_lower for word in ['fear', 'terror', 'anxiety', 'horror', 'dread', 'shame', 'guilt', 'worry']):
        notes.append("• **Annotator says**: Ah, existential dread—the universal human experience, now available in invertebrate!")
        notes.append("• **Science Note**: The psychological states depicted here anticipate modern anxiety research by decades. The author didn't need a DSM-5 to know dread when he saw it.")
    
    # Look for physical/bodily themes - WITH HUMOR
    elif any(word in text_lower for word in ['body', 'legs', 'back', 'belly', 'head', 'pain', 'movement', 'crawl']):
        notes.append("• **Annotator says**: The author really commits to the bits. I mean legs. Many, many legs.")
        notes.append("• **Humanist Note**: The detailed bodily descriptions force us to inhabit an alienated form—basically your yoga teacher's worst nightmare made literary.")
    
    # Default notes if nothing specific found - WITH HUMOR
    if not notes:
        if quote:
            notes.append(f"• **Annotator says**: Every time I think I've plumbed the depths of this text, it hands me another shovel.")
            notes.append(f'• **Context Note**: The phrase "{quote[:40]}..." is doing a lot of heavy lifting here—like a forklift, but for existential weight.')
        else:
            notes.append("• **Annotator says**: Another day, another passage that makes me question everything I thought I knew about reality.")
            notes.append("• **Context Note**: This passage exemplifies the author's skill at making you read a sentence three times and still feel like you missed something.")
        
        if character:
            notes.append(f"• **Humanist Note**: Through {character}'s experience, we're reminded that protagonists don't get to choose their problems—only their coping mechanisms.")
        else:
            notes.append("• **Humanist Note**: The writing invites us to see ourselves in the strangest mirrors. Spoiler: we don't always like what we see.")
    
    # Ensure we have at least 2 notes
    if len(notes) < 2:
        notes.append("• **Literary Note**: The prose here demonstrates that skill in creating tension through understatement. Less is more, except when it's less.")
    
    return '\n\n'.join(notes[:3])

def generate_annotation(section_text: str, use_ollama: bool = True, demo_mode: bool = False) -> str:
    """Generate annotation using either Ollama (preferred), OpenAI, or demo mode"""
    if demo_mode:
        return generate_annotation_demo(section_text)
    elif use_ollama:
        return generate_annotation_ollama(section_text)
    else:
        return generate_annotation_openai(section_text)

def annotate_sections(sections, out_path="annotations/annotations.json", prefer_ollama=True, demo_mode=False):
    """Annotate text sections with robust fallback strategy"""
    return annotate_sections_with_context(sections, out_path, prefer_ollama, demo_mode, analysis_context=None)


def annotate_sections_with_context(sections, out_path="annotations/annotations.json", prefer_ollama=True, demo_mode=False, analysis_context=None):
    """Annotate text sections using analysis context for better annotations"""
    annotated = []
    
    # Helper to safely get list items (handles dicts, lists, strings)
    def safe_list(value, max_items=5):
        """Convert various types to a list of strings for joining"""
        if value is None:
            return []
        if isinstance(value, dict):
            # If it's a dict, use the keys
            return list(value.keys())[:max_items]
        if isinstance(value, str):
            return [value]
        if isinstance(value, (list, tuple)):
            # Ensure all items are strings
            return [str(item) for item in value[:max_items]]
        return []
    
    # Build context string from analysis if available
    context_prompt = ""
    if analysis_context:
        themes = analysis_context.get('themes', [])
        characters = analysis_context.get('characters', [])
        setting = analysis_context.get('setting', '')
        tone = analysis_context.get('tone', '')
        scientific = analysis_context.get('scientific_elements', [])
        
        context_parts = []
        if themes:
            theme_list = safe_list(themes)
            if theme_list:
                context_parts.append(f"Key themes: {', '.join(theme_list)}")
        if characters:
            char_list = safe_list(characters)
            if char_list:
                context_parts.append(f"Main characters: {', '.join(char_list)}")
        if setting:
            setting_str = setting if isinstance(setting, str) else str(setting)
            context_parts.append(f"Setting: {setting_str}")
        if tone:
            tone_str = tone if isinstance(tone, str) else str(tone)
            context_parts.append(f"Tone: {tone_str}")
        if scientific:
            sci_list = safe_list(scientific)
            if sci_list:
                context_parts.append(f"Scientific elements to note: {', '.join(sci_list)}")
        
        if context_parts:
            context_prompt = "\n\nCONTEXT FROM ANALYSIS:\n" + "\n".join(context_parts)
            print(f"📚 Using analysis context: {len(context_parts)} elements")
    
    if demo_mode:
        print("🎭 Using demo mode for annotations...")
    elif prefer_ollama:
        print("🦙 Checking Ollama servers for annotations...")
        # Get available servers
        available_servers = get_available_ollama_servers()
        
        if not available_servers:
            print("⚠️  No Ollama servers available, using demo mode")
            demo_mode = True
        else:
            print(f"✅ Using sequential processing with {len(available_servers)} server(s)")
    else:
        print("🤖 Using OpenAI for annotations...")
    
    for i, section in enumerate(sections):
        print(f"📝 Annotating section {i+1}/{len(sections)}...")
        
        # Detect chapter from section content
        chapter = ""
        if section.strip().startswith("Chapter "):
            chapter_match = section.split('\n')[0]
            chapter = chapter_match.strip()
        elif "Chapter I" in section[:50] or section.strip().startswith("I "):
            chapter = "Chapter I"
        
        section_info = {
            'section_num': i + 1,
            'total_sections': len(sections),
            'chapter': chapter
        }
        
        try:
            if demo_mode:
                note = generate_annotation_demo(section)
            elif prefer_ollama and 'available_servers' in locals() and available_servers:
                # Use load balancing - rotate through available servers
                server = available_servers[i % len(available_servers)]
                note = generate_annotation_ollama_with_context(section, context_prompt, server_url=server["url"], section_info=section_info)
            else:
                note = generate_annotation_openai(section)
                
            annotated.append({"section": i, "text": section, "annotation": note})
            print(f"✅ Section {i+1} annotated successfully")
            
        except Exception as e:
            print(f"❌ Error annotating section {i+1}: {e}")
            
            # Fallback strategy
            if prefer_ollama and not demo_mode and 'available_servers' in locals() and available_servers:
                print("🔄 Trying different Ollama servers...")
                success = False
                for backup_server in available_servers:
                    try:
                        note = generate_annotation_ollama_with_context(section, context_prompt, server_url=backup_server["url"], section_info=section_info)
                        annotated.append({"section": i, "text": section, "annotation": note})
                        print(f"✅ Section {i+1} annotated with backup server {backup_server['url']}")
                        success = True
                        break
                    except Exception as e2:
                        print(f"⚠️  Server {backup_server['url']} also failed: {e2}")
                
                if not success:
                    print("🎭 All servers failed, using demo mode...")
                    note = generate_annotation_demo(section)
                    annotated.append({"section": i, "text": section, "annotation": note})
            else:
                print("🎭 Using demo fallback...")
                note = generate_annotation_demo(section)
                annotated.append({"section": i, "text": section, "annotation": note})
    
    # Ensure output directory exists
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(annotated, indent=2), encoding='utf-8')
    print(f"💾 Annotations saved to: {out_path}")
    return annotated


def generate_annotation_ollama_with_context(section_text: str, context_prompt: str = "", model: str = None, server_url: str = None, section_info: dict = None) -> str:
    """Generate annotation using Ollama with analysis context"""
    if model is None or server_url is None:
        model, server_url = get_best_ollama_model(server_url)
    
    # Build section-specific context
    section_context = ""
    if section_info:
        section_num = section_info.get('section_num', 0)
        total_sections = section_info.get('total_sections', 0)
        chapter = section_info.get('chapter', '')
        if chapter:
            section_context = f"\n\nSECTION CONTEXT: This is section {section_num} of {total_sections}, from {chapter}."
        else:
            section_context = f"\n\nSECTION CONTEXT: This is section {section_num} of {total_sections}."
    
    prompt = f"""You are a Forge Publisher annotator creating scholarly commentary for classic literature.

Your tone should be: scholarly yet accessible, satirical but not dismissive, futurist-minded, and deeply humanist.
{context_prompt}{section_context}

IMPORTANT: Your annotations MUST directly reference specific content from this section. Quote or paraphrase specific phrases, events, or imagery from the text below. Do NOT provide generic commentary.

For the following text section, provide 2-3 concise commentary notes. Each note should:
1. Reference a specific quote, phrase, or event from THIS section
2. Explain its significance using one of these lenses:

• **Science Note**: Comment on scientific concepts, accuracy, or speculation
• **Context Note**: Historical, literary, or cultural context  
• **Futurist Note**: How the ideas relate to modern concerns or predictions
• **Humanist Note**: What this reveals about human nature or society

TEXT TO ANNOTATE:
---
{section_text}
---

Provide your annotations as Markdown bullets, with each note citing specific text from above:"""
    
    try:
        print(f"AI_THINKING: Generating annotation with context...")
        response = requests.post(
            f"{server_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 400
                }
            },
            timeout=120,
            stream=True
        )
        
        if response.status_code == 200:
            result = ""
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        text = chunk.get('response', '')
                        result += text
                        # Show thinking in real-time
                        print(text, end='', flush=True)
                    except:
                        pass
            print()  # Newline after streaming
            
            # Clean up the response if needed
            if result and not result.startswith("•"):
                lines = result.split('\n')
                formatted_lines = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("•"):
                        formatted_lines.append(f"• {line}")
                    elif line:
                        formatted_lines.append(line)
                result = '\n'.join(formatted_lines) if formatted_lines else result
            
            return result
        else:
            raise Exception(f"Server returned {response.status_code}")
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Ollama request failed with model {model} on {server_url}: {e}")
        raise Exception(f"Ollama connection failed: {e}")
