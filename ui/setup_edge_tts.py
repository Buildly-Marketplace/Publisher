#!/usr/bin/env python
"""Setup Edge TTS provider and voice profiles"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'publisher_django.settings')

import django
django.setup()

from books.models import TTSProvider, VoiceProfile

print("Setting up Edge TTS...")
print()

# Create Edge TTS provider and set as primary
TTSProvider.objects.update(is_primary=False)

edge_provider, created = TTSProvider.objects.update_or_create(
    provider_type='edge-tts',
    defaults={
        'name': 'Edge TTS (Microsoft Neural)',
        'is_active': True,
        'is_primary': True,
        'server_url': '',
        'sample_rate': 24000,
    }
)
print(f"Edge TTS provider: {'CREATED' if created else 'updated'}")

# Create high-quality Edge TTS voice profiles
voices = [
    ('Guy (Neural)', 'en-US-GuyNeural', 'narrator', 'Warm, charismatic male - excellent for narration'),
    ('Andrew (Neural)', 'en-US-AndrewNeural', 'annotator', 'Warm, authentic - perfect for annotations'),
    ('Aria (Neural)', 'en-US-AriaNeural', 'narrator', 'Positive, confident female narrator'),
    ('Christopher (Neural)', 'en-US-ChristopherNeural', 'narrator', 'Reliable, authoritative male'),
    ('Jenny (Neural)', 'en-US-JennyNeural', 'character', 'Friendly female voice'),
]

print()
print("Voice profiles:")
for name, voice_id, role, desc in voices:
    v, created = VoiceProfile.objects.update_or_create(
        voice_id=voice_id,
        defaults={
            'name': name,
            'role': role,
            'pitch': 1.0,
            'speed': 1.0 if role != 'narrator' else 0.95,
            'tone': 'friendly' if role == 'annotator' else 'dramatic',
            'description': desc,
        }
    )
    status = "CREATED" if created else "exists"
    print(f"  {status}: {name} ({voice_id})")

print()
print("=" * 50)
print("DONE!")
print()
print(f"Primary TTS provider: {TTSProvider.objects.get(is_primary=True)}")
print()
print("Available voices:")
for v in VoiceProfile.objects.all():
    print(f"  - {v.name}: {v.voice_id or '(no voice_id)'}")
