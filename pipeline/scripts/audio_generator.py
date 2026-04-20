"""
Audio Generation for Publisher
Generates dramatic readings of books with character-specific voices using:
- NVIDIA PersonaPlex-7B (Hugging Face) - Real-time speech-to-speech
- NVIDIA Riva TTS (Local server)
- Fallback providers (pyttsx3, gTTS)
"""

import os
import re
import json
import wave
import struct
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class VoiceConfig:
    """Configuration for a voice"""
    name: str
    voice_id: str
    pitch: float = 1.0  # Multiplier (0.5 = half pitch, 2.0 = double)
    speed: float = 1.0  # Multiplier (0.5 = half speed, 2.0 = double)
    tone: str = "neutral"  # neutral, dramatic, gentle, stern, etc.
    description: str = ""
    # PersonaPlex-specific settings
    voice_prompt_path: str = None  # Path to voice prompt audio for PersonaPlex
    persona_text: str = None  # Text prompt describing the persona/role
    
    def to_dict(self):
        return {
            'name': self.name,
            'voice_id': self.voice_id,
            'pitch': self.pitch,
            'speed': self.speed,
            'tone': self.tone,
            'description': self.description,
            'voice_prompt_path': self.voice_prompt_path,
            'persona_text': self.persona_text,
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class CharacterVoice:
    """Maps a character name to a voice configuration"""
    character: str
    voice: VoiceConfig
    patterns: List[str] = field(default_factory=list)  # Regex patterns to match this character's speech


# Default voice configurations
DEFAULT_VOICES = {
    'narrator': VoiceConfig(
        name='Narrator',
        voice_id='English-US.Male-1',
        pitch=1.0,
        speed=0.95,
        tone='dramatic',
        description='Deep, dramatic narrator voice'
    ),
    'narrator_female': VoiceConfig(
        name='Narrator (Female)',
        voice_id='English-US.Female-1',
        pitch=1.0,
        speed=0.95,
        tone='dramatic',
        description='Warm, engaging female narrator'
    ),
    'annotator_voice': VoiceConfig(
        name='Annotator',
        voice_id='English-US.Male-2',
        pitch=1.1,
        speed=1.05,
        tone='friendly',
        description='Friendly, knowledgeable voice for annotations'
    ),
    'male_young': VoiceConfig(
        name='Young Male',
        voice_id='English-US.Male-1',
        pitch=1.15,
        speed=1.0,
        tone='neutral',
        description='Youthful male voice'
    ),
    'male_old': VoiceConfig(
        name='Older Male',
        voice_id='English-US.Male-2',
        pitch=0.9,
        speed=0.9,
        tone='stern',
        description='Mature, authoritative male voice'
    ),
    'female_young': VoiceConfig(
        name='Young Female',
        voice_id='English-US.Female-1',
        pitch=1.1,
        speed=1.0,
        tone='gentle',
        description='Youthful female voice'
    ),
    'female_older': VoiceConfig(
        name='Older Female',
        voice_id='English-US.Female-2',
        pitch=0.95,
        speed=0.95,
        tone='warm',
        description='Mature, caring female voice'
    ),
}


class PersonaPlexClient:
    """
    Client for NVIDIA PersonaPlex-7B speech-to-speech model.
    
    PersonaPlex is a real-time, full-duplex speech model that can:
    - Generate speech from text with specific personas
    - Clone voices from audio prompts
    - Handle conversations with natural interruptions
    
    Requires:
    - HF_TOKEN environment variable (accept license at HuggingFace)
    - Running moshi server (local or cloud)
    """
    
    def __init__(self, server_url: str = "wss://localhost:8443", 
                 sample_rate: int = 24000):
        """
        Initialize PersonaPlex client.
        
        Args:
            server_url: WebSocket URL of the moshi server
            sample_rate: Audio sample rate (PersonaPlex uses 24kHz)
        """
        self.server_url = server_url
        self.sample_rate = sample_rate
        self.connected = False
    
    def synthesize(self, text: str, voice_prompt: str = None, 
                   persona_text: str = None, pitch: float = 1.0,
                   speed: float = 1.0) -> bytes:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            voice_prompt: Path to voice prompt audio file (for voice cloning)
            persona_text: Text describing the persona/role
            pitch: Pitch multiplier
            speed: Speed multiplier
        
        Returns: Audio data as bytes (WAV format, 24kHz)
        """
        try:
            # For batch TTS (non-real-time), we use the text-to-speech mode
            # This sends text and receives synthesized audio
            
            import asyncio
            import websockets
            import ssl
            
            async def synthesize_async():
                # Create SSL context for secure connection
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                async with websockets.connect(
                    self.server_url,
                    ssl=ssl_context if self.server_url.startswith('wss') else None
                ) as websocket:
                    # Send synthesis request
                    request = {
                        'type': 'synthesize',
                        'text': text,
                        'persona': persona_text,
                        'voice_prompt': voice_prompt,
                        'sample_rate': self.sample_rate,
                    }
                    
                    await websocket.send(json.dumps(request))
                    
                    # Receive audio chunks
                    audio_chunks = []
                    while True:
                        try:
                            response = await asyncio.wait_for(
                                websocket.recv(), 
                                timeout=30.0
                            )
                            if isinstance(response, bytes):
                                audio_chunks.append(response)
                            else:
                                data = json.loads(response)
                                if data.get('type') == 'done':
                                    break
                                elif data.get('type') == 'error':
                                    raise Exception(data.get('message', 'Unknown error'))
                        except asyncio.TimeoutError:
                            break
                    
                    return b''.join(audio_chunks)
            
            # Run async synthesis
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, create new loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, synthesize_async())
                    return future.result()
            else:
                return loop.run_until_complete(synthesize_async())
                
        except ImportError as e:
            print(f"⚠️ PersonaPlex requires: pip install websockets")
            raise
        except Exception as e:
            print(f"⚠️ PersonaPlex synthesis error: {e}")
            raise
    
    @staticmethod
    def get_setup_instructions() -> str:
        """Get instructions for setting up PersonaPlex"""
        return """
NVIDIA PersonaPlex-7B Setup Instructions
========================================

1. PREREQUISITES:
   - Accept license at: https://huggingface.co/nvidia/personaplex-7b-v1
   - Generate HF token in your Hugging Face settings
   - Set environment variable: export HF_TOKEN=<YOUR_TOKEN>

2. OPTION A: Local Server (requires NVIDIA GPU)
   
   # Clone the repository
   git clone https://github.com/NVIDIA/personaplex
   cd personaplex
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Start the server
   SSL_DIR=$(mktemp -d)
   python -m moshi.server --ssl "$SSL_DIR"
   
   # With CPU offload (if VRAM is insufficient):
   pip install accelerate
   python -m moshi.server --ssl "$SSL_DIR" --cpu-offload

3. OPTION B: Cloud GPU (RunPod/Vast.ai/Lambda Labs)
   
   - Rent RTX 3090/4090 or A100/H100 (~$0.30-0.50/hr)
   - Run the server setup above
   - Configure firewall to expose port 8443
   - Set server_url to your cloud instance

4. OPTION C: Google Colab Pro
   
   - Use T4 or A100 instances for experimentation
   - See example notebooks in the personaplex repo

5. VOICE CUSTOMIZATION:
   
   - Voice Prompts: Provide 5-10 seconds of audio to clone a voice
   - Persona Text: Describe the character's speaking style
   - Example: "You are a dramatic narrator with a deep, resonant voice"
"""


class AudioGenerator:
    """
    Generate audio from text using TTS services.
    Supports:
    - NVIDIA PersonaPlex-7B (Hugging Face) - Real-time speech-to-speech model
    - NVIDIA Riva (Local server)
    - edge-tts (Microsoft Edge neural voices - excellent quality, requires internet)
    - pyttsx3 (Local, no GPU required)
    - gTTS (Google Text-to-Speech)
    """
    
    PROVIDER_PERSONAPLEX = 'personaplex'
    PROVIDER_RIVA = 'riva'
    PROVIDER_EDGE_TTS = 'edge-tts'
    PROVIDER_XTTS = 'xtts'
    PROVIDER_PYTTSX3 = 'pyttsx3'
    PROVIDER_GTTS = 'gtts'
    
    def __init__(self, provider: str = None, server_url: str = None, 
                 sample_rate: int = 24000, hf_token: str = None,
                 cpu_offload: bool = False):
        """
        Initialize the audio generator.
        
        Args:
            provider: TTS provider ('personaplex', 'riva', 'pyttsx3', 'gtts')
            server_url: Server address for PersonaPlex or Riva
            sample_rate: Output audio sample rate in Hz (24000 for PersonaPlex)
            hf_token: Hugging Face token for PersonaPlex
            cpu_offload: Use CPU offload for PersonaPlex (if VRAM insufficient)
        """
        self.provider = provider or self.PROVIDER_PYTTSX3
        self.server_url = server_url
        self.sample_rate = sample_rate
        self.hf_token = hf_token or os.environ.get('HF_TOKEN')
        self.cpu_offload = cpu_offload
        
        # Service clients
        self.personaplex_client = None
        self.riva_client = None
        self.tts_service = None
        self.pyttsx3_engine = None
        self.xtts_model = None
        self.xtts_speaker_wav = None  # Reference audio for voice cloning
        
        # Character voice mappings
        self.character_voices: Dict[str, CharacterVoice] = {}
        self.narrator_voice = DEFAULT_VOICES['narrator']
        self.annotation_voice = DEFAULT_VOICES['annotator_voice']
        
        # Initialize the selected provider
        self._init_provider()
    
    def _init_provider(self):
        """Initialize the selected TTS provider"""
        if self.provider == self.PROVIDER_PERSONAPLEX:
            self._init_personaplex()
        elif self.provider == self.PROVIDER_RIVA:
            self._init_riva()
        elif self.provider == self.PROVIDER_EDGE_TTS:
            self._init_edge_tts()
        elif self.provider == self.PROVIDER_XTTS:
            self._init_xtts()
        elif self.provider == self.PROVIDER_PYTTSX3:
            self._init_pyttsx3()
        elif self.provider == self.PROVIDER_GTTS:
            print("✅ Google TTS ready (requires internet)")
    
    def _init_personaplex(self):
        """Initialize NVIDIA PersonaPlex-7B from Hugging Face"""
        try:
            # Check for HF token
            if not self.hf_token:
                print("⚠️ HF_TOKEN not set. Run: export HF_TOKEN=<YOUR_TOKEN>")
                print("   You must accept the license at https://huggingface.co/nvidia/personaplex-7b-v1")
                return False
            
            # Check if moshi server is running
            if self.server_url:
                print(f"✅ PersonaPlex configured to use server at {self.server_url}")
                self.personaplex_client = PersonaPlexClient(
                    server_url=self.server_url,
                    sample_rate=self.sample_rate
                )
                return True
            
            print("ℹ️ PersonaPlex: No server URL specified.")
            print("   To start local server:")
            print("   1. git clone https://github.com/NVIDIA/personaplex")
            print("   2. cd personaplex")
            print(f"   3. SSL_DIR=$(mktemp -d); python -m moshi.server --ssl \"$SSL_DIR\"")
            if self.cpu_offload:
                print("   (With CPU offload: add --cpu-offload flag)")
            return False
            
        except Exception as e:
            print(f"⚠️ PersonaPlex initialization failed: {e}")
            return False
    
    def _init_riva(self):
        """Initialize NVIDIA Riva client"""
        try:
            import riva.client
            from riva.client.auth import Auth
            
            if not self.server_url:
                self.server_url = 'localhost:50051'
            
            auth = Auth(uri=self.server_url)
            self.tts_service = riva.client.tts.SpeechSynthesisService(auth)
            print(f"✅ Connected to NVIDIA Riva server at {self.server_url}")
            return True
        except Exception as e:
            print(f"⚠️ Could not connect to NVIDIA Riva: {e}")
            return False
    
    def _init_pyttsx3(self):
        """Initialize pyttsx3 local TTS"""
        try:
            import pyttsx3
            self.pyttsx3_engine = pyttsx3.init()
            print("✅ pyttsx3 TTS engine initialized")
            return True
        except Exception as e:
            print(f"⚠️ pyttsx3 not available: {e}")
            print("   Install with: pip install pyttsx3")
            return False
    
    def _init_edge_tts(self):
        """Initialize Edge TTS (Microsoft neural voices via edge-tts)"""
        try:
            import edge_tts
            print("✅ Edge TTS ready (requires internet)")
            print("   Using Microsoft neural voices - excellent quality")
            return True
        except ImportError:
            print("⚠️ edge-tts not available")
            print("   Install with: pip install edge-tts")
            return False
    
    def _init_xtts(self, speaker_wav: str = None):
        """Initialize Coqui XTTS v2 (locally expressive TTS with voice cloning)
        
        Args:
            speaker_wav: Path to reference WAV for voice cloning (6-10 seconds recommended)
        """
        try:
            from TTS.api import TTS
            import torch
            
            # Check for GPU
            device = "cuda" if torch.cuda.is_available() else "cpu"
            if device == "cpu":
                print("⚠️ XTTS running on CPU - will be slow. GPU recommended.")
            
            # Load XTTS v2 model
            print("⏳ Loading Coqui XTTS v2 model (may take a moment)...")
            self.xtts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
            
            # Set speaker reference if provided
            if speaker_wav and os.path.exists(speaker_wav):
                self.xtts_speaker_wav = speaker_wav
                print(f"✅ XTTS ready with voice reference: {speaker_wav}")
            else:
                # Use default speaker from XTTS
                self.xtts_speaker_wav = None
                print("✅ XTTS ready (using default speaker)")
                print("   💡 Tip: Set speaker_wav for voice cloning")
            
            return True
            
        except ImportError:
            print("⚠️ Coqui TTS not available")
            print("   Install with: pip install TTS")
            print("   Note: Requires ~2GB download on first run")
            return False
        except Exception as e:
            print(f"⚠️ XTTS initialization failed: {e}")
            return False
    
    def set_xtts_speaker(self, speaker_wav: str):
        """Set the reference audio for XTTS voice cloning.
        
        Args:
            speaker_wav: Path to WAV file (6-10 seconds of clean speech recommended)
        """
        if os.path.exists(speaker_wav):
            self.xtts_speaker_wav = speaker_wav
            print(f"✅ XTTS speaker set to: {speaker_wav}")
        else:
            print(f"⚠️ Speaker WAV not found: {speaker_wav}")
    
    def set_narrator_voice(self, voice: VoiceConfig):
        """Set the voice for narration"""
        self.narrator_voice = voice
    
    def set_annotation_voice(self, voice: VoiceConfig):
        """Set the voice for annotator annotations"""
        self.annotation_voice = voice
    
    def add_character_voice(self, character: str, voice: VoiceConfig, patterns: List[str] = None):
        """
        Add a voice mapping for a character.
        
        Args:
            character: Character name (e.g., 'Gregor', 'Grete')
            voice: Voice configuration to use
            patterns: Optional list of regex patterns to detect this character's speech
        """
        if patterns is None:
            # Default pattern: "Character said" or "said Character"
            patterns = [
                rf'{character}\s+(said|replied|called|shouted|whispered|asked|thought)',
                rf'(said|replied|called|shouted|whispered|asked)\s+{character}',
            ]
        
        self.character_voices[character.lower()] = CharacterVoice(
            character=character,
            voice=voice,
            patterns=patterns
        )
    
    def detect_speaker(self, text: str, context: str = "") -> str:
        """
        Detect who is speaking based on text patterns.
        
        Returns character name or 'narrator' for narration.
        """
        # Check for character patterns
        for char_name, char_voice in self.character_voices.items():
            for pattern in char_voice.patterns:
                if re.search(pattern, context, re.IGNORECASE):
                    return char_name
        
        # Check for direct speech markers
        if text.startswith('"') or text.startswith('"') or text.startswith("'"):
            # This is dialog - check context for speaker
            for char_name in self.character_voices.keys():
                if char_name in context.lower():
                    return char_name
        
        return 'narrator'
    
    def synthesize_text(self, text: str, voice: VoiceConfig) -> bytes:
        """
        Synthesize speech from text using the specified voice.
        
        Returns: Audio data as bytes (WAV format)
        """
        if self.provider == self.PROVIDER_PERSONAPLEX and self.personaplex_client:
            return self._synthesize_personaplex(text, voice)
        elif self.provider == self.PROVIDER_RIVA and self.tts_service:
            return self._synthesize_riva(text, voice)
        elif self.provider == self.PROVIDER_EDGE_TTS:
            return self._synthesize_edge_tts(text, voice)
        elif self.provider == self.PROVIDER_XTTS and self.xtts_model:
            return self._synthesize_xtts(text, voice)
        elif self.provider == self.PROVIDER_PYTTSX3 and self.pyttsx3_engine:
            return self._synthesize_pyttsx3(text, voice)
        elif self.provider == self.PROVIDER_GTTS:
            return self._synthesize_gtts(text, voice)
        else:
            return self._synthesize_fallback(text, voice)
    
    def _synthesize_personaplex(self, text: str, voice: VoiceConfig) -> bytes:
        """Synthesize using NVIDIA PersonaPlex-7B"""
        try:
            return self.personaplex_client.synthesize(
                text=text,
                voice_prompt=voice.voice_prompt_path,
                persona_text=voice.persona_text or f"You are {voice.name}, speaking with a {voice.tone} tone.",
                pitch=voice.pitch,
                speed=voice.speed
            )
        except Exception as e:
            print(f"⚠️ PersonaPlex synthesis failed: {e}")
            return self._synthesize_fallback(text, voice)
    
    def _synthesize_riva(self, text: str, voice: VoiceConfig) -> bytes:
        """Synthesize using NVIDIA Riva"""
        try:
            import riva.client
            
            response = self.tts_service.synthesize(
                text=text,
                voice_name=voice.voice_id,
                language_code='en-US',
                sample_rate_hz=self.sample_rate,
            )
            
            # Response contains audio data
            return response.audio
            
        except Exception as e:
            print(f"⚠️ Riva synthesis failed: {e}")
            return self._synthesize_fallback(text, voice)
    
    def _synthesize_edge_tts(self, text: str, voice: VoiceConfig) -> bytes:
        """Synthesize using Microsoft Edge TTS (neural voices via edge-tts)
        
        Uses preprocessing for more natural prosody and pacing.
        """
        try:
            import edge_tts
            import asyncio
            import tempfile
            
            # Map voice_id to edge-tts voice names
            # Use newer/better neural voices for audiobook narration
            edge_voice_map = {
                # Our generic voice_ids - use best available voices
                'english-us.male-1': 'en-US-GuyNeural',       # Classic, reliable narrator
                'english-us.male-2': 'en-US-BrianNeural',     # Natural, newer
                'english-us.female-1': 'en-US-JennyNeural',   # Very natural
                'english-us.female-2': 'en-US-AvaNeural',     # High quality, newer
                # Annotator voice - friendly conversational
                'annotator': 'en-US-AndrewNeural',
            }
            
            # Use mapped voice or direct voice name if it starts with 'en-'
            voice_id_lower = voice.voice_id.lower() if voice.voice_id else ''
            if voice_id_lower.startswith('en-'):
                edge_voice = voice.voice_id  # Direct edge-tts voice name
            else:
                edge_voice = edge_voice_map.get(voice_id_lower, 'en-US-GuyNeural')
            
            # Calculate rate for audiobook - slower is better
            # Default to 85% speed for relaxed audiobook pace (vs conversational)
            # This gives listeners time to absorb the text
            if voice.speed == 1.0:
                base_rate = 0.85  # 15% slower for audiobook narration
            else:
                base_rate = voice.speed * 0.90  # Apply their speed but still slower
            rate_percent = int((base_rate - 1.0) * 100)
            rate_str = f"{rate_percent:+d}%"
            
            # Pitch: usually leave neutral for natural reading
            pitch_offset = int((voice.pitch - 1.0) * 50)
            pitch_str = f"{pitch_offset:+d}Hz"
            
            # Preprocess text for natural reading
            processed_text = self._preprocess_for_natural_speech(text)
            
            # Create temp output file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                mp3_path = tmp.name
            
            async def generate():
                communicate = edge_tts.Communicate(processed_text, edge_voice, rate=rate_str, pitch=pitch_str)
                await communicate.save(mp3_path)
            
            # Run async function - handle case where event loop may already be running
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            
            if loop and loop.is_running():
                # Event loop already running (e.g., in Django async context)
                # Use nest_asyncio or run in thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, generate())
                    future.result(timeout=60)
            else:
                # No event loop running, safe to use asyncio.run()
                asyncio.run(generate())
            
            # Convert MP3 to WAV
            wav_path = mp3_path.replace('.mp3', '.wav')
            
            # Use ffmpeg if available, otherwise pydub
            try:
                result = subprocess.run([
                    'ffmpeg', '-y', '-i', mp3_path,
                    '-ar', str(self.sample_rate),
                    '-ac', '1',  # Mono
                    '-sample_fmt', 's16',
                    wav_path
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    raise Exception(f"ffmpeg failed: {result.stderr}")
                    
            except FileNotFoundError:
                # ffmpeg not available, try pydub
                try:
                    from pydub import AudioSegment
                    audio = AudioSegment.from_mp3(mp3_path)
                    audio = audio.set_frame_rate(self.sample_rate).set_channels(1)
                    audio.export(wav_path, format='wav')
                except ImportError:
                    print("⚠️ Neither ffmpeg nor pydub available for MP3->WAV conversion")
                    os.unlink(mp3_path)
                    return self._synthesize_fallback(text, voice)
            
            # Read WAV data
            with open(wav_path, 'rb') as f:
                audio_data = f.read()
            
            # Cleanup
            os.unlink(mp3_path)
            os.unlink(wav_path)
            
            return audio_data
            
        except Exception as e:
            print(f"⚠️ Edge TTS synthesis failed: {e}")
            return self._synthesize_fallback(text, voice)
    
    def _synthesize_xtts(self, text: str, voice: VoiceConfig) -> bytes:
        """Synthesize using Coqui XTTS v2 (expressive, supports voice cloning)
        
        XTTS automatically handles:
        - Emotion detection from text context
        - Natural prosody and pauses  
        - Dialogue differentiation (detects quotes)
        """
        if not self.xtts_model:
            print("⚠️ XTTS model not loaded")
            return self._synthesize_fallback(text, voice)
            
        try:
            import tempfile
            import wave
            import numpy as np
            
            # Preprocess text (XTTS handles most prosody, but we help with abbreviations)
            processed_text = self._preprocess_for_natural_speech(text)
            
            # XTTS can chunk automatically, but we split very long text
            # to avoid memory issues (max ~250 words per chunk)
            max_words = 250
            words = processed_text.split()
            
            if len(words) <= max_words:
                chunks = [processed_text]
            else:
                # Split on sentence boundaries
                import re
                sentences = re.split(r'(?<=[.!?])\s+', processed_text)
                chunks = []
                current_chunk = []
                current_len = 0
                
                for sentence in sentences:
                    sentence_words = len(sentence.split())
                    if current_len + sentence_words > max_words and current_chunk:
                        chunks.append(' '.join(current_chunk))
                        current_chunk = [sentence]
                        current_len = sentence_words
                    else:
                        current_chunk.append(sentence)
                        current_len += sentence_words
                
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
            
            # Synthesize each chunk
            all_audio = []
            
            for chunk in chunks:
                if not chunk.strip():
                    continue
                    
                # XTTS synthesis
                if self.xtts_speaker_wav:
                    # Voice cloning mode
                    wav = self.xtts_model.tts(
                        text=chunk,
                        speaker_wav=self.xtts_speaker_wav,
                        language="en"
                    )
                else:
                    # Use XTTS default speaker
                    wav = self.xtts_model.tts(
                        text=chunk,
                        language="en"
                    )
                
                # Convert to numpy array if not already
                if isinstance(wav, list):
                    wav = np.array(wav)
                
                # Normalize and convert to int16
                wav = np.clip(wav, -1.0, 1.0)
                wav_int16 = (wav * 32767).astype(np.int16)
                all_audio.append(wav_int16)
            
            # Concatenate all chunks
            if all_audio:
                full_audio = np.concatenate(all_audio)
            else:
                return self._synthesize_fallback(text, voice)
            
            # Convert to bytes
            audio_bytes = full_audio.tobytes()
            
            # XTTS outputs at 24kHz - resample if needed
            if self.sample_rate != 24000:
                # Use scipy for resampling if available
                try:
                    from scipy import signal
                    num_samples = int(len(full_audio) * self.sample_rate / 24000)
                    resampled = signal.resample(full_audio, num_samples)
                    audio_bytes = resampled.astype(np.int16).tobytes()
                except ImportError:
                    # Keep at 24kHz if scipy not available
                    pass
            
            # Create WAV with header
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
            
            with wave.open(tmp_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_bytes)
            
            with open(tmp_path, 'rb') as f:
                wav_data = f.read()
            
            os.unlink(tmp_path)
            return wav_data
            
        except Exception as e:
            print(f"⚠️ XTTS synthesis failed: {e}")
            import traceback
            traceback.print_exc()
            return self._synthesize_fallback(text, voice)
    
    def _synthesize_fallback(self, text: str, voice: VoiceConfig) -> bytes:
        """
        Fallback synthesis when primary TTS is unavailable.
        Generates silent placeholder audio.
        """
        # Calculate duration based on text length (rough estimate)
        # Average speaking rate ~150 words/minute = 2.5 words/second
        word_count = len(text.split())
        duration_seconds = max(word_count / 2.5, 0.5)
        
        # Generate silence placeholder
        num_samples = int(self.sample_rate * duration_seconds)
        
        # Create WAV data with silence
        audio_data = struct.pack('<' + 'h' * num_samples, *([0] * num_samples))
        
        return audio_data
    
    def _synthesize_pyttsx3(self, text: str, voice: VoiceConfig) -> bytes:
        """Synthesize using pyttsx3 or macOS 'say' command (local, no GPU required)"""
        import platform
        
        # On macOS, use the native 'say' command for reliable file output
        # pyttsx3's NSSpeechSynthesizer backend has buffering issues with long text
        if platform.system() == 'Darwin':
            return self._synthesize_macos_say(text, voice)
        
        try:
            # Create temp file for output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
            
            # Configure voice
            self.pyttsx3_engine.setProperty('rate', int(150 * voice.speed))
            
            # Adjust pitch if possible (platform-dependent)
            voices = self.pyttsx3_engine.getProperty('voices')
            if voices:
                # Select voice based on voice_id pattern
                for v in voices:
                    if voice.voice_id.lower() in v.id.lower():
                        self.pyttsx3_engine.setProperty('voice', v.id)
                        break
            
            # Save to file
            self.pyttsx3_engine.save_to_file(text, tmp_path)
            self.pyttsx3_engine.runAndWait()
            
            # Read the audio data
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()
            
            os.unlink(tmp_path)
            return audio_data
            
        except Exception as e:
            print(f"⚠️ pyttsx3 synthesis failed: {e}")
            return self._synthesize_fallback(text, voice)
    
    def _get_available_macos_voices(self) -> List[str]:
        """Get list of available macOS voices (cached)"""
        if not hasattr(self, '_macos_voices_cache'):
            try:
                result = subprocess.run(['say', '-v', '?'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Parse voice names from output like "Alex en_US # Hello..."
                    self._macos_voices_cache = [
                        line.split()[0] for line in result.stdout.strip().split('\n')
                        if line.strip()
                    ]
                else:
                    self._macos_voices_cache = []
            except Exception:
                self._macos_voices_cache = []
        return self._macos_voices_cache
    
    def _get_available_macos_voice(self, candidates: List[str]) -> str:
        """Find the first available voice from a list of candidates"""
        available = self._get_available_macos_voices()
        
        for candidate in candidates:
            # Check for exact match or partial match (for voices with parentheses)
            for voice in available:
                if candidate.lower() == voice.lower() or candidate.lower() in voice.lower():
                    return voice
        
        # Return last candidate as fallback (usually a standard voice)
        return candidates[-1] if candidates else 'Alex'
    
    def _synthesize_macos_say(self, text: str, voice: VoiceConfig) -> bytes:
        """Synthesize using macOS native 'say' command - much more reliable than pyttsx3"""
        try:
            # Create temp file for output (say outputs AIFF, we'll convert to WAV)
            with tempfile.NamedTemporaryFile(suffix='.aiff', delete=False) as tmp:
                aiff_path = tmp.name
            wav_path = aiff_path.replace('.aiff', '.wav')
            
            # Map voice_id to macOS voice names
            # Prefer neural/premium voices if available, with fallbacks to standard voices
            # Users can download enhanced voices in: System Settings → Accessibility → Spoken Content → System Voice → Manage Voices
            macos_voice_map = {
                # Male voices - prefer newer/enhanced versions
                'english-us.male-1': ['Evan (Enhanced)', 'Tom', 'Alex'],  # Evan Enhanced is excellent
                'english-us.male-2': ['Oliver (Enhanced)', 'Daniel', 'Fred'],
                # Female voices - prefer newer/enhanced versions  
                'english-us.female-1': ['Zoe (Enhanced)', 'Ava (Enhanced)', 'Samantha'],
                'english-us.female-2': ['Karen (Enhanced)', 'Victoria', 'Allison'],
                # Annotator - friendly conversational voice
                'annotator': ['Evan (Enhanced)', 'Tom', 'Alex'],
            }
            
            # Try to find an available voice
            voice_candidates = macos_voice_map.get(voice.voice_id.lower(), ['Alex'])
            voice_name = self._get_available_macos_voice(voice_candidates)
            
            # Calculate words per minute (macOS default is ~175)
            rate = int(175 * voice.speed)
            
            # Run the say command
            cmd = [
                'say',
                '-v', voice_name,
                '-r', str(rate),
                '-o', aiff_path,
                text
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(f"⚠️ macOS say command failed: {result.stderr}")
                return self._synthesize_fallback(text, voice)
            
            # Convert AIFF to WAV using afconvert
            convert_cmd = [
                'afconvert',
                '-f', 'WAVE',
                '-d', 'LEI16@22050',
                aiff_path,
                wav_path
            ]
            
            result = subprocess.run(convert_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"⚠️ AIFF to WAV conversion failed: {result.stderr}")
                # Try to read AIFF directly
                with open(aiff_path, 'rb') as f:
                    audio_data = f.read()
                os.unlink(aiff_path)
                return audio_data
            
            # Read the WAV data
            with open(wav_path, 'rb') as f:
                audio_data = f.read()
            
            # Cleanup
            os.unlink(aiff_path)
            os.unlink(wav_path)
            
            return audio_data
            
        except subprocess.TimeoutExpired:
            print(f"⚠️ macOS say command timed out for text length {len(text)}")
            return self._synthesize_fallback(text, voice)
        except Exception as e:
            print(f"⚠️ macOS say synthesis failed: {e}")
            return self._synthesize_fallback(text, voice)
    
    def _synthesize_gtts(self, text: str, voice: VoiceConfig) -> bytes:
        """Synthesize using Google Text-to-Speech (requires internet)"""
        try:
            from gtts import gTTS
            import io
            from pydub import AudioSegment
            
            # Create TTS
            tts = gTTS(text=text, lang='en', slow=(voice.speed < 0.9))
            
            # Save to buffer
            mp3_buffer = io.BytesIO()
            tts.write_to_fp(mp3_buffer)
            mp3_buffer.seek(0)
            
            # Convert MP3 to WAV
            audio = AudioSegment.from_mp3(mp3_buffer)
            audio = audio.set_frame_rate(self.sample_rate)
            
            wav_buffer = io.BytesIO()
            audio.export(wav_buffer, format='wav')
            wav_buffer.seek(0)
            
            return wav_buffer.read()
            
        except Exception as e:
            print(f"⚠️ gTTS synthesis failed: {e}")
            return self._synthesize_fallback(text, voice)
    
    def parse_text_for_voices(self, text: str) -> List[Tuple[str, str, VoiceConfig]]:
        """
        Parse text into segments with appropriate voices.
        
        Returns: List of (segment_text, speaker_type, voice_config) tuples
        """
        segments = []
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for sentence in sentences:
            if not sentence.strip():
                continue
            
            # Check if this is dialog
            dialog_match = re.match(r'^["\u201c](.+?)["\u201d](.*)$', sentence)
            
            if dialog_match:
                dialog_text = dialog_match.group(1)
                attribution = dialog_match.group(2)
                
                # Detect speaker from attribution
                speaker = self.detect_speaker(dialog_text, attribution)
                
                if speaker in self.character_voices:
                    voice = self.character_voices[speaker].voice
                else:
                    voice = self.narrator_voice
                
                segments.append((f'"{dialog_text}"', speaker, voice))
                
                if attribution.strip():
                    segments.append((attribution.strip(), 'narrator', self.narrator_voice))
            else:
                segments.append((sentence, 'narrator', self.narrator_voice))
        
        return segments
    
    def generate_section_audio(self, section_text: str, section_index: int, 
                               output_dir: str, include_annotations: bool = True,
                               annotation_text: str = None,
                               annotator_intro_stinger: str = None,
                               annotator_outro_stinger: str = None) -> str:
        """
        Generate audio for a section of the book.
        
        Args:
            section_text: The text content of the section
            section_index: Section number for filename
            output_dir: Directory to save audio files
            include_annotations: Whether to include annotator annotations
            annotation_text: Annotator text for this section
            annotator_intro_stinger: Path to audio file to play before annotator annotation
            annotator_outro_stinger: Path to audio file to play after annotator annotation
        
        Returns: Path to the generated audio file
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        audio_segments = []
        
        # Parse text into voiced segments
        segments = self.parse_text_for_voices(section_text)
        
        for segment_text, speaker, voice in segments:
            audio = self.synthesize_text(segment_text, voice)
            # Apply longer fades to prevent clicks at segment boundaries
            audio = self._apply_fade(audio, fade_in_ms=50, fade_out_ms=80)
            audio_segments.append(audio)
            # Add silence gap between segments for natural pacing
            gap_samples = int(self.sample_rate * 0.15)  # 150ms gap
            gap_audio = struct.pack('<' + 'h' * gap_samples, *([0] * gap_samples))
            audio_segments.append(gap_audio)
        
        # Add annotation audio if requested
        if include_annotations and annotation_text:
            # Add pause before annotation
            pause_samples = int(self.sample_rate * 1.0)  # 1 second pause
            pause_audio = struct.pack('<' + 'h' * pause_samples, *([0] * pause_samples))
            audio_segments.append(pause_audio)
            
            # Add intro stinger if provided
            if annotator_intro_stinger and os.path.exists(annotator_intro_stinger):
                stinger_audio = self._load_audio_file(annotator_intro_stinger)
                if stinger_audio:
                    stinger_audio = self._apply_fade(stinger_audio, fade_in_ms=30, fade_out_ms=50)
                    audio_segments.append(stinger_audio)
                    # Short gap after stinger - just enough to breathe
                    gap_samples = int(self.sample_rate * 0.12)  # 120ms gap (was 400ms)
                    audio_segments.append(struct.pack('<' + 'h' * gap_samples, *([0] * gap_samples)))
            
            # Synthesize annotation
            annotation_audio = self.synthesize_text(
                f"Annotator notes: {annotation_text}",
                self.annotation_voice
            )
            annotation_audio = self._apply_fade(annotation_audio, fade_in_ms=30, fade_out_ms=50)
            audio_segments.append(annotation_audio)
            
            # Add outro stinger if provided
            if annotator_outro_stinger and os.path.exists(annotator_outro_stinger):
                # Gap before stinger
                gap_samples = int(self.sample_rate * 0.4)
                audio_segments.append(struct.pack('<' + 'h' * gap_samples, *([0] * gap_samples)))
                stinger_audio = self._load_audio_file(annotator_outro_stinger)
                if stinger_audio:
                    stinger_audio = self._apply_fade(stinger_audio, fade_in_ms=30, fade_out_ms=50)
                    audio_segments.append(stinger_audio)
            
            # Pause after annotation before next section
            pause_samples = int(self.sample_rate * 0.6)
            audio_segments.append(struct.pack('<' + 'h' * pause_samples, *([0] * pause_samples)))
        
        # Combine all segments
        combined_audio = b''.join(audio_segments)
        
        # Save as WAV file
        output_path = os.path.join(output_dir, f"section_{section_index:03d}.wav")
        self._save_wav(combined_audio, output_path)
        
        return output_path
    
    def _extract_raw_samples(self, audio_data: bytes) -> bytes:
        """Extract raw PCM samples from audio data, stripping any WAV header."""
        if len(audio_data) > 44 and audio_data[:4] == b'RIFF':
            # This is a WAV file - skip 44-byte header
            return audio_data[44:]
        return audio_data
    
    def _remove_dc_offset(self, samples: 'array.array') -> 'array.array':
        """Remove DC offset from audio samples to prevent clicks."""
        import array
        if len(samples) < 100:
            return samples
        
        # Calculate DC offset (average value)
        dc_offset = sum(samples) // len(samples)
        
        # Only remove if significant
        if abs(dc_offset) > 10:
            corrected = array.array('h', [max(-32768, min(32767, s - dc_offset)) for s in samples])
            return corrected
        return samples
    
    def _apply_fade(self, audio_data: bytes, fade_in_ms: int = 20, fade_out_ms: int = 30) -> bytes:
        """Apply fade in/out to audio data to prevent clicks.
        
        Returns RAW PCM samples (no WAV header) for concatenation.
        Uses cosine curve for smoother transitions.
        Also removes DC offset which can cause clicks.
        """
        import array
        import math
        
        # Extract raw samples (strip any WAV header)
        raw_samples = self._extract_raw_samples(audio_data)
        
        # Convert bytes to samples
        samples = array.array('h')
        try:
            samples.frombytes(raw_samples)
        except Exception:
            return raw_samples  # Return as-is if can't parse
        
        if len(samples) < 100:
            return raw_samples
        
        # Remove DC offset first (major cause of clicks)
        samples = self._remove_dc_offset(samples)
        
        # Calculate fade lengths in samples
        fade_in_samples = min(int(self.sample_rate * fade_in_ms / 1000), len(samples) // 4)
        fade_out_samples = min(int(self.sample_rate * fade_out_ms / 1000), len(samples) // 4)
        
        # Apply smooth cosine fade in (sounds more natural than linear)
        for i in range(fade_in_samples):
            # Cosine curve: starts at 0, ends at 1
            factor = (1 - math.cos(math.pi * i / fade_in_samples)) / 2
            samples[i] = int(samples[i] * factor)
        
        # Apply smooth cosine fade out
        for i in range(fade_out_samples):
            idx = len(samples) - 1 - i
            # Cosine curve: starts at 1, ends at 0
            factor = (1 - math.cos(math.pi * i / fade_out_samples)) / 2
            samples[idx] = int(samples[idx] * factor)
        
        # Return RAW samples only (no header) for clean concatenation
        return samples.tobytes()
    
    def _load_audio_file(self, file_path: str) -> bytes:
        """Load an audio file and return raw PCM data, resampling if needed."""
        try:
            # Try to use ffmpeg to convert to our format
            import subprocess
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
            
            # Convert to our sample rate and format
            cmd = [
                'ffmpeg', '-y', '-i', file_path,
                '-ar', str(self.sample_rate),
                '-ac', '1',
                '-acodec', 'pcm_s16le',
                tmp_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                with wave.open(tmp_path, 'rb') as wav:
                    audio_data = wav.readframes(wav.getnframes())
                os.unlink(tmp_path)
                return audio_data
            else:
                print(f"   ⚠️ Could not convert stinger: {result.stderr[:100]}")
                os.unlink(tmp_path)
                return None
                
        except Exception as e:
            print(f"   ⚠️ Could not load stinger {file_path}: {e}")
            return None
        
        return output_path
    
    def _save_wav(self, audio_data: bytes, output_path: str):
        """Save audio data as WAV file"""
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data)
    
    def _preprocess_for_natural_speech(self, text: str) -> str:
        """Preprocess text for more natural TTS output.
        
        Fixes abbreviations and formatting that cause robotic reading.
        Also adds natural pauses and improves prosody cues.
        """
        import re
        
        # Fix common abbreviations that cause unnatural pauses
        text = re.sub(r'\bMr\.\s*', 'Mister ', text)
        text = re.sub(r'\bMrs\.\s*', 'Missus ', text)
        text = re.sub(r'\bDr\.\s*', 'Doctor ', text)
        text = re.sub(r'\bSt\.\s*', 'Saint ', text)
        text = re.sub(r'\bvs\.\s*', 'versus ', text)
        text = re.sub(r'\betc\.', 'etcetera', text)
        text = re.sub(r'\be\.g\.', 'for example', text)
        text = re.sub(r'\bi\.e\.', 'that is', text)
        text = re.sub(r'\bNo\.\s*(\d)', r'Number \1', text)  # No. 5 -> Number 5
        
        # Fix specific well-known names with initials - use phonetic spelling
        # TTS engines pause between single letters, so spell them out phonetically
        text = re.sub(r'\bH\.?\s*G\.?\s*Wells\b', 'Aitch-Gee Wells', text, flags=re.IGNORECASE)
        text = re.sub(r'\bJ\.?\s*R\.?\s*R\.?\s*Tolkien\b', 'Jay-Arr-Arr Tolkien', text, flags=re.IGNORECASE)
        text = re.sub(r'\bC\.?\s*S\.?\s*Lewis\b', 'Cee-Ess Lewis', text, flags=re.IGNORECASE)
        
        # Fix generic initials: A.B. or A. B. -> A B (but not at end of sentence)
        text = re.sub(r'\b([A-Z])\.\s*(?=[A-Z]\.)', r'\1 ', text)  # A.B. -> A B.
        text = re.sub(r'\b([A-Z])\.\s+(?=[A-Z][a-z])', r'\1 ', text)  # A. Smith -> A Smith
        
        # Fix Roman numerals in chapter markers - read as ordinals
        text = re.sub(r'\bChapter\s+I\b(?![VXI])', 'Chapter One', text)
        text = re.sub(r'\bChapter\s+II\b', 'Chapter Two', text)
        text = re.sub(r'\bChapter\s+III\b', 'Chapter Three', text)
        text = re.sub(r'\bChapter\s+IV\b', 'Chapter Four', text)
        text = re.sub(r'\bChapter\s+V\b(?![I])', 'Chapter Five', text)
        text = re.sub(r'\bChapter\s+VI\b', 'Chapter Six', text)
        text = re.sub(r'\bChapter\s+VII\b', 'Chapter Seven', text)
        text = re.sub(r'\bChapter\s+VIII\b', 'Chapter Eight', text)
        text = re.sub(r'\bChapter\s+IX\b', 'Chapter Nine', text)
        text = re.sub(r'\bChapter\s+X\b(?![I])', 'Chapter Ten', text)
        
        # === DIALOGUE HANDLING ===
        # Add pause BEFORE opening quote (signals dialogue is coming)
        # "Hello" becomes ...  "Hello"
        text = re.sub(r'(\w)\s*"', r'\1...  "', text)  # word "quote -> word...  "quote
        text = re.sub(r'([.?!])\s*"(?=[A-Z])', r'\1  ...  "', text)  # End of sentence, new quote
        
        # Add pause after closing quote before narration continues
        text = re.sub(r'"\s*([a-z])', r'"...  \1', text)  # " word -> "...  word (lowercase = narration)
        
        # Fix quotation followed immediately by attribution - add pause
        # "Hello" he said -> "Hello," ... he said
        text = re.sub(r'(["\'])\s*(he|she|they|I|we|it)\s+(said|asked|replied|shouted|whispered|exclaimed|murmured|cried|muttered)', 
                      r'\1,  \2 \3', text, flags=re.IGNORECASE)
        
        # Add emphasis for exclamatory dialogue (edge-tts reads faster with !)
        # Already handled naturally by TTS
        
        # Improve dialogue tag pauses: "Hello," said John. -> "Hello,"... said John.
        text = re.sub(r'([,"])\s+(said|asked|replied|shouted|whispered|exclaimed)', 
                      r'\1...  \2', text, flags=re.IGNORECASE)
        
        # === PARAGRAPH AND SENTENCE FLOW ===
        # Em-dashes become thought pauses
        text = re.sub(r'—', '...  ', text)  # Em-dash gets longer pause
        text = re.sub(r'--', '...  ', text)
        
        # Add breathing room after paragraph breaks (if represented by newlines)
        text = re.sub(r'\n\n+', '...  ', text)  # Paragraph breaks get pause
        text = re.sub(r'\n', ' ', text)
        
        # Add micro-pauses after sentence-ending punctuation for natural pacing
        # This helps TTS engines recognize sentence boundaries
        text = re.sub(r'([.!?])\s+', r'\1   ', text)  # Triple space after sentences
        
        # Add pause after colons (list introductions, etc)
        text = re.sub(r':\s+', ':  ', text)
        
        # Add pause after semicolons (clause boundaries)
        text = re.sub(r';\s+', ';  ', text)
        
        # Add slight pause after commas for better flow
        text = re.sub(r',\s+', ',  ', text)
        
        # Clean up excessive spaces and ellipses (but keep intentional pauses)
        text = re.sub(r'\.{4,}', '...', text)  # Too many dots
        text = re.sub(r'\s{4,}', '   ', text)  # Max triple space
        text = re.sub(r'\.\.\.\s*\.\.\.', '... ', text)  # Double ellipsis
        text = text.strip()
        
        # Ensure sentences end with proper punctuation for TTS pacing
        if text and text[-1] not in '.!?…':
            text += '.'
        
        return text
    
    def generate_book_audio(self, book_data: dict, output_dir: str,
                           include_annotations: bool = True) -> List[str]:
        """
        Generate audio for an entire book.
        
        Args:
            book_data: Book data dict with 'sections' containing text and annotations
            output_dir: Directory to save audio files
            include_annotations: Whether to include annotator annotations
        
        Returns: List of paths to generated audio files
        """
        audio_files = []
        sections = book_data.get('sections', [])
        
        print(f"🎙️ Generating audio for {len(sections)} sections...")
        
        for i, section in enumerate(sections):
            if isinstance(section, dict):
                section_text = section.get('text', '')
                annotation = section.get('annotation', '')
            else:
                section_text = str(section)
                annotation = ''
            
            if section_text.strip():
                print(f"  📢 Section {i + 1}/{len(sections)}...")
                audio_path = self.generate_section_audio(
                    section_text,
                    i + 1,
                    output_dir,
                    include_annotations,
                    annotation
                )
                audio_files.append(audio_path)
        
        print(f"✅ Generated {len(audio_files)} audio files")
        return audio_files
    
    def get_available_voices(self) -> List[VoiceConfig]:
        """Get list of available voices"""
        if self.tts_service:
            # TODO: Query Riva for available voices
            pass
        
        return list(DEFAULT_VOICES.values())
    
    def preview_voice(self, voice: VoiceConfig, sample_text: str = None) -> bytes:
        """
        Generate a preview of a voice.
        
        Args:
            voice: Voice configuration to preview
            sample_text: Optional sample text (defaults to standard preview)
        
        Returns: Audio data as bytes
        """
        if sample_text is None:
            sample_text = f"Hello, I am {voice.name}. This is a preview of how I sound when reading your book."
        
        return self.synthesize_text(sample_text, voice)


def setup_metamorphosis_voices(generator: AudioGenerator):
    """
    Set up character voices for Kafka's Metamorphosis.
    """
    # Gregor Samsa - protagonist, anxious young man
    generator.add_character_voice(
        'Gregor',
        VoiceConfig(
            name='Gregor Samsa',
            voice_id='English-US.Male-1',
            pitch=1.0,
            speed=1.0,
            tone='anxious',
            description='Protagonist - anxious, confused young man'
        ),
        patterns=[
            r'Gregor\s+(said|replied|called|thought|asked)',
            r'(said|replied|thought)\s+Gregor',
            r'".*?"\s*,?\s*said\s+Gregor',
            r'".*?"\s*,?\s*Gregor\s+(said|thought)',
        ]
    )
    
    # Grete - Gregor's caring sister
    generator.add_character_voice(
        'Grete',
        VoiceConfig(
            name='Grete Samsa',
            voice_id='English-US.Female-1',
            pitch=1.1,
            speed=1.0,
            tone='gentle',
            description='Gregor\'s sister - caring but increasingly frustrated'
        )
    )
    
    # Father - stern, authoritative
    generator.add_character_voice(
        'father',
        VoiceConfig(
            name='Mr. Samsa (Father)',
            voice_id='English-US.Male-2',
            pitch=0.85,
            speed=0.9,
            tone='stern',
            description='Gregor\'s father - stern, authoritative'
        ),
        patterns=[
            r'(his\s+)?father\s+(said|called|shouted|asked)',
            r'Mr\.?\s*Samsa\s+(said|called)',
        ]
    )
    
    # Mother - worried, emotional
    generator.add_character_voice(
        'mother',
        VoiceConfig(
            name='Mrs. Samsa (Mother)',
            voice_id='English-US.Female-2',
            pitch=0.95,
            speed=0.95,
            tone='worried',
            description='Gregor\'s mother - worried, emotional'
        ),
        patterns=[
            r'(his\s+)?mother\s+(said|called|cried|asked)',
            r'Mrs\.?\s*Samsa\s+(said|called)',
        ]
    )
    
    # Chief clerk - officious
    generator.add_character_voice(
        'chief clerk',
        VoiceConfig(
            name='Chief Clerk',
            voice_id='English-US.Male-2',
            pitch=1.05,
            speed=1.1,
            tone='officious',
            description='Office supervisor - pompous, officious'
        )
    )


# Example usage
if __name__ == "__main__":
    # Create generator (without Riva server for testing)
    generator = AudioGenerator()
    
    # Set up character voices for Metamorphosis
    setup_metamorphosis_voices(generator)
    
    # Print available voices
    print("Available voices:")
    for voice in generator.get_available_voices():
        print(f"  - {voice.name}: {voice.description}")
    
    print("\nCharacter voices configured:")
    for char, cv in generator.character_voices.items():
        print(f"  - {cv.character}: {cv.voice.description}")
