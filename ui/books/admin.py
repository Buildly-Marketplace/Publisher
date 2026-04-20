from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import Book, EPUBBuild, AIProvider, TTSProvider, VoiceProfile, CharacterVoiceMapping, AudioBuild
import json


@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider_type', 'api_url', 'default_model', 'status_badge', 'is_active', 'is_primary', 'priority']
    list_filter = ['provider_type', 'is_active', 'is_primary', 'last_test_success']
    list_editable = ['is_active', 'is_primary', 'priority']
    search_fields = ['name', 'api_url']
    ordering = ['-is_primary', '-priority', 'name']
    
    fieldsets = (
        ('Provider Settings', {
            'fields': ('name', 'provider_type', 'is_active', 'is_primary', 'priority')
        }),
        ('Connection', {
            'fields': ('api_url', 'api_key', 'default_model'),
            'description': 'Configure the connection to your AI provider'
        }),
        ('Status', {
            'fields': ('last_tested', 'last_test_success', 'last_test_message', 'available_models'),
            'classes': ('collapse',),
            'description': 'Connection test results (read-only)'
        }),
    )
    
    readonly_fields = ['last_tested', 'last_test_success', 'last_test_message', 'available_models']
    
    actions = ['test_selected_connections', 'set_as_primary']
    
    def status_badge(self, obj):
        if obj.last_test_success is None:
            return format_html('<span style="color: gray; font-size: 1.2em;">⚪</span> Not tested')
        elif obj.last_test_success:
            return format_html('<span style="color: green; font-size: 1.2em;">🟢</span> Connected')
        else:
            return format_html('<span style="color: red; font-size: 1.2em;">🔴</span> Failed')
    status_badge.short_description = 'Status'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/test/', self.admin_site.admin_view(self.test_connection_view), name='books_aiprovider_test'),
            path('test-all/', self.admin_site.admin_view(self.test_all_connections_view), name='books_aiprovider_test_all'),
            path('<int:pk>/quick-test/', self.admin_site.admin_view(self.quick_test_view), name='books_aiprovider_quick_test'),
        ]
        return custom_urls + urls
    
    def test_connection_view(self, request, pk):
        """View to test a single provider connection"""
        provider = AIProvider.objects.get(pk=pk)
        success, message = provider.test_connection()
        
        if success:
            messages.success(request, f"✓ {provider.name}: {message}")
        else:
            messages.error(request, f"✗ {provider.name}: {message}")
        
        return redirect(reverse('admin:books_aiprovider_changelist'))
    
    def test_all_connections_view(self, request):
        """View to test all provider connections"""
        providers = AIProvider.objects.filter(is_active=True)
        results = []
        
        for provider in providers:
            success, message = provider.test_connection()
            results.append({
                'name': provider.name,
                'success': success,
                'message': message
            })
            
            if success:
                messages.success(request, f"✓ {provider.name}: {message}")
            else:
                messages.warning(request, f"✗ {provider.name}: {message}")
        
        return redirect(reverse('admin:books_aiprovider_changelist'))
    
    def quick_test_view(self, request, pk):
        """AJAX endpoint for quick connection test"""
        provider = AIProvider.objects.get(pk=pk)
        success, message = provider.test_connection()
        
        return JsonResponse({
            'success': success,
            'message': message,
            'models': provider.get_available_models_list()
        })
    
    @admin.action(description="Test connection for selected providers")
    def test_selected_connections(self, request, queryset):
        for provider in queryset:
            success, message = provider.test_connection()
            if success:
                messages.success(request, f"✓ {provider.name}: {message}")
            else:
                messages.error(request, f"✗ {provider.name}: {message}")
    
    @admin.action(description="Set as primary provider")
    def set_as_primary(self, request, queryset):
        if queryset.count() > 1:
            messages.error(request, "Please select only one provider to set as primary")
            return
        
        provider = queryset.first()
        AIProvider.objects.all().update(is_primary=False)
        provider.is_primary = True
        provider.save()
        messages.success(request, f"{provider.name} is now the primary AI provider")
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_test_button'] = True
        return super().change_view(request, object_id, form_url, extra_context=extra_context)
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_test_all_button'] = True
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'slug', 'created_at']
    list_filter = ['author', 'created_at']
    search_fields = ['title', 'author']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(EPUBBuild)
class EPUBBuildAdmin(admin.ModelAdmin):
    list_display = ['book', 'status', 'current_stage', 'started_at', 'completed_at']
    list_filter = ['status', 'current_stage']
    search_fields = ['book__title']
    readonly_fields = ['started_at', 'completed_at', 'stage_log']


