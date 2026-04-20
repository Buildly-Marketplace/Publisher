from django.db import models
from django.utils import timezone
import os
import requests
import json


class AIProvider(models.Model):
    """Model to configure AI providers (Ollama, OpenAI, etc.)"""
    PROVIDER_TYPES = [
        ('ollama', 'Ollama (Local/Network)'),
        ('openai', 'OpenAI API'),
    ]
    
    name = models.CharField(max_length=100, help_text="Friendly name for this configuration")
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPES, default='ollama')
    
    # Connection settings
    api_url = models.URLField(
        max_length=255, 
        default="http://localhost:11434",
        help_text="For Ollama: http://localhost:11434 or http://your-server:11434. For OpenAI: https://api.openai.com/v1"
    )
    api_key = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Required for OpenAI, optional for Ollama"
    )
    
    # Model settings
    default_model = models.CharField(
        max_length=100, 
        default="llama3.2:1b",
        help_text="Model to use (e.g., llama3.2:1b, gpt-4o-mini)"
    )
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Enable/disable this provider")
    is_primary = models.BooleanField(default=False, help_text="Use as the primary AI provider")
    priority = models.IntegerField(default=0, help_text="Higher priority = tried first (for fallback)")
    
    # Connection status (cached)
    last_tested = models.DateTimeField(null=True, blank=True)
    last_test_success = models.BooleanField(null=True, blank=True)
    last_test_message = models.TextField(blank=True, default="")
    available_models = models.TextField(blank=True, default="[]", help_text="JSON list of available models")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_primary', '-priority', 'name']
        verbose_name = "AI Provider"
        verbose_name_plural = "AI Providers"
    
    def __str__(self):
        status = "✓" if self.last_test_success else "✗" if self.last_test_success is False else "?"
        primary = " (Primary)" if self.is_primary else ""
        return f"{status} {self.name} ({self.get_provider_type_display()}){primary}"
    
    def save(self, *args, **kwargs):
        # If this is set as primary, unset all others
        if self.is_primary:
            AIProvider.objects.exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
    
    def test_connection(self):
        """Test the connection to this AI provider"""
        from django.utils import timezone
        
        self.last_tested = timezone.now()
        
        try:
            if self.provider_type == 'ollama':
                return self._test_ollama()
            elif self.provider_type == 'openai':
                return self._test_openai()
            else:
                self.last_test_success = False
                self.last_test_message = f"Unknown provider type: {self.provider_type}"
                self.save()
                return False, self.last_test_message
        except Exception as e:
            self.last_test_success = False
            self.last_test_message = f"Connection error: {str(e)}"
            self.save()
            return False, self.last_test_message
    
    def _test_ollama(self):
        """Test connection to Ollama server"""
        try:
            # Test basic connectivity
            response = requests.get(f"{self.api_url}/api/tags", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                model_names = [m.get("name", "unknown") for m in models]
                
                self.available_models = json.dumps(model_names)
                self.last_test_success = True
                self.last_test_message = f"Connected! {len(models)} models available: {', '.join(model_names[:5])}"
                if len(model_names) > 5:
                    self.last_test_message += f" (+{len(model_names) - 5} more)"
                self.save()
                return True, self.last_test_message
            else:
                self.last_test_success = False
                self.last_test_message = f"Server responded with status {response.status_code}"
                self.save()
                return False, self.last_test_message
                
        except requests.exceptions.Timeout:
            self.last_test_success = False
            self.last_test_message = "Connection timeout - server unreachable"
            self.save()
            return False, self.last_test_message
        except requests.exceptions.ConnectionError:
            self.last_test_success = False
            self.last_test_message = "Connection refused - server offline or wrong address"
            self.save()
            return False, self.last_test_message
    
    def _test_openai(self):
        """Test connection to OpenAI API"""
        if not self.api_key:
            self.last_test_success = False
            self.last_test_message = "API key is required for OpenAI"
            self.save()
            return False, self.last_test_message
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Test with models endpoint
            response = requests.get(
                f"{self.api_url}/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                # Filter to just chat models
                chat_models = [m["id"] for m in models if "gpt" in m["id"].lower()][:10]
                
                self.available_models = json.dumps(chat_models)
                self.last_test_success = True
                self.last_test_message = f"Connected! {len(chat_models)} chat models available"
                self.save()
                return True, self.last_test_message
            elif response.status_code == 401:
                self.last_test_success = False
                self.last_test_message = "Invalid API key"
                self.save()
                return False, self.last_test_message
            else:
                self.last_test_success = False
                self.last_test_message = f"API responded with status {response.status_code}"
                self.save()
                return False, self.last_test_message
                
        except requests.exceptions.Timeout:
            self.last_test_success = False
            self.last_test_message = "Connection timeout"
            self.save()
            return False, self.last_test_message
        except requests.exceptions.ConnectionError:
            self.last_test_success = False
            self.last_test_message = "Connection failed"
            self.save()
            return False, self.last_test_message
    
    def get_available_models_list(self):
        """Return available models as a Python list"""
        try:
            return json.loads(self.available_models)
        except:
            return []
    
    def generate_text(self, prompt, model=None, stream=False):
        """Generate text using this provider"""
        model = model or self.default_model
        
        if self.provider_type == 'ollama':
            return self._generate_ollama(prompt, model, stream)
        elif self.provider_type == 'openai':
            return self._generate_openai(prompt, model, stream)
        else:
            raise ValueError(f"Unknown provider type: {self.provider_type}")
    
    def _generate_ollama(self, prompt, model, stream):
        """Generate text with Ollama"""
        response = requests.post(
            f"{self.api_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 500
                }
            },
            timeout=120,
            stream=stream
        )
        
        if stream:
            return response  # Return the response object for streaming
        else:
            response.raise_for_status()
            return response.json().get("response", "")
    
    def _generate_openai(self, prompt, model, stream):
        """Generate text with OpenAI"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.api_url}/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": stream,
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=120,
            stream=stream
        )
        
        if stream:
            return response
        else:
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]


class Book(models.Model):
    """Model to represent a published book"""
    title = models.CharField(max_length=255, default="Untitled")
    author = models.CharField(max_length=255, default="Unknown Author")
    slug = models.SlugField(unique=True, default="untitled")
    
    # File paths - these should be set dynamically per book
    manuscript_path = models.CharField(max_length=512, default="")
    annotations_path = models.CharField(max_length=512, default="")
    cover_path = models.CharField(max_length=512, null=True, blank=True)
    
    # Annotation planning - user instructions and approach
    THEME_CHOICES = [
        ('bobs_somewhat_humanist', "Bob's Somewhat Humanist"),
        ('scientific_review', 'Scientific Review'),
        ('cyberpunk_neon', 'Cyberpunk Neon'),
        ('textbook_classic', 'Textbook Classic'),
    ]
    annotation_theme = models.CharField(
        max_length=50,
        choices=THEME_CHOICES,
        default='bobs_somewhat_humanist',
        help_text="Visual theme and annotator persona for this book's annotations"
    )
    custom_annotator_name = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Override the theme's default annotator name"
    )
    custom_icon_letter = models.CharField(
        max_length=5,
        blank=True,
        default="",
        help_text="Override the annotator icon letter (1-2 chars)"
    )
    custom_primary_color = models.CharField(
        max_length=7,
        blank=True,
        default="",
        help_text="Override primary color (hex, e.g. #B87333)"
    )
    custom_background_color = models.CharField(
        max_length=7,
        blank=True,
        default="",
        help_text="Override background color (hex, e.g. #F5F5DC)"
    )
    annotation_instructions = models.TextField(
        blank=True, 
        default="",
        help_text="Custom instructions for the annotator when annotating this book"
    )
    annotation_approach = models.TextField(
        blank=True, 
        default="",
        help_text="AI-generated annotation approach/plan for this book"
    )
    preferred_model = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Preferred AI model for annotating this book (e.g., qwen2.5:7b)"
    )
    annotation_conversation = models.TextField(
        blank=True,
        default="[]",
        help_text="JSON array of conversation history about annotation planning"
    )
    planning_completed = models.BooleanField(
        default=False,
        help_text="Whether annotation planning has been completed"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} by {self.author}"
    
    def get_conversation_history(self):
        """Return conversation history as a Python list"""
        try:
            return json.loads(self.annotation_conversation)
        except:
            return []
    
    def add_to_conversation(self, role, content):
        """Add a message to the conversation history"""
        history = self.get_conversation_history()
        history.append({
            "role": role,
            "content": content,
            "timestamp": timezone.now().isoformat()
        })
        self.annotation_conversation = json.dumps(history)
        self.save()


class EPUBBuild(models.Model):
    """Track EPUB builds and their status"""
    BUILD_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ingesting', 'Ingesting Text'),
        ('annotating', 'Generating Annotations'),
        ('analyzing', 'Comprehensive Analysis'),
        ('building', 'Building EPUB'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='builds')
    status = models.CharField(max_length=20, choices=BUILD_STATUS_CHOICES, default='pending')
    
    # Build details
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    output_path = models.CharField(max_length=512, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    # Stage tracking
    current_stage = models.CharField(max_length=50, default='pending')
    stage_log = models.TextField(default='[]')  # JSON array of stage updates
    
    # Metadata
    file_size = models.BigIntegerField(null=True, blank=True)  # in bytes
    chapter_count = models.IntegerField(null=True, blank=True)
    section_count = models.IntegerField(null=True, blank=True)
    annotation_count = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.book.title} - {self.status} ({self.created_at})"
    
    def file_size_mb(self):
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return None
    
    def is_downloadable(self):
        return self.status == 'success' and os.path.exists(self.output_path)


class TTSProvider(models.Model):
    """Text-to-Speech provider configuration (PersonaPlex, NVIDIA Riva, etc.)"""
    PROVIDER_TYPES = [
        ('personaplex', 'NVIDIA PersonaPlex-7B (HuggingFace)'),
        ('riva', 'NVIDIA Riva'),
        ('edge-tts', 'Microsoft Edge TTS (Neural, Online)'),
        ('xtts', 'Coqui XTTS v2 (Local, Expressive)'),
        ('pyttsx3', 'pyttsx3/macOS (Local)'),
        ('piper', 'Piper TTS (Offline, Fast)'),
        ('gtts', 'Google TTS (Online)'),
        ('azure', 'Azure Speech'),
    ]
    
    name = models.CharField(max_length=100, help_text="Friendly name")
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPES, default='personaplex')
    
    # Connection settings
    server_url = models.CharField(
        max_length=255,
        default="wss://localhost:8443",
        help_text="Server address (wss://localhost:8443 for PersonaPlex, localhost:50051 for Riva)"
    )
    api_key = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="HuggingFace token for PersonaPlex, or API key for other providers"
    )
    
    # PersonaPlex-specific settings
    cpu_offload = models.BooleanField(
        default=False,
        help_text="Use CPU offload for PersonaPlex (if GPU VRAM is insufficient)"
    )
    
    # Audio settings
    sample_rate = models.IntegerField(default=24000, help_text="Audio sample rate in Hz (24000 for PersonaPlex)")
    output_format = models.CharField(max_length=10, default='wav', help_text="Output format (wav, mp3)")
    
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    
    last_tested = models.DateTimeField(null=True, blank=True)
    last_test_success = models.BooleanField(null=True, blank=True)
    last_test_message = models.TextField(blank=True, default="")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_primary', 'name']
        verbose_name = "TTS Provider"
        verbose_name_plural = "TTS Providers"
    
    def __str__(self):
        status = "✓" if self.last_test_success else "✗" if self.last_test_success is False else "?"
        primary = " (Primary)" if self.is_primary else ""
        return f"{status} {self.name} ({self.get_provider_type_display()}){primary}"
    
    def save(self, *args, **kwargs):
        if self.is_primary:
            TTSProvider.objects.exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class VoiceProfile(models.Model):
    """Voice profile for TTS - supports multiple providers with provider-specific options"""
    VOICE_ROLES = [
        ('narrator', 'Narrator'),
        ('annotator', 'Annotator'),
        ('character', 'Character'),
    ]
    
    # Provider this voice is configured for
    provider = models.ForeignKey(
        'TTSProvider', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='voices',
        help_text="TTS provider this voice is configured for"
    )
    
    name = models.CharField(max_length=100, help_text="Voice name")
    voice_id = models.CharField(
        max_length=200, 
        help_text="Voice ID from TTS provider (e.g., en-US-AvaNeural for Edge TTS)",
        blank=True
    )
    role = models.CharField(max_length=20, choices=VOICE_ROLES, default='character')
    
    # Voice characteristics
    pitch = models.FloatField(default=1.0, help_text="Pitch multiplier (0.5-2.0)")
    speed = models.FloatField(default=1.0, help_text="Speed multiplier (0.5-2.0)")
    tone = models.CharField(max_length=50, default="neutral", help_text="Tone (neutral, dramatic, gentle, stern)")
    
    description = models.TextField(blank=True, help_text="Voice description")
    
    # PersonaPlex-specific: Voice prompt for cloning
    voice_prompt_path = models.CharField(
        max_length=512, 
        blank=True, 
        null=True,
        help_text="Path to 5-10 second audio file for PersonaPlex voice cloning"
    )
    persona_text = models.TextField(
        blank=True,
        default="",
        help_text="PersonaPlex persona description (e.g., 'You are a dramatic narrator with a deep voice')"
    )
    
    # Sample audio for preview
    sample_audio_path = models.CharField(max_length=512, blank=True, null=True)
    sample_text = models.TextField(
        blank=True,
        default="Hello, I am a voice for the publisher. This is a preview of how I sound."
    )
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['role', 'name']
        verbose_name = "Voice Profile"
        verbose_name_plural = "Voice Profiles"
    
    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"
    
    def to_voice_config(self):
        """Convert to VoiceConfig for audio generator"""
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


class CharacterVoiceMapping(models.Model):
    """Map characters to voice profiles for a specific book"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='character_voices')
    character_name = models.CharField(max_length=100, help_text="Character name (e.g., 'Gregor', 'Grete')")
    voice = models.ForeignKey(VoiceProfile, on_delete=models.CASCADE, related_name='character_mappings')
    
    # Detection patterns
    speech_patterns = models.TextField(
        blank=True,
        help_text="JSON list of regex patterns to detect this character's speech"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['book', 'character_name']
        ordering = ['book', 'character_name']
        verbose_name = "Character Voice Mapping"
        verbose_name_plural = "Character Voice Mappings"
    
    def __str__(self):
        return f"{self.character_name} → {self.voice.name} ({self.book.title})"
    
    def get_patterns_list(self):
        try:
            return json.loads(self.speech_patterns) if self.speech_patterns else []
        except:
            return []


class AudioBuild(models.Model):
    """Track audio generation builds"""
    BUILD_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('generating', 'Generating Audio'),
        ('combining', 'Combining Tracks'),
        ('encoding', 'Encoding MP3'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='audio_builds')
    tts_provider = models.ForeignKey(TTSProvider, on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=BUILD_STATUS_CHOICES, default='pending')
    
    # Build settings
    include_annotations = models.BooleanField(default=True, help_text="Include annotations in audio")
    narrator_voice = models.ForeignKey(
        VoiceProfile, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='narrator_builds'
    )
    annotator_voice = models.ForeignKey(
        VoiceProfile, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='annotator_builds'
    )
    
    # Voice style customization
    style_prompt = models.TextField(
        blank=True, default="",
        help_text="Style instructions for voice (e.g., 'Read in a humorous, laid-back tone with a southern accent')"
    )
    
    # Bumper/outro audio
    bumper_audio_path = models.CharField(
        max_length=512, blank=True, null=True,
        help_text="Path to intro bumper audio file"
    )
    outro_audio_path = models.CharField(
        max_length=512, blank=True, null=True,
        help_text="Path to outro audio file"
    )
    
    # Legal disclaimer
    legal_disclaimer_text = models.TextField(
        blank=True, default="",
        help_text="Legal disclaimer text to be read at the beginning"
    )
    include_legal_disclaimer = models.BooleanField(default=False)
    
    # Narration range (which section to start from)
    start_section = models.IntegerField(
        default=1, help_text="Section number to start narration from (1-based)"
    )
    end_section = models.IntegerField(
        null=True, blank=True,
        help_text="Section number to end narration at (leave blank for all)"
    )
    
    # Progress
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    current_section = models.IntegerField(default=0)
    total_sections = models.IntegerField(default=0)
    
    # Output
    output_path = models.CharField(max_length=512, null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    error_message = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Audio Build"
        verbose_name_plural = "Audio Builds"
    
    def __str__(self):
        return f"{self.book.title} - Audio ({self.status})"
    
    def progress_percent(self):
        if self.total_sections and self.total_sections > 0:
            return int((self.current_section / self.total_sections) * 100)
        return 0
    
    def duration_formatted(self):
        if self.duration_seconds:
            hours = self.duration_seconds // 3600
            minutes = (self.duration_seconds % 3600) // 60
            seconds = self.duration_seconds % 60
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return None
    
    def file_size_mb(self):
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return None


class AudioAsset(models.Model):
    """Reusable audio assets (bumpers, outros, sound effects, legal disclaimers)"""
    ASSET_TYPES = [
        ('bumper', 'Intro Bumper'),
        ('outro', 'Outro'),
        ('legal', 'Legal Disclaimer'),
        ('transition', 'Transition Sound'),
        ('effect', 'Sound Effect'),
    ]
    
    name = models.CharField(max_length=100, help_text="Asset name")
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES, default='bumper')
    description = models.TextField(blank=True)
    
    # File storage
    audio_file = models.FileField(
        upload_to='audio_assets/', 
        null=True, blank=True,
        help_text="Upload WAV or MP3 file"
    )
    file_path = models.CharField(
        max_length=512, blank=True, null=True,
        help_text="Alternative: path to existing audio file"
    )
    
    # If generated from text
    source_text = models.TextField(
        blank=True, default="",
        help_text="Original text (if generated from TTS)"
    )
    
    # Metadata
    duration_seconds = models.FloatField(null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    sample_rate = models.IntegerField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['asset_type', 'name']
        verbose_name = "Audio Asset"
        verbose_name_plural = "Audio Assets"
    
    def __str__(self):
        return f"{self.name} ({self.get_asset_type_display()})"
    
    def get_audio_path(self):
        """Return the actual path to the audio file"""
        if self.audio_file:
            return self.audio_file.path
        return self.file_path
    
    def file_size_kb(self):
        if self.file_size:
            return round(self.file_size / 1024, 1)
        return None
