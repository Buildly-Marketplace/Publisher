"""
URL configuration for publisher_django project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path

from books.views import (
    book_list, manuscript_detail, annotation_list, annotation_edit, 
    book_data_list, book_data_editor,
    book_dashboard, build_epub, build_detail, download_epub, build_status_api, tail_log,
    # AI Configuration views
    ai_config, ai_status_api, ai_add_provider, ai_edit_provider, 
    ai_delete_provider, ai_test_provider, ai_test_all, ai_set_primary,
    ai_discover_models,
    # Annotation Planning views
    annotation_planning, annotation_generate_approach, annotation_chat,
    annotation_preview_sample, annotation_save_instructions, annotation_clear_conversation,
    # Audiobook views
    audiobook_config, audiobook_save_voices, audiobook_build, 
    audiobook_build_status, audiobook_status_api, download_audiobook,
    voice_profile_create, voice_preview, edge_tts_voices, create_default_edge_tts_voices,
    tts_config, tts_add_provider, tts_set_primary, tts_test_provider, tts_edit_provider, tts_delete_provider, tts_get_voices,
    # Book section preview
    book_sections, book_section_content,
    # Audio Asset views
    audio_assets, audio_asset_create, audio_asset_delete, audio_asset_download,
    generate_audio_file,
)
try:
    from books.book_views import book_create, book_edit, book_preview
except ImportError:
    # Fallback if book_views doesn't exist
    book_create = book_edit = book_preview = None

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", book_list, name="book_list"),
    path("manuscript/<str:filename>", manuscript_detail, name="manuscript_detail"),
    path("annotations/", annotation_list, name="annotation_list"),
    path("annotations/<str:filename>", annotation_edit, name="annotation_edit"),
    path("books-data/", book_data_list, name="book_data_list"),
    path("books-data/<str:book_folder>", book_data_editor, name="book_data_editor"),
    
    # EPUB building endpoints
    path("dashboard/", book_dashboard, name="book_dashboard"),
    path("dashboard/", book_dashboard, name="dashboard"),  # Alias for dashboard
    path("book/create/", book_create, name="book_create"),
    path("book/<int:book_id>/edit/", book_edit, name="book_edit"),
    path("book/<int:book_id>/preview/", book_preview, name="book_preview"),
    path("build/<int:book_id>/", build_epub, name="build_epub"),
    path("build-detail/<int:build_id>/", build_detail, name="build_detail"),
    path("download/<int:build_id>/", download_epub, name="download_epub"),
    path("api/build/<int:build_id>/", build_status_api, name="build_status_api"),
    path("api/log/pipeline/", tail_log, name="tail_log"),
    
    # AI Configuration endpoints
    path("ai/", ai_config, name="ai_config"),
    path("api/ai/status/", ai_status_api, name="ai_status_api"),
    path("ai/add/", ai_add_provider, name="ai_add_provider"),
    path("ai/<int:provider_id>/edit/", ai_edit_provider, name="ai_edit_provider"),
    path("ai/<int:provider_id>/delete/", ai_delete_provider, name="ai_delete_provider"),
    path("ai/<int:provider_id>/test/", ai_test_provider, name="ai_test_provider"),
    path("ai/test-all/", ai_test_all, name="ai_test_all"),
    path("ai/<int:provider_id>/set-primary/", ai_set_primary, name="ai_set_primary"),
    path("api/ai/discover-models/", ai_discover_models, name="ai_discover_models"),
    
    # Annotation Planning endpoints
    path("book/<int:book_id>/annotation/", annotation_planning, name="annotation_planning"),
    path("book/<int:book_id>/annotation/generate-approach/", annotation_generate_approach, name="annotation_generate_approach"),
    path("book/<int:book_id>/annotation/chat/", annotation_chat, name="annotation_chat"),
    path("book/<int:book_id>/annotation/preview-sample/", annotation_preview_sample, name="annotation_preview_sample"),
    path("book/<int:book_id>/annotation/save-instructions/", annotation_save_instructions, name="annotation_save_instructions"),
    path("book/<int:book_id>/annotation/clear-conversation/", annotation_clear_conversation, name="annotation_clear_conversation"),
    
    # Audiobook endpoints
    path("audiobook/<int:book_id>/", audiobook_config, name="audiobook_config"),
    path("audiobook/<int:book_id>/save-voices/", audiobook_save_voices, name="audiobook_save_voices"),
    path("audiobook/<int:book_id>/build/", audiobook_build, name="audiobook_build"),
    path("audiobook/build/<int:build_id>/", audiobook_build_status, name="audiobook_build_status"),
    path("api/audiobook/<int:build_id>/", audiobook_status_api, name="audiobook_status_api"),
    
    # TTS Configuration endpoints
    path("tts/", tts_config, name="tts_config"),
    path("tts/add/", tts_add_provider, name="tts_add_provider"),
    path("tts/<int:provider_id>/set-primary/", tts_set_primary, name="tts_set_primary"),
    path("tts/<int:provider_id>/test/", tts_test_provider, name="tts_test_provider"),
    path("tts/<int:provider_id>/edit/", tts_edit_provider, name="tts_edit_provider"),
    path("tts/<int:provider_id>/delete/", tts_delete_provider, name="tts_delete_provider"),
    path("api/tts/<int:provider_id>/voices/", tts_get_voices, name="tts_get_voices"),
    path("voice/create/", voice_profile_create, name="voice_profile_create"),
    path("voice/preview/", voice_preview, name="voice_preview"),
    path("voice/edge-tts-voices/", edge_tts_voices, name="edge_tts_voices"),
    path("voice/create-edge-tts-defaults/", create_default_edge_tts_voices, name="create_default_edge_tts_voices"),
    
    # Book section preview for audiobook
    path("api/book/<int:book_id>/sections/", book_sections, name="book_sections"),
    path("api/book/<int:book_id>/section/<int:section_index>/", book_section_content, name="book_section_content"),
    
    # Audiobook download
    path("audiobook/download/<int:build_id>/", download_audiobook, name="download_audiobook"),
    
    # Audio Asset endpoints
    path("audio-assets/", audio_assets, name="audio_assets"),
    path("audio-asset/create/", audio_asset_create, name="audio_asset_create"),
    path("audio-asset/<int:asset_id>/delete/", audio_asset_delete, name="audio_asset_delete"),
    path("audio-asset/<int:asset_id>/download/", audio_asset_download, name="audio_asset_download"),
    path("audio/generate/", generate_audio_file, name="generate_audio_file"),
]