@admin.register(TTSProvider)
class TTSProviderAdmin(admin.ModelAdmin):
    """Admin for TTS provider configuration."""
    list_display = ['name', 'provider_type', 'status_badge', 'is_primary', 'created_at']
    list_filter = ['provider_type', 'is_active', 'is_primary']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at', 'last_tested', 'last_test_success', 'last_test_message']
    actions = ['test_tts_connections', 'set_as_primary', 'show_setup_instructions']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'provider_type', 'is_active', 'is_primary')
        }),
        ('Connection', {
            'fields': ('server_url', 'api_key'),
            'description': 'For PersonaPlex: wss://localhost:8443, API key = HF token. For Riva: localhost:50051'
        }),
        ('PersonaPlex Settings', {
            'fields': ('cpu_offload',),
            'classes': ('collapse',),
            'description': 'Enable CPU offload if GPU VRAM is insufficient for PersonaPlex'
        }),
        ('Audio Settings', {
            'fields': ('sample_rate', 'output_format'),
            'description': 'PersonaPlex uses 24000 Hz sample rate'
        }),
        ('Test Results', {
            'fields': ('last_tested', 'last_test_success', 'last_test_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        if obj.is_active:
            color = 'green'
            text = 'Active'
        else:
            color = 'red'
            text = 'Inactive'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, text
        )
    status_badge.short_description = 'Status'
    
    @admin.action(description="Test TTS connection")
    def test_tts_connections(self, request, queryset):
        for provider in queryset:
            if provider.provider_type == 'personaplex':
                try:
                    import websockets
                    messages.info(request, f"⚠ {provider.name}: WebSocket test - ensure moshi server is running at {provider.server_url}")
                except ImportError:
                    messages.error(request, f"✗ {provider.name}: Install websockets: pip install websockets")
            elif provider.provider_type == 'riva':
                try:
                    import riva.client
                    auth = riva.client.Auth(uri=provider.server_url)
                    messages.success(request, f"✓ {provider.name}: Connection successful")
                except Exception as e:
                    messages.error(request, f"✗ {provider.name}: {str(e)}")
            elif provider.provider_type == 'pyttsx3':
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
                    messages.success(request, f"✓ {provider.name}: pyttsx3 engine ready")
                except Exception as e:
                    messages.error(request, f"✗ {provider.name}: {str(e)}")
            elif provider.provider_type == 'gtts':
                messages.info(request, f"✓ {provider.name}: gTTS ready (requires internet)")
            else:
                messages.info(request, f"⚠ {provider.name}: Test not implemented for {provider.provider_type}")
    
    @admin.action(description="Set as primary provider")
    def set_as_primary(self, request, queryset):
        if queryset.count() != 1:
            messages.error(request, "Please select exactly one provider to set as primary")
            return
        TTSProvider.objects.update(is_primary=False)
        queryset.update(is_primary=True)
        messages.success(request, f"Set {queryset.first().name} as primary TTS provider")
    
    @admin.action(description="Show setup instructions")
    def show_setup_instructions(self, request, queryset):
        for provider in queryset:
            if provider.provider_type == 'personaplex':
                messages.info(request, format_html(
                    '<strong>PersonaPlex Setup:</strong><br>'
                    '1. Accept license at huggingface.co/nvidia/personaplex-7b-v1<br>'
                    '2. Set HF_TOKEN environment variable<br>'
                    '3. git clone https://github.com/NVIDIA/personaplex<br>'
                    '4. SSL_DIR=$(mktemp -d); python -m moshi.server --ssl "$SSL_DIR"<br>'
                    '5. For CPU offload: add --cpu-offload flag'
                ))


@admin.register(VoiceProfile)
class VoiceProfileAdmin(admin.ModelAdmin):
    """Admin for voice profiles."""
    list_display = ['name', 'role', 'voice_id', 'speed', 'pitch', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['name', 'voice_id', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'voice_id', 'role', 'is_active')
        }),
        ('Voice Settings', {
            'fields': ('pitch', 'speed', 'tone', 'description')
        }),
        ('PersonaPlex Voice Cloning', {
            'fields': ('voice_prompt_path', 'persona_text'),
            'classes': ('collapse',),
            'description': 'For PersonaPlex: provide a 5-10 second audio sample and persona description'
        }),
        ('Preview', {
            'fields': ('sample_text', 'sample_audio_path'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CharacterVoiceMapping)
class CharacterVoiceMappingAdmin(admin.ModelAdmin):
    """Admin for character-to-voice mappings."""
    list_display = ['book', 'character_name', 'voice']
    list_filter = ['book']
    search_fields = ['character_name', 'book__title']
    
    fieldsets = (
        (None, {
            'fields': ('book', 'character_name', 'voice')
        }),
        ('Detection', {
            'fields': ('speech_patterns',),
            'classes': ('collapse',),
            'description': 'JSON list of regex patterns to detect this character\'s speech'
        }),
    )


@admin.register(AudioBuild)
class AudioBuildAdmin(admin.ModelAdmin):
    """Admin for audio builds."""
    list_display = ['book', 'status_badge', 'progress_display', 'started_at', 'completed_at']
    list_filter = ['status']
    search_fields = ['book__title']
    readonly_fields = ['started_at', 'completed_at', 'duration_seconds', 'file_size', 'error_message', 'created_at']
    
    fieldsets = (
        (None, {
            'fields': ('book', 'status', 'tts_provider')
        }),
        ('Voices', {
            'fields': ('narrator_voice', 'annotator_voice', 'include_annotations')
        }),
        ('Progress', {
            'fields': ('total_sections', 'current_section')
        }),
        ('Output', {
            'fields': ('output_path', 'duration_seconds', 'file_size')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at', 'created_at'),
            'classes': ('collapse',)
        }),
        ('Errors', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': 'gray',
            'generating': 'blue',
            'combining': 'blue',
            'encoding': 'blue',
            'success': 'green',
            'failed': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.status.replace('_', ' ').title()
        )
    status_badge.short_description = 'Status'
    
    def progress_display(self, obj):
        return f"{obj.current_section}/{obj.total_sections} ({obj.progress_percent()}%)"
    progress_display.short_description = 'Progress'

