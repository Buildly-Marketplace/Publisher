from django.views.decorators.csrf import csrf_exempt
def tail_log(request):
	"""API endpoint to tail the pipeline log (last N lines)"""
	log_path = os.path.abspath(os.path.join(settings.BASE_DIR, '..', 'ops', 'pipeline.log'))
	num_lines = int(request.GET.get('lines', 40))
	log_content = []
	try:
		with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
			log_content = f.readlines()[-num_lines:]
	except Exception as e:
		log_content = [f"Error reading log: {e}\n"]
	return JsonResponse({"log": ''.join(log_content)})
import os
import sys
import json
import subprocess
from datetime import datetime
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse, JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Book, EPUBBuild

PIPELINE_DIR = os.path.join(settings.BASE_DIR, '..', 'pipeline')
BOOKS_DATA_DIR = os.path.join(settings.BASE_DIR, '..', 'books_data')

def book_data_list(request):
	try:
		books = [d for d in os.listdir(BOOKS_DATA_DIR) if os.path.isdir(os.path.join(BOOKS_DATA_DIR, d))]
	except FileNotFoundError:
		books = []
	return render(request, "books/book_data_list.html", {"books": books})

def book_data_editor(request, book_folder):
	import datetime
	book_path = os.path.join(BOOKS_DATA_DIR, book_folder)
	manuscript_path = os.path.join(book_path, "manuscript.txt")
	annotation_path = os.path.join(book_path, "annotations.json")
	cover_path = None
	cover_is_image = False

	for ext in ["jpg", "jpeg", "png", "gif"]:
		candidate = os.path.join(book_path, f"cover.{ext}")
		if os.path.exists(candidate):
			cover_path = candidate
			cover_is_image = True
			break
	if not cover_path:
		cover_path = os.path.join(book_path, "cover.txt") if os.path.exists(os.path.join(book_path, "cover.txt")) else None

	versions_dir = os.path.join(book_path, "versions")
	os.makedirs(versions_dir, exist_ok=True)
	# List available versions
	version_files = sorted(os.listdir(versions_dir)) if os.path.exists(versions_dir) else []
	version_choices = [(f, f) for f in version_files if f.startswith("manuscript_") or f.startswith("annotations_")]

	saved = False
	error = None
	# Restore version if requested
	restore_file = request.GET.get("restore")
	if restore_file:
		restore_path = os.path.join(versions_dir, restore_file)
		if restore_file.startswith("manuscript_") and os.path.exists(restore_path):
			with open(restore_path, "r", encoding="utf-8") as f:
				data = f.read()
			with open(manuscript_path, "w", encoding="utf-8") as f:
				f.write(data)
			saved = True
		elif restore_file.startswith("annotations_") and os.path.exists(restore_path):
			with open(restore_path, "r", encoding="utf-8") as f:
				data = f.read()
			with open(annotation_path, "w", encoding="utf-8") as f:
				f.write(data)
			saved = True

	if request.method == "POST":
		# Versioning: save previous versions
		timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
		# Save previous manuscript
		if os.path.exists(manuscript_path):
			with open(manuscript_path, "r", encoding="utf-8") as f:
				prev = f.read()
			with open(os.path.join(versions_dir, f"manuscript_{timestamp}.txt"), "w", encoding="utf-8") as f:
				f.write(prev)
		# Save previous annotation
		if os.path.exists(annotation_path):
			with open(annotation_path, "r", encoding="utf-8") as f:
				prev = f.read()
			with open(os.path.join(versions_dir, f"annotations_{timestamp}.json"), "w", encoding="utf-8") as f:
				f.write(prev)
		# Save new manuscript
		try:
			with open(manuscript_path, "w", encoding="utf-8") as f:
				f.write(request.POST.get("manuscript", ""))
			with open(annotation_path, "w", encoding="utf-8") as f:
				f.write(request.POST.get("annotation", ""))
			saved = True
		except Exception as e:
			error = str(e)

	# Load manuscript
	try:
		with open(manuscript_path, "r", encoding="utf-8") as f:
			manuscript = f.read()
	except Exception as e:
		manuscript = f"Error reading manuscript: {e}"

	# Load annotation
	try:
		with open(annotation_path, "r", encoding="utf-8") as f:
			annotation = f.read()
	except Exception as e:
		annotation = f"Error reading annotation: {e}"

	return render(request, "books/book_data_editor.html", {
		"book_folder": book_folder,
		"manuscript": manuscript,
		"annotation": annotation,
		"cover_path": cover_path,
		"saved": saved,
		"error": error,
		"version_choices": version_choices,
	})


from django.conf import settings

ANNOTATIONS_DIR = os.path.join(settings.BASE_DIR, '..', 'pipeline', 'annotations')

def annotation_list(request):
	try:
		annotation_files = [f for f in os.listdir(ANNOTATIONS_DIR) if f.endswith('.json')]
	except FileNotFoundError:
		annotation_files = []
	return render(request, "books/annotations/annotation_list.html", {"annotation_files": annotation_files})

def annotation_edit(request, filename):
	# Security: prevent path traversal
	if '/' in filename or '\\' in filename or not filename.endswith('.json'):
		return render(request, "books/annotations/annotation_edit.html", {"filename": filename, "content": "Invalid filename.", "saved": False})
	annotation_path = os.path.join(ANNOTATIONS_DIR, filename)
	saved = False
	if request.method == "POST":
		new_content = request.POST.get("content", "")
		try:
			# Validate JSON before saving
			json.loads(new_content)
			with open(annotation_path, 'w', encoding='utf-8') as f:
				f.write(new_content)
			saved = True
		except Exception as e:
			return render(request, "books/annotations/annotation_edit.html", {"filename": filename, "content": f"Error saving file: {e}", "saved": False})
	try:
		with open(annotation_path, 'r', encoding='utf-8') as f:
			content = f.read()
	except Exception as e:
		content = f"Error reading file: {e}"
	return render(request, "books/annotations/annotation_edit.html", {"filename": filename, "content": content, "saved": saved})


from django.conf import settings

MANUSCRIPTS_DIR = os.path.join(settings.BASE_DIR, '..', 'pipeline', 'manuscripts')


def book_list(request):
	# List all .txt files in the manuscripts directory
	try:
		manuscripts = [f for f in os.listdir(MANUSCRIPTS_DIR) if f.endswith('.txt')]
	except FileNotFoundError:
		manuscripts = []
	return render(request, "books/book_list.html", {"manuscripts": manuscripts})

def manuscript_detail(request, filename):
	# Security: prevent path traversal
	if '/' in filename or '\\' in filename or not filename.endswith('.txt'):
		return render(request, "books/manuscript_detail.html", {"filename": filename, "content": "Invalid filename.", "saved": False, "annotation": None})
	manuscript_path = os.path.join(MANUSCRIPTS_DIR, filename)
	saved = False
	if request.method == "POST":
		new_content = request.POST.get("content", "")
		try:
			with open(manuscript_path, 'w', encoding='utf-8') as f:
				f.write(new_content)
			saved = True
		except Exception as e:
			return render(request, "books/manuscript_detail.html", {"filename": filename, "content": f"Error saving file: {e}", "saved": False, "annotation": None})
	try:
		with open(manuscript_path, 'r', encoding='utf-8') as f:
			content = f.read()
	except Exception as e:
		content = f"Error reading file: {e}"

	# Try to load annotation file with matching base name
	base = os.path.splitext(filename)[0]
	annotation_file = base + '.json'
	annotation_path = os.path.join(ANNOTATIONS_DIR, annotation_file)
	annotation = None
	if os.path.exists(annotation_path):
		try:
			with open(annotation_path, 'r', encoding='utf-8') as f:
				annotation = json.load(f)
		except Exception:
			annotation = None

	return render(request, "books/manuscript_detail.html", {"filename": filename, "content": content, "saved": saved, "annotation": annotation})


# EPUB Building Views
def book_dashboard(request):
	"""Dashboard to manage books and EPUB builds"""
	books = Book.objects.all()
	
	# Auto-create books from manuscripts if none exist
	if not books.exists():
		try:
			manuscripts = [f for f in os.listdir(MANUSCRIPTS_DIR) if f.endswith('.txt')]
			for manuscript in manuscripts:
				base_name = os.path.splitext(manuscript)[0]
				title = base_name.replace('_', ' ').title()
				slug = base_name.replace('_', '-')
				
				Book.objects.create(
					title=title,
					author="Unknown Author",  # Will be extracted from manuscript during build
					slug=slug,
					manuscript_path=f"manuscripts/{manuscript}",
					annotations_path=f"annotations/{base_name}_notes_enhanced.json",
				)
			books = Book.objects.all()
		except Exception as e:
			pass
	
	return render(request, "books/book_dashboard.html", {"books": books})


import threading
import json as json_module

def run_build_in_background(build_id, book, pipeline_dir, venv_python):
	"""Run the build pipeline in a background thread"""
	from .models import EPUBBuild
	import json
	
	build = EPUBBuild.objects.get(id=build_id)
	stage_logs = []
	ai_thinking_buffer = []
	
	def log_stage(stage, message, status='running'):
		stage_logs.append({
			'stage': stage,
			'message': message,
			'status': status,
			'timestamp': timezone.now().isoformat()
		})
		build.current_stage = stage
		build.stage_log = json.dumps(stage_logs)
		build.status = stage if status == 'running' else build.status
		build.save()
	
	def log_ai_thinking(text):
		"""Log AI thinking output for display"""
		ai_thinking_buffer.append(text)
		# Update the stage log with AI thinking
		if stage_logs and stage_logs[-1].get('stage') == 'analyzing':
			stage_logs[-1]['ai_thinking'] = ''.join(ai_thinking_buffer[-100:])  # Keep last 100 chunks
			build.stage_log = json.dumps(stage_logs)
			build.save()
	
	try:
		title = book.title
		author = book.author
		manuscript_path = os.path.join(pipeline_dir, book.manuscript_path) if not os.path.isabs(book.manuscript_path) else book.manuscript_path
		output_base = os.path.splitext(os.path.basename(book.manuscript_path))[0]
		output_path = os.path.join(pipeline_dir, 'output', f'{output_base}_press.epub')
		
		# Determine cover path
		cover_path = None
		if book.cover_path:
			cover_path = os.path.join(pipeline_dir, book.cover_path) if not os.path.isabs(book.cover_path) else book.cover_path
		
		# Run the full pipeline with all stages
		log_stage('ingesting', 'Starting text ingestion...')
		
		pipeline_cmd = [
			venv_python, '-m', 'scripts.full_pipeline',
			'--input', manuscript_path,
			'--output', os.path.join(pipeline_dir, 'output'),
			'--title', title,
			'--author', author,
		]
		if cover_path:
			pipeline_cmd.extend(['--cover', cover_path])
		
		# Run pipeline and capture output
		process = subprocess.Popen(
			pipeline_cmd,
			cwd=pipeline_dir,
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			text=True,
			bufsize=1
		)
		
		# Parse output for stage updates and AI thinking
		in_ai_thinking = False
		for line in process.stdout:
			line_stripped = line.strip()
			
			# Handle AI thinking output
			if line_stripped.startswith('AI_THINKING:'):
				in_ai_thinking = True
				thinking_content = line_stripped[12:].strip()
				if thinking_content:
					log_ai_thinking(thinking_content + '\n')
				continue
			elif line_stripped == 'AI_THINKING_COMPLETE':
				in_ai_thinking = False
				ai_thinking_buffer.clear()
				continue
			elif in_ai_thinking:
				# This is continuation of AI thinking
				log_ai_thinking(line)
				continue
			
			if line_stripped.startswith('STAGE:'):
				parts = line_stripped.split(':', 3)
				if len(parts) >= 4:
					_, stage, status, message = parts
					log_stage(stage, message, status)
			elif line_stripped.startswith('STATS:'):
				try:
					stats = json.loads(line_stripped[6:])
					build.section_count = stats.get('sections', 0)
					build.annotation_count = stats.get('annotations', 0)
					build.chapter_count = stats.get('chapters', 0)
					build.save()
				except:
					pass
			elif line_stripped.startswith('PIPELINE:COMPLETE:'):
				pass  # Success handled below
			elif line_stripped.startswith('PIPELINE:ERROR:'):
				raise Exception(line_stripped[15:])
		
		process.wait()
		
		if process.returncode == 0 and os.path.exists(output_path):
			build.status = 'success'
			build.output_path = output_path
			build.file_size = os.path.getsize(output_path)
			
			# Update book's annotation path
			book.annotations_path = f'annotations/{output_base}_notes_enhanced.json'
			book.save()
			
			log_stage('complete', 'Build completed successfully!', 'complete')
		else:
			build.status = 'failed'
			build.error_message = f"Pipeline exited with code {process.returncode}"
		
	except Exception as e:
		build.status = 'failed'
		build.error_message = str(e)
		log_stage('error', str(e), 'failed')
	
	finally:
		build.completed_at = timezone.now()
		build.save()


def build_epub(request, book_id):
	"""Trigger EPUB build for a book"""
	book = get_object_or_404(Book, id=book_id)
	
	# Create build record
	build = EPUBBuild.objects.create(
		book=book,
		status='pending',
		current_stage='pending',
		started_at=timezone.now()
	)
	
	# Use the venv Python
	venv_python = os.path.join(settings.BASE_DIR, '..', '.venv', 'bin', 'python')
	if not os.path.exists(venv_python):
		venv_python = 'python3'
	
	# Start build in background thread
	thread = threading.Thread(
		target=run_build_in_background,
		args=(build.id, book, PIPELINE_DIR, venv_python)
	)
	thread.daemon = True
	thread.start()
	
	# Redirect to build detail immediately
	return redirect('build_detail', build_id=build.id)


def build_detail(request, build_id):
	"""View build status and download"""
	build = get_object_or_404(EPUBBuild, id=build_id)
	
	# Parse stage log
	try:
		stage_logs = json_module.loads(build.stage_log) if build.stage_log else []
	except:
		stage_logs = []
	
	return render(request, "books/build_detail.html", {
		"build": build,
		"stage_logs": stage_logs,
	})


def download_epub(request, build_id):
	"""Download the built EPUB file"""
	build = get_object_or_404(EPUBBuild, id=build_id)
	
	if not build.is_downloadable():
		return redirect('build_detail', build_id=build.id)
	
	# Serve the file
	file_path = build.output_path
	response = FileResponse(open(file_path, 'rb'))
	response['Content-Disposition'] = f'attachment; filename="{build.book.slug}.epub"'
	response['Content-Type'] = 'application/epub+zip'
	return response


def build_status_api(request, build_id):
	"""API endpoint to check build status"""
	build = get_object_or_404(EPUBBuild, id=build_id)
	
	# Parse stage log
	try:
		stage_logs = json_module.loads(build.stage_log) if build.stage_log else []
	except:
		stage_logs = []
	
	return JsonResponse({
		'id': build.id,
		'status': build.status,
		'current_stage': build.current_stage,
		'stage_logs': stage_logs,
		'file_size_mb': build.file_size_mb(),
		'chapter_count': build.chapter_count,
		'section_count': getattr(build, 'section_count', None),
		'annotation_count': getattr(build, 'annotation_count', None),
		'error': build.error_message,
		'is_downloadable': build.is_downloadable(),
		'completed_at': build.completed_at.isoformat() if build.completed_at else None,
	})


# ==================== AI Configuration Views ====================

from .models import AIProvider

def ai_config(request):
	"""AI Configuration page"""
	providers = AIProvider.objects.all()
	connected_count = providers.filter(last_test_success=True).count()
	primary_provider = providers.filter(is_primary=True).first()
	
	return render(request, "books/ai_config.html", {
		"providers": providers,
		"connected_count": connected_count,
		"primary_provider": primary_provider,
	})


def ai_status_api(request):
	"""API endpoint for AI status check"""
	providers = AIProvider.objects.filter(is_active=True)
	connected = providers.filter(last_test_success=True)
	primary = providers.filter(is_primary=True).first()
	
	return JsonResponse({
		"has_providers": providers.exists(),
		"any_connected": connected.exists(),
		"connected_count": connected.count(),
		"total_count": providers.count(),
		"primary_provider": primary.name if primary else None,
		"primary_connected": primary.last_test_success if primary else False,
	})


@require_http_methods(["POST"])
def ai_add_provider(request):
	"""Add a new AI provider"""
	provider = AIProvider(
		name=request.POST.get('name'),
		provider_type=request.POST.get('provider_type'),
		api_url=request.POST.get('api_url'),
		default_model=request.POST.get('default_model'),
		api_key=request.POST.get('api_key') or None,
		priority=int(request.POST.get('priority', 0)),
		is_active=request.POST.get('is_active') == 'on',
		is_primary=request.POST.get('is_primary') == 'on',
	)
	provider.save()
	
	# Test the connection immediately
	provider.test_connection()
	
	return redirect('ai_config')


def ai_edit_provider(request, provider_id):
	"""Edit an AI provider"""
	provider = get_object_or_404(AIProvider, id=provider_id)
	
	if request.method == 'POST':
		provider.name = request.POST.get('name')
		provider.provider_type = request.POST.get('provider_type')
		provider.api_url = request.POST.get('api_url')
		provider.default_model = request.POST.get('default_model')
		provider.priority = int(request.POST.get('priority', 0))
		provider.is_active = request.POST.get('is_active') == 'on'
		provider.is_primary = request.POST.get('is_primary') == 'on'
		
		# Only update API key if a new one is provided
		new_key = request.POST.get('api_key')
		if new_key:
			provider.api_key = new_key
		
		provider.save()
		return redirect('ai_config')
	
	return render(request, "books/ai_edit_provider.html", {
		"provider": provider,
	})


@require_http_methods(["POST"])
def ai_delete_provider(request, provider_id):
	"""Delete an AI provider"""
	provider = get_object_or_404(AIProvider, id=provider_id)
	provider.delete()
	return redirect('ai_config')


@require_http_methods(["POST"])
def ai_test_provider(request, provider_id):
	"""Test a single AI provider connection"""
	provider = get_object_or_404(AIProvider, id=provider_id)
	success, message = provider.test_connection()
	return redirect('ai_config')


@require_http_methods(["POST"])
def ai_test_all(request):
	"""Test all AI provider connections"""
	providers = AIProvider.objects.filter(is_active=True)
	for provider in providers:
		provider.test_connection()
	return redirect('ai_config')


@require_http_methods(["POST"])
def ai_set_primary(request, provider_id):
	"""Set a provider as primary"""
	provider = get_object_or_404(AIProvider, id=provider_id)
	AIProvider.objects.all().update(is_primary=False)
	provider.is_primary = True
	provider.save()
	return redirect('ai_config')


# ==================== Audiobook Configuration Views ====================

from .models import TTSProvider, VoiceProfile, CharacterVoiceMapping, AudioBuild, AudioAsset

def audiobook_config(request, book_id):
	"""Audiobook configuration page - set up voices and build options"""
	book = get_object_or_404(Book, id=book_id)
	
	# Get TTS providers
	tts_providers = TTSProvider.objects.filter(is_active=True)
	primary_tts = tts_providers.filter(is_primary=True).first()
	
	# Get available voice profiles
	voice_profiles = VoiceProfile.objects.filter(is_active=True)
	narrator_voices = voice_profiles.filter(role='narrator')
	annotator_voices = voice_profiles.filter(role='annotator')
	character_voices = voice_profiles.filter(role='character')
	
	# Get existing character mappings for this book
	character_mappings = CharacterVoiceMapping.objects.filter(book=book)
	
	# Get recent audio builds
	audio_builds = AudioBuild.objects.filter(book=book).order_by('-created_at')[:5]
	last_build = audio_builds.first() if audio_builds.exists() else None
	
	# Get audio assets for bumper/outro
	bumper_assets = AudioAsset.objects.filter(is_active=True, asset_type='bumper')
	outro_assets = AudioAsset.objects.filter(is_active=True, asset_type='outro')
	legal_assets = AudioAsset.objects.filter(is_active=True, asset_type='legal')
	transition_assets = AudioAsset.objects.filter(is_active=True, asset_type='transition')
	effect_assets = AudioAsset.objects.filter(is_active=True, asset_type='effect')
	
	# Count sections for the book
	section_count = 0
	try:
		pipeline_dir = os.path.join(settings.BASE_DIR.parent, 'pipeline')
		book_slug = book.title.lower().replace(' ', '_')
		book_data_path = os.path.join(pipeline_dir, 'output', f'{book_slug}_book_data.json')
		if os.path.exists(book_data_path):
			with open(book_data_path, 'r') as f:
				book_data = json.load(f)
				section_count = len(book_data.get('sections', []))
		else:
			# Try annotations file
			annotations_path = os.path.join(pipeline_dir, 'annotations', f'{book_slug}_notes_enhanced.json')
			if os.path.exists(annotations_path):
				with open(annotations_path, 'r') as f:
					annotations_data = json.load(f)
					if isinstance(annotations_data, dict):
						section_count = len(annotations_data.get('sections', []))
					else:
						section_count = len(annotations_data)
	except:
		pass
	
	# Default legal disclaimer
	default_legal_disclaimer = """This audiobook was produced using the Forge Publisher platform. The original work is in the public domain. This audio edition, including all narration, annotations, and commentary, is copyright of the publisher.

Annotations and commentary represent educational interpretations and do not constitute legal, medical, or professional advice. Views expressed are for educational and entertainment purposes only.

Unauthorized reproduction or distribution of this audio is prohibited."""
	
	# Detect characters from book data (if available)
	detected_characters = []
	try:
		book_data_path = os.path.join(BOOKS_DATA_DIR, book.title.lower().replace(' ', '_'), 'book_data.json')
		if os.path.exists(book_data_path):
			with open(book_data_path, 'r') as f:
				book_data = json.load(f)
				detected_characters = book_data.get('characters', [])
	except:
		# Default characters for common books
		if 'metamorphosis' in book.title.lower():
			detected_characters = ['Gregor', 'Grete', 'Father', 'Mother', 'Chief Clerk']
	
	return render(request, "books/audiobook_config.html", {
		"book": book,
		"tts_providers": tts_providers,
		"primary_tts": primary_tts,
		"voice_profiles": voice_profiles,
		"narrator_voices": narrator_voices,
		"annotator_voices": annotator_voices,
		"character_voices": character_voices,
		"character_mappings": character_mappings,
		"audio_builds": audio_builds,
		"last_build": last_build,
		"detected_characters": detected_characters,
		"bumper_assets": bumper_assets,
		"outro_assets": outro_assets,
		"legal_assets": legal_assets,
		"transition_assets": transition_assets,
		"effect_assets": effect_assets,
		"section_count": section_count,
		"default_legal_disclaimer": default_legal_disclaimer,
	})


@require_http_methods(["POST"])
def audiobook_save_voices(request, book_id):
	"""Save voice configuration for a book"""
	book = get_object_or_404(Book, id=book_id)
	
	# Update character voice mappings
	# First, clear existing mappings
	CharacterVoiceMapping.objects.filter(book=book).delete()
	
	# Process form data for character mappings
	character_names = request.POST.getlist('character_name')
	voice_ids = request.POST.getlist('voice_id')
	
	for name, voice_id in zip(character_names, voice_ids):
		if name and voice_id:
			try:
				voice = VoiceProfile.objects.get(id=voice_id)
				CharacterVoiceMapping.objects.create(
					book=book,
					character_name=name,
					voice=voice
				)
			except VoiceProfile.DoesNotExist:
				pass
	
	return redirect('audiobook_config', book_id=book_id)


@require_http_methods(["POST"])
def audiobook_build(request, book_id):
	"""Start building an audiobook"""
	book = get_object_or_404(Book, id=book_id)
	
	# Get selected options
	tts_provider_id = request.POST.get('tts_provider')
	narrator_voice_id = request.POST.get('narrator_voice')
	annotator_voice_id = request.POST.get('annotator_voice')
	include_annotations = request.POST.get('include_annotations') == 'on'
	
	# Get new options
	style_prompt = request.POST.get('style_prompt', '').strip()
	include_legal_disclaimer = request.POST.get('include_legal_disclaimer') == 'on'
	legal_disclaimer_text = request.POST.get('legal_disclaimer_text', '').strip()
	bumper_asset_id = request.POST.get('bumper_asset')
	outro_asset_id = request.POST.get('outro_asset')
	annotator_intro_stinger_id = request.POST.get('annotator_intro_stinger')
	annotator_outro_stinger_id = request.POST.get('annotator_outro_stinger')
	start_section = request.POST.get('start_section', '1')
	end_section = request.POST.get('end_section', '')
	
	# Get the provider
	tts_provider = None
	if tts_provider_id:
		try:
			tts_provider = TTSProvider.objects.get(id=tts_provider_id)
		except TTSProvider.DoesNotExist:
			pass
	
	# Get voices
	narrator_voice = None
	annotator_voice = None
	if narrator_voice_id:
		try:
			narrator_voice = VoiceProfile.objects.get(id=narrator_voice_id)
		except VoiceProfile.DoesNotExist:
			pass
	if annotator_voice_id:
		try:
			annotator_voice = VoiceProfile.objects.get(id=annotator_voice_id)
		except VoiceProfile.DoesNotExist:
			pass
	
	# Get bumper/outro audio paths
	bumper_audio_path = None
	outro_audio_path = None
	if bumper_asset_id:
		try:
			bumper_asset = AudioAsset.objects.get(id=bumper_asset_id)
			bumper_audio_path = bumper_asset.get_audio_path()
		except AudioAsset.DoesNotExist:
			pass
	if outro_asset_id:
		try:
			outro_asset = AudioAsset.objects.get(id=outro_asset_id)
			outro_audio_path = outro_asset.get_audio_path()
		except AudioAsset.DoesNotExist:
			pass
	
	# Get annotator stinger paths
	annotator_intro_stinger_path = None
	annotator_outro_stinger_path = None
	if annotator_intro_stinger_id:
		try:
			stinger_asset = AudioAsset.objects.get(id=annotator_intro_stinger_id)
			annotator_intro_stinger_path = stinger_asset.get_audio_path()
		except AudioAsset.DoesNotExist:
			pass
	if annotator_outro_stinger_id:
		try:
			stinger_asset = AudioAsset.objects.get(id=annotator_outro_stinger_id)
			annotator_outro_stinger_path = stinger_asset.get_audio_path()
		except AudioAsset.DoesNotExist:
			pass
	
	# Parse section values
	try:
		start_section_num = int(start_section) if start_section else 1
	except ValueError:
		start_section_num = 1
	
	try:
		end_section_num = int(end_section) if end_section else None
	except ValueError:
		end_section_num = None
	
	# Create the audio build record
	audio_build = AudioBuild.objects.create(
		book=book,
		tts_provider=tts_provider,
		narrator_voice=narrator_voice,
		annotator_voice=annotator_voice,
		include_annotations=include_annotations,
		style_prompt=style_prompt,
		include_legal_disclaimer=include_legal_disclaimer,
		legal_disclaimer_text=legal_disclaimer_text,
		bumper_audio_path=bumper_audio_path,
		outro_audio_path=outro_audio_path,
		start_section=start_section_num,
		end_section=end_section_num,
		status='pending',
	)
	
	# Start the build process in background
	audio_build.status = 'generating'
	audio_build.started_at = timezone.now()
	audio_build.save()
	
	# Spawn the audio generation process
	pipeline_dir = os.path.join(settings.BASE_DIR.parent, 'pipeline')
	script_path = os.path.join(pipeline_dir, 'scripts', 'generate_audiobook.py')
	
	# Build command arguments
	cmd = [
		sys.executable,  # Use same Python interpreter
		script_path,
		'--build-id', str(audio_build.id),
		'--book-title', book.title,
	]
	
	# Add provider type
	if tts_provider:
		provider_type = tts_provider.provider_type.lower()
		cmd.extend(['--provider', provider_type])
		if tts_provider.server_url:
			cmd.extend(['--server-url', tts_provider.server_url])
	else:
		cmd.extend(['--provider', 'pyttsx3'])  # Default fallback
	
	# Add voice configs as JSON
	if narrator_voice:
		narrator_config = {
			'voice_id': narrator_voice.voice_id or '',
			'name': narrator_voice.name,
			'speed': narrator_voice.speed,
			'pitch': narrator_voice.pitch,
			'tone': narrator_voice.tone,
		}
		cmd.extend(['--narrator-config', json.dumps(narrator_config)])
	
	if annotator_voice:
		annotator_config = {
			'voice_id': annotator_voice.voice_id or '',
			'name': annotator_voice.name,
			'speed': annotator_voice.speed,
			'pitch': annotator_voice.pitch,
			'tone': annotator_voice.tone,
		}
		cmd.extend(['--annotator-config', json.dumps(annotator_config)])
	
	if not include_annotations:
		cmd.append('--no-annotations')
	
	# Add new options
	if style_prompt:
		cmd.extend(['--style-prompt', style_prompt])
	
	if include_legal_disclaimer and legal_disclaimer_text:
		cmd.extend(['--legal-disclaimer', legal_disclaimer_text])
	
	if bumper_audio_path:
		cmd.extend(['--bumper', bumper_audio_path])
	
	if outro_audio_path:
		cmd.extend(['--outro', outro_audio_path])
	
	if start_section_num > 1:
		cmd.extend(['--start-section', str(start_section_num)])
	
	if end_section_num:
		cmd.extend(['--end-section', str(end_section_num)])
	
	if annotator_intro_stinger_path:
		cmd.extend(['--annotator-intro-stinger', annotator_intro_stinger_path])
	
	if annotator_outro_stinger_path:
		cmd.extend(['--annotator-outro-stinger', annotator_outro_stinger_path])
	
	# Log the command
	print(f"[AUDIOBOOK] Starting generation: {' '.join(cmd)}")
	
	# Run in background
	log_dir = os.path.join(pipeline_dir, 'output', 'logs')
	os.makedirs(log_dir, exist_ok=True)
	log_file = os.path.join(log_dir, f'audiobook_build_{audio_build.id}.log')
	
	with open(log_file, 'w') as log:
		subprocess.Popen(
			cmd,
			stdout=log,
			stderr=subprocess.STDOUT,
			start_new_session=True,  # Detach from parent
			cwd=pipeline_dir,
		)
	
	return redirect('audiobook_build_status', build_id=audio_build.id)


def audiobook_build_status(request, build_id):
	"""Show audiobook build status"""
	audio_build = get_object_or_404(AudioBuild, id=build_id)
	
	return render(request, "books/audiobook_build_status.html", {
		"build": audio_build,
		"book": audio_build.book,
	})


def audiobook_status_api(request, build_id):
	"""API endpoint for audiobook build status"""
	build = get_object_or_404(AudioBuild, id=build_id)
	
	return JsonResponse({
		'status': build.status,
		'progress': build.progress_percent(),
		'current_section': build.current_section,
		'total_sections': build.total_sections,
		'error': build.error_message,
		'duration': build.duration_formatted(),
		'file_size_mb': build.file_size_mb(),
		'completed_at': build.completed_at.isoformat() if build.completed_at else None,
	})


@require_http_methods(["POST"])
def voice_profile_create(request):
	"""Create a new voice profile"""
	# Get provider if specified
	provider = None
	provider_id = request.POST.get('provider_id')
	if provider_id:
		try:
			provider = TTSProvider.objects.get(id=provider_id)
		except TTSProvider.DoesNotExist:
			pass
	
	voice = VoiceProfile(
		name=request.POST.get('name'),
		voice_id=request.POST.get('voice_id', ''),
		role=request.POST.get('role', 'character'),
		pitch=float(request.POST.get('pitch', 1.0)),
		speed=float(request.POST.get('speed', 1.0)),
		tone=request.POST.get('tone', 'neutral'),
		description=request.POST.get('description', ''),
		persona_text=request.POST.get('persona_text', ''),
		provider=provider,
	)
	voice.save()
	
	# Redirect back to where we came from
	next_url = request.POST.get('next', 'ai_config')
	return redirect(next_url)


def tts_config(request):
	"""TTS Configuration page"""
	providers = TTSProvider.objects.all()
	voices = VoiceProfile.objects.all()
	primary_provider = providers.filter(is_primary=True).first()
	
	return render(request, "books/tts_config.html", {
		"providers": providers,
		"voices": voices,
		"primary_provider": primary_provider,
	})


@require_http_methods(["POST"])
def tts_add_provider(request):
	"""Add a new TTS provider"""
	provider = TTSProvider(
		name=request.POST.get('name'),
		provider_type=request.POST.get('provider_type'),
		server_url=request.POST.get('server_url'),
		api_key=request.POST.get('api_key') or None,
		sample_rate=int(request.POST.get('sample_rate', 24000)),
		cpu_offload=request.POST.get('cpu_offload') == 'on',
		is_active=request.POST.get('is_active') == 'on',
		is_primary=request.POST.get('is_primary') == 'on',
	)
	provider.save()
	return redirect('tts_config')


@require_http_methods(["POST"])
def tts_set_primary(request, provider_id):
	"""Set a TTS provider as primary"""
	provider = get_object_or_404(TTSProvider, id=provider_id)
	TTSProvider.objects.all().update(is_primary=False)
	provider.is_primary = True
	provider.save()
	return redirect('tts_config')


@require_http_methods(["POST"])
def tts_edit_provider(request, provider_id):
	"""Edit an existing TTS provider"""
	provider = get_object_or_404(TTSProvider, id=provider_id)
	
	provider.name = request.POST.get('name', provider.name)
	provider.provider_type = request.POST.get('provider_type', provider.provider_type)
	provider.server_url = request.POST.get('server_url', provider.server_url)
	if request.POST.get('api_key'):
		provider.api_key = request.POST.get('api_key')
	provider.sample_rate = int(request.POST.get('sample_rate', provider.sample_rate))
	provider.cpu_offload = request.POST.get('cpu_offload') == 'on'
	provider.is_active = request.POST.get('is_active') == 'on'
	provider.save()
	
	return redirect('tts_config')


@require_http_methods(["POST"])
def tts_delete_provider(request, provider_id):
	"""Delete a TTS provider"""
	provider = get_object_or_404(TTSProvider, id=provider_id)
	
	# Don't allow deleting the primary provider
	if provider.is_primary:
		# Set another provider as primary first
		other = TTSProvider.objects.exclude(id=provider_id).first()
		if other:
			other.is_primary = True
			other.save()
	
	provider.delete()
	return redirect('tts_config')


@require_http_methods(["GET"])
def tts_get_voices(request, provider_id):
	"""Get available voices for a TTS provider - returns JSON"""
	import json
	
	provider = get_object_or_404(TTSProvider, id=provider_id)
	voices = []
	
	if provider.provider_type == 'edge-tts':
		# All Edge TTS English voices with personalities
		voices = [
			# US English voices
			{"id": "en-US-AvaNeural", "name": "Ava (US)", "gender": "Female", "style": "Expressive, Caring, Warm"},
			{"id": "en-US-AndrewNeural", "name": "Andrew (US)", "gender": "Male", "style": "Warm, Confident"},
			{"id": "en-US-EmmaNeural", "name": "Emma (US)", "gender": "Female", "style": "Cheerful, Conversational"},
			{"id": "en-US-BrianNeural", "name": "Brian (US)", "gender": "Male", "style": "Approachable, Casual"},
			{"id": "en-US-ChristopherNeural", "name": "Christopher (US)", "gender": "Male", "style": "Reliable, Authority"},
			{"id": "en-US-JennyNeural", "name": "Jenny (US)", "gender": "Female", "style": "Friendly, Comfort"},
			{"id": "en-US-GuyNeural", "name": "Guy (US)", "gender": "Male", "style": "Passion, Newscast"},
			{"id": "en-US-AriaNeural", "name": "Aria (US)", "gender": "Female", "style": "Stories, Narration"},
			{"id": "en-US-DavisNeural", "name": "Davis (US)", "gender": "Male", "style": "Chat, Stories"},
			{"id": "en-US-JaneNeural", "name": "Jane (US)", "gender": "Female", "style": "Angry, Fearful"},
			{"id": "en-US-JasonNeural", "name": "Jason (US)", "gender": "Male", "style": "Cheerful, Whisper"},
			{"id": "en-US-NancyNeural", "name": "Nancy (US)", "gender": "Female", "style": "Cheerful, Serious"},
			{"id": "en-US-SaraNeural", "name": "Sara (US)", "gender": "Female", "style": "Friendly, Light"},
			{"id": "en-US-TonyNeural", "name": "Tony (US)", "gender": "Male", "style": "Friendly, Serious"},
			{"id": "en-US-MichelleNeural", "name": "Michelle (US)", "gender": "Female", "style": "Clear, Neutral"},
			{"id": "en-US-RogerNeural", "name": "Roger (US)", "gender": "Male", "style": "News, Sports"},
			{"id": "en-US-SteffanNeural", "name": "Steffan (US)", "gender": "Male", "style": "Friendly"},
			{"id": "en-US-EricNeural", "name": "Eric (US)", "gender": "Male", "style": "Neutral"},
			{"id": "en-US-RyanMultilingualNeural", "name": "Ryan Multilingual (US)", "gender": "Male", "style": "Professional"},
			{"id": "en-US-AdamMultilingualNeural", "name": "Adam Multilingual (US)", "gender": "Male", "style": "Professional"},
			{"id": "en-US-AvaMultilingualNeural", "name": "Ava Multilingual (US)", "gender": "Female", "style": "Expressive"},
			{"id": "en-US-EmmaMultilingualNeural", "name": "Emma Multilingual (US)", "gender": "Female", "style": "Cheerful"},
			{"id": "en-US-AndrewMultilingualNeural", "name": "Andrew Multilingual (US)", "gender": "Male", "style": "Warm"},
			{"id": "en-US-BrianMultilingualNeural", "name": "Brian Multilingual (US)", "gender": "Male", "style": "Casual"},
			{"id": "en-US-AlloyTurboMultilingualNeural", "name": "Alloy Turbo (US)", "gender": "Neutral", "style": "Fast"},
			{"id": "en-US-NovaTurboMultilingualNeural", "name": "Nova Turbo (US)", "gender": "Female", "style": "Fast, Bright"},
			{"id": "en-US-AnaNeural", "name": "Ana (US, Child)", "gender": "Female", "style": "Child"},
			{"id": "en-US-BlueNeural", "name": "Blue (US)", "gender": "Neutral", "style": "Optimized"},
			{"id": "en-US-KaiNeural", "name": "Kai (US)", "gender": "Male", "style": "Conversation"},
			{"id": "en-US-LunaNeural", "name": "Luna (US)", "gender": "Female", "style": "Friendly"},
			
			# British English voices
			{"id": "en-GB-SoniaNeural", "name": "Sonia (UK)", "gender": "Female", "style": "Cheerful, Sad"},
			{"id": "en-GB-RyanNeural", "name": "Ryan (UK)", "gender": "Male", "style": "Cheerful, Whisper"},
			{"id": "en-GB-LibbyNeural", "name": "Libby (UK)", "gender": "Female", "style": "British Accent"},
			{"id": "en-GB-ThomasNeural", "name": "Thomas (UK)", "gender": "Male", "style": "British Accent"},
			{"id": "en-GB-MaisieNeural", "name": "Maisie (UK)", "gender": "Female", "style": "British Accent"},
			{"id": "en-GB-NoahNeural", "name": "Noah (UK)", "gender": "Male", "style": "British Accent"},
			{"id": "en-GB-OllieMultilingualNeural", "name": "Ollie Multilingual (UK)", "gender": "Male", "style": "British"},
			
			# Australian English
			{"id": "en-AU-NatashaNeural", "name": "Natasha (AU)", "gender": "Female", "style": "Australian"},
			{"id": "en-AU-WilliamNeural", "name": "William (AU)", "gender": "Male", "style": "Australian"},
			
			# Canadian English
			{"id": "en-CA-ClaraNeural", "name": "Clara (CA)", "gender": "Female", "style": "Canadian"},
			{"id": "en-CA-LiamNeural", "name": "Liam (CA)", "gender": "Male", "style": "Canadian"},
			
			# Indian English
			{"id": "en-IN-NeerjaNeural", "name": "Neerja (India)", "gender": "Female", "style": "Indian English"},
			{"id": "en-IN-PrabhatNeural", "name": "Prabhat (India)", "gender": "Male", "style": "Indian English"},
			
			# Irish English
			{"id": "en-IE-ConnorNeural", "name": "Connor (Ireland)", "gender": "Male", "style": "Irish"},
			{"id": "en-IE-EmilyNeural", "name": "Emily (Ireland)", "gender": "Female", "style": "Irish"},
			
			# New Zealand English
			{"id": "en-NZ-MitchellNeural", "name": "Mitchell (NZ)", "gender": "Male", "style": "New Zealand"},
			{"id": "en-NZ-MollyNeural", "name": "Molly (NZ)", "gender": "Female", "style": "New Zealand"},
		]
		
	elif provider.provider_type == 'xtts':
		# XTTS uses voice cloning - show available reference voices
		voices = [
			{"id": "default", "name": "Default Voice", "gender": "Neutral", "style": "Standard"},
			{"id": "clone", "name": "Voice Clone (Upload Reference)", "gender": "Clone", "style": "Uses uploaded audio sample"},
		]
		
	elif provider.provider_type == 'pyttsx3':
		# System voices - varies by OS
		try:
			import pyttsx3
			engine = pyttsx3.init()
			for voice in engine.getProperty('voices'):
				voice_id = voice.id
				# Extract readable name from voice ID
				name = voice.name if hasattr(voice, 'name') else voice_id.split('.')[-1]
				gender = 'Female' if 'female' in voice_id.lower() or 'samantha' in voice_id.lower() else 'Male'
				voices.append({
					"id": voice_id,
					"name": name,
					"gender": gender,
					"style": "System Voice"
				})
			engine.stop()
		except Exception as e:
			voices = [{"id": "default", "name": "Default System Voice", "gender": "Neutral", "style": "System"}]
			
	elif provider.provider_type == 'piper':
		# Piper TTS voices - will be populated based on downloaded models
		voices = [
			{"id": "en_US-lessac-medium", "name": "Lessac (US)", "gender": "Male", "style": "Clear, Audiobook"},
			{"id": "en_US-libritts-high", "name": "LibriTTS (US)", "gender": "Neutral", "style": "High Quality"},
			{"id": "en_US-arctic-medium", "name": "Arctic (US)", "gender": "Male", "style": "Natural"},
			{"id": "en_US-kathleen-low", "name": "Kathleen (US)", "gender": "Female", "style": "Compact"},
			{"id": "en_GB-cori-high", "name": "Cori (UK)", "gender": "Female", "style": "British"},
			{"id": "en_GB-alan-medium", "name": "Alan (UK)", "gender": "Male", "style": "British"},
		]
	
	elif provider.provider_type == 'gtts':
		# Google TTS - language based
		voices = [
			{"id": "en", "name": "English (General)", "gender": "Neutral", "style": "Standard"},
			{"id": "en-us", "name": "English US", "gender": "Neutral", "style": "American"},
			{"id": "en-uk", "name": "English UK", "gender": "Neutral", "style": "British"},
			{"id": "en-au", "name": "English AU", "gender": "Neutral", "style": "Australian"},
		]
		
	elif provider.provider_type == 'azure':
		# Azure TTS - similar to Edge but requires API key
		voices = [
			{"id": "en-US-JennyNeural", "name": "Jenny (US)", "gender": "Female", "style": "Friendly"},
			{"id": "en-US-GuyNeural", "name": "Guy (US)", "gender": "Male", "style": "Newscast"},
			{"id": "en-GB-SoniaNeural", "name": "Sonia (UK)", "gender": "Female", "style": "Cheerful"},
			{"id": "en-GB-RyanNeural", "name": "Ryan (UK)", "gender": "Male", "style": "British"},
		]
		
	elif provider.provider_type == 'riva':
		voices = [
			{"id": "English-US-Female-1", "name": "US Female", "gender": "Female", "style": "Standard"},
			{"id": "English-US-Male-1", "name": "US Male", "gender": "Male", "style": "Standard"},
		]
		
	return JsonResponse({"voices": voices})


def download_audiobook(request, build_id):
	"""Download a completed audiobook"""
	build = get_object_or_404(AudioBuild, id=build_id)
	
	if build.status != 'success' or not build.output_path:
		return HttpResponse("Audiobook not available", status=404)
	
	if not os.path.exists(build.output_path):
		return HttpResponse("Audiobook file not found", status=404)
	
	# Determine content type
	file_ext = os.path.splitext(build.output_path)[1].lower()
	content_types = {
		'.wav': 'audio/wav',
		'.mp3': 'audio/mpeg',
		'.m4a': 'audio/mp4',
		'.ogg': 'audio/ogg',
	}
	content_type = content_types.get(file_ext, 'application/octet-stream')
	
	# Generate filename
	filename = f"{build.book.title.replace(' ', '_')}_audiobook{file_ext}"
	
	# Stream the file
	response = FileResponse(
		open(build.output_path, 'rb'),
		content_type=content_type
	)
	response['Content-Disposition'] = f'attachment; filename="{filename}"'
	return response


@csrf_exempt
@require_http_methods(["POST"])
def voice_preview(request):
	"""Generate a voice preview audio sample"""
	voice_id = request.POST.get('voice_id')
	sample_text = request.POST.get('sample_text', 'Hello, this is a preview of how I sound.')
	provider_id = request.POST.get('provider_id')
	provider_voice_id = request.POST.get('provider_voice_id')  # Direct voice ID from provider (e.g., en-US-AvaNeural)
	
	# Custom voice parameters (for previewing new voice settings)
	custom_pitch = request.POST.get('pitch')
	custom_speed = request.POST.get('speed')
	custom_tone = request.POST.get('tone')
	
	# Get voice profile
	voice = None
	if voice_id:
		try:
			voice = VoiceProfile.objects.get(id=voice_id)
		except VoiceProfile.DoesNotExist:
			pass
	
	# Get TTS provider
	provider = None
	if provider_id:
		try:
			provider = TTSProvider.objects.get(id=provider_id)
		except TTSProvider.DoesNotExist:
			pass
	
	if not provider:
		provider = TTSProvider.objects.filter(is_primary=True, is_active=True).first()
	
	if not provider:
		return JsonResponse({'error': 'No TTS provider configured'}, status=400)
	
	try:
		# Import audio generator
		pipeline_dir = os.path.join(settings.BASE_DIR.parent, 'pipeline')
		sys.path.insert(0, pipeline_dir)
		from scripts.audio_generator import AudioGenerator, VoiceConfig
		
		# Create generator
		generator = AudioGenerator(
			provider=provider.provider_type,
			server_url=provider.server_url,
			sample_rate=provider.sample_rate
		)
		
		# Create voice config
		if voice:
			# Use existing voice profile, but allow overrides
			voice_config = VoiceConfig(
				name=voice.name,
				voice_id=provider_voice_id or voice.voice_id or '',
				pitch=float(custom_pitch) if custom_pitch else voice.pitch,
				speed=float(custom_speed) if custom_speed else voice.speed,
				tone=custom_tone if custom_tone else voice.tone,
				description=voice.description,
				persona_text=voice.persona_text,
			)
		elif provider_voice_id:
			# Use direct provider voice ID (e.g., en-US-AvaNeural for Edge TTS)
			voice_config = VoiceConfig(
				name=provider_voice_id,
				voice_id=provider_voice_id,
				pitch=float(custom_pitch) if custom_pitch else 1.0,
				speed=float(custom_speed) if custom_speed else 1.0,
				tone=custom_tone if custom_tone else 'neutral',
			)
		else:
			# Create voice config from custom parameters
			voice_config = VoiceConfig(
				name='Preview',
				voice_id='',
				pitch=float(custom_pitch) if custom_pitch else 1.0,
				speed=float(custom_speed) if custom_speed else 1.0,
				tone=custom_tone if custom_tone else 'neutral',
			)
		
		# Generate preview
		audio_data = generator.synthesize_text(sample_text, voice_config)
		
		# Return as audio response
		response = HttpResponse(audio_data, content_type='audio/wav')
		response['Content-Disposition'] = 'inline; filename="preview.wav"'
		return response
		
	except Exception as e:
		return JsonResponse({'error': str(e)}, status=500)


def book_sections(request, book_id):
	"""Get sections from a book for preview selection"""
	book = get_object_or_404(Book, id=book_id)
	
	sections = []
	try:
		pipeline_dir = os.path.join(settings.BASE_DIR.parent, 'pipeline')
		book_slug = book.title.lower().replace(' ', '_')
		
		# Try annotations file first (has actual content)
		annotations_path = os.path.join(pipeline_dir, 'annotations', f'{book_slug}_notes_enhanced.json')
		if not os.path.exists(annotations_path):
			annotations_path = os.path.join(pipeline_dir, 'annotations', f'{book_slug}_notes.json')
		
		if os.path.exists(annotations_path):
			with open(annotations_path, 'r') as f:
				annotations_data = json.load(f)
				
			# Handle both list and dict formats
			if isinstance(annotations_data, dict):
				raw_sections = annotations_data.get('sections', [])
			else:
				raw_sections = annotations_data
				
			# Extract section info with preview text
			for i, section in enumerate(raw_sections):
				if isinstance(section, dict):
					title = section.get('title', section.get('heading', f'Section {i+1}'))
					content = section.get('content', section.get('text', ''))
				else:
					title = f'Section {i+1}'
					content = str(section)
				
				# Skip Gutenberg front matter
				title_lower = title.lower()
				if any(skip in title_lower for skip in ['gutenberg', 'project gutenberg', 'start of', 'end of', 'copyright', 'transcriber']):
					continue
				
				# Get first 150 chars as preview
				preview = content[:150].strip() + ('...' if len(content) > 150 else '')
				
				sections.append({
					'index': i,
					'title': title,
					'preview': preview,
					'length': len(content)
				})
		
		# Fallback to book_data.json
		if not sections:
			book_data_path = os.path.join(pipeline_dir, 'output', f'{book_slug}_book_data.json')
			if os.path.exists(book_data_path):
				with open(book_data_path, 'r') as f:
					book_data = json.load(f)
					
				for i, section in enumerate(book_data.get('sections', [])):
					title = section.get('title', f'Section {i+1}')
					content = section.get('content', '')
					preview = content[:150].strip() + ('...' if len(content) > 150 else '')
					
					sections.append({
						'index': i,
						'title': title,
						'preview': preview,
						'length': len(content)
					})
					
	except Exception as e:
		return JsonResponse({'error': str(e), 'sections': []}, status=500)
	
	return JsonResponse({'sections': sections, 'book_title': book.title})


def book_section_content(request, book_id, section_index):
	"""Get full content of a specific section for TTS preview"""
	book = get_object_or_404(Book, id=book_id)
	
	try:
		pipeline_dir = os.path.join(settings.BASE_DIR.parent, 'pipeline')
		book_slug = book.title.lower().replace(' ', '_')
		
		# Try annotations file
		annotations_path = os.path.join(pipeline_dir, 'annotations', f'{book_slug}_notes_enhanced.json')
		if not os.path.exists(annotations_path):
			annotations_path = os.path.join(pipeline_dir, 'annotations', f'{book_slug}_notes.json')
		
		if os.path.exists(annotations_path):
			with open(annotations_path, 'r') as f:
				annotations_data = json.load(f)
				
			if isinstance(annotations_data, dict):
				raw_sections = annotations_data.get('sections', [])
			else:
				raw_sections = annotations_data
			
			if section_index < len(raw_sections):
				section = raw_sections[section_index]
				if isinstance(section, dict):
					title = section.get('title', section.get('heading', f'Section {section_index+1}'))
					content = section.get('content', section.get('text', ''))
					annotation = section.get('annotation', section.get('annotator', ''))
				else:
					title = f'Section {section_index+1}'
					content = str(section)
					annotation = ''
				
				return JsonResponse({
					'title': title,
					'content': content,
					'annotation': annotation,
					'index': section_index,
					'total_sections': len(raw_sections)
				})
		
		return JsonResponse({'error': 'Section not found'}, status=404)
		
	except Exception as e:
		return JsonResponse({'error': str(e)}, status=500)


def edge_tts_voices(request):
	"""List available edge-tts voices"""
	try:
		import edge_tts
		import asyncio
		
		async def get_voices():
			voices = await edge_tts.list_voices()
			return voices
		
		voices = asyncio.run(get_voices())
		
		# Filter to English voices and format nicely
		en_voices = [
			{
				'name': v['ShortName'],
				'friendly_name': v['FriendlyName'],
				'gender': v['Gender'],
				'locale': v['Locale'],
				'style': v.get('StyleList', []),
			}
			for v in voices
			if v['Locale'].startswith('en')
		]
		
		return JsonResponse({'voices': en_voices})
		
	except ImportError:
		return JsonResponse({'error': 'edge-tts not installed. Run: pip install edge-tts'}, status=500)
	except Exception as e:
		return JsonResponse({'error': str(e)}, status=500)


def create_default_edge_tts_voices(request):
	"""Create default edge-tts voice profiles"""
	# Popular edge-tts voices for audiobooks
	default_voices = [
		{
			'name': 'Guy (Edge TTS)',
			'voice_id': 'en-US-GuyNeural',
			'role': 'narrator',
			'pitch': 1.0,
			'speed': 0.95,
			'tone': 'dramatic',
			'description': 'Warm, charismatic male voice - great for narration',
		},
		{
			'name': 'Andrew (Edge TTS)',
			'voice_id': 'en-US-AndrewNeural',
			'role': 'annotator',
			'pitch': 1.0,
			'speed': 1.0,
			'tone': 'friendly',
			'description': 'Warm, authentic male - perfect for annotations',
		},
		{
			'name': 'Aria (Edge TTS)',
			'voice_id': 'en-US-AriaNeural',
			'role': 'narrator',
			'pitch': 1.0,
			'speed': 0.95,
			'tone': 'confident',
			'description': 'Positive, confident female voice - excellent for narration',
		},
		{
			'name': 'Jenny (Edge TTS)',
			'voice_id': 'en-US-JennyNeural',
			'role': 'character',
			'pitch': 1.0,
			'speed': 1.0,
			'tone': 'friendly',
			'description': 'Friendly, considerate female voice',
		},
		{
			'name': 'Christopher (Edge TTS)',
			'voice_id': 'en-US-ChristopherNeural',
			'role': 'narrator',
			'pitch': 1.0,
			'speed': 0.9,
			'tone': 'authoritative',
			'description': 'Reliable, authoritative male voice',
		},
	]
	
	created = []
	for voice_data in default_voices:
		# Check if voice already exists
		if not VoiceProfile.objects.filter(voice_id=voice_data['voice_id']).exists():
			voice = VoiceProfile.objects.create(**voice_data)
			created.append(voice.name)
	
	if created:
		return JsonResponse({'message': f'Created voices: {", ".join(created)}'})
	else:
		return JsonResponse({'message': 'Edge TTS voices already exist'})


@require_http_methods(["POST"])
def tts_test_provider(request, provider_id):
	"""Test a TTS provider connection"""
	provider = get_object_or_404(TTSProvider, id=provider_id)
	
	try:
		# Import audio generator
		pipeline_dir = os.path.join(settings.BASE_DIR.parent, 'pipeline')
		sys.path.insert(0, pipeline_dir)
		from scripts.audio_generator import AudioGenerator
		
		# Try to initialize the provider
		generator = AudioGenerator(
			provider=provider.provider_type,
			server_url=provider.server_url,
			sample_rate=provider.sample_rate
		)
		
		# Update provider status
		provider.last_tested = timezone.now()
		
		# Check if provider initialized successfully
		if provider.provider_type == 'pyttsx3':
			if generator.pyttsx3_engine:
				provider.last_test_success = True
				provider.last_test_message = "pyttsx3 engine initialized successfully"
			else:
				provider.last_test_success = False
				provider.last_test_message = "Failed to initialize pyttsx3 engine"
		elif provider.provider_type == 'edge-tts':
			# Test edge-tts by importing and checking
			try:
				import edge_tts
				provider.last_test_success = True
				provider.last_test_message = "Edge TTS ready - using Microsoft neural voices (requires internet)"
			except ImportError:
				provider.last_test_success = False
				provider.last_test_message = "edge-tts not installed. Run: pip install edge-tts"
		elif provider.provider_type == 'gtts':
			# gTTS doesn't need initialization, just internet
			provider.last_test_success = True
			provider.last_test_message = "Google TTS ready (requires internet)"
		elif provider.provider_type == 'personaplex':
			if generator.personaplex_client:
				provider.last_test_success = True
				provider.last_test_message = f"PersonaPlex configured at {provider.server_url}"
			else:
				provider.last_test_success = False
				provider.last_test_message = "PersonaPlex not initialized - check server URL and HF_TOKEN"
		elif provider.provider_type == 'riva':
			if generator.tts_service:
				provider.last_test_success = True
				provider.last_test_message = f"Connected to Riva at {provider.server_url}"
			else:
				provider.last_test_success = False
				provider.last_test_message = "Failed to connect to Riva server"
		elif provider.provider_type == 'xtts':
			# Test XTTS by checking if TTS library is available
			try:
				from TTS.api import TTS
				if generator.xtts_model:
					provider.last_test_success = True
					provider.last_test_message = "Coqui XTTS v2 model loaded and ready"
				else:
					provider.last_test_success = True
					provider.last_test_message = "Coqui XTTS ready - model will download (~2GB) on first use"
			except ImportError:
				provider.last_test_success = False
				provider.last_test_message = "TTS not installed. Run: pip install TTS"
		elif provider.provider_type == 'piper':
			# Test Piper TTS
			try:
				import piper
				provider.last_test_success = True
				provider.last_test_message = "Piper TTS ready - fast offline synthesis"
			except ImportError:
				provider.last_test_success = False
				provider.last_test_message = "Piper not installed. Run: pip install piper-tts"
		else:
			provider.last_test_success = False
			provider.last_test_message = f"Unknown provider type: {provider.provider_type}"
		
		provider.save()
		
		return JsonResponse({
			'success': provider.last_test_success,
			'message': provider.last_test_message,
		})
		
	except Exception as e:
		provider.last_tested = timezone.now()
		provider.last_test_success = False
		provider.last_test_message = f"Error: {str(e)}"
		provider.save()
		
		return JsonResponse({
			'success': False,
			'message': str(e),
		})


# ==================== Annotation Planning Views ====================

def annotation_planning(request, book_id):
    """Annotation planning page - preview theme, discuss approach with AI"""
    book = get_object_or_404(Book, id=book_id)
    
    # Get available AI providers
    providers = AIProvider.objects.filter(is_active=True, last_test_success=True)
    primary_provider = providers.filter(is_primary=True).first() or providers.first()
    
    # Get all available models across providers
    all_models = []
    for provider in providers:
        models = provider.get_available_models_list()
        for model in models:
            all_models.append({
                'name': model,
                'provider': provider.name,
                'provider_id': provider.id,
                'is_preferred': 'qwen' in model.lower()
            })
    
    # Sort to put qwen models first
    all_models.sort(key=lambda x: (not x['is_preferred'], x['name']))
    
    # Get conversation history
    conversation = book.get_conversation_history()
    
    # Read a sample from the manuscript for preview
    sample_text = ""
    if book.manuscript_path:
        manuscript_path = os.path.join(PIPELINE_DIR, book.manuscript_path) if not os.path.isabs(book.manuscript_path) else book.manuscript_path
        if os.path.exists(manuscript_path):
            try:
                with open(manuscript_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Get a meaningful sample (skip headers, find some actual content)
                    lines = content.split('\n')
                    start_idx = 0
                    for i, line in enumerate(lines):
                        if line.strip() and len(line.strip()) > 50 and not line.strip().startswith(('Title:', 'Author:', 'CHAPTER', 'THE PROJECT')):
                            start_idx = i
                            break
                    sample_text = '\n'.join(lines[start_idx:start_idx+10])[:500]
            except Exception as e:
                sample_text = f"Error reading manuscript: {e}"
    
    return render(request, "books/annotation_planning.html", {
        "book": book,
        "providers": providers,
        "primary_provider": primary_provider,
        "all_models": all_models,
        "conversation": conversation,
        "sample_text": sample_text,
    })


@require_http_methods(["POST"])
def annotation_generate_approach(request, book_id):
    """Generate an annotation approach/plan for a book"""
    book = get_object_or_404(Book, id=book_id)
    
    # Get the primary provider
    provider = AIProvider.objects.filter(is_active=True, is_primary=True).first()
    if not provider:
        provider = AIProvider.objects.filter(is_active=True, last_test_success=True).first()
    
    if not provider:
        return JsonResponse({'error': 'No AI provider configured'}, status=400)
    
    # Read manuscript sample
    manuscript_path = os.path.join(PIPELINE_DIR, book.manuscript_path) if not os.path.isabs(book.manuscript_path) else book.manuscript_path
    sample_text = ""
    if os.path.exists(manuscript_path):
        with open(manuscript_path, 'r', encoding='utf-8') as f:
            content = f.read()
            sample_text = content[:3000]  # First 3000 chars for analysis
    
    # Build the prompt for approach generation
    prompt = f"""You are the press's literary annotator.

You're about to annotate a book:
- Title: {book.title}
- Author: {book.author}

Here's a sample of the text:
---
{sample_text}
---

Based on this sample, describe your planned annotation approach in a conversational way:
1. What themes and topics do you see that are worth commenting on?
2. What kind of humor/tone will work best for this text?
3. What historical or scientific context might be relevant?
4. What's your overall strategy for this book?

Keep it friendly and conversational - you're explaining to the editor what you plan to do.
Address them directly as if having a planning meeting.
Be specific about THIS book, not generic."""

    try:
        # Use the preferred model if set, otherwise let the provider decide
        model = book.preferred_model or provider.default_model
        
        response = provider.generate_text(prompt, model=model)
        
        # Save the approach
        book.annotation_approach = response
        book.save()
        
        # Add to conversation
        book.add_to_conversation('assistant', response)
        
        return JsonResponse({
            'success': True,
            'approach': response,
            'model_used': model,
            'provider': provider.name
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def annotation_chat(request, book_id):
    """Chat with the AI about the annotation approach"""
    book = get_object_or_404(Book, id=book_id)
    
    # Get user message
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
    except:
        user_message = request.POST.get('message', '').strip()
    
    if not user_message:
        return JsonResponse({'error': 'No message provided'}, status=400)
    
    # Get the primary provider
    provider = AIProvider.objects.filter(is_active=True, is_primary=True).first()
    if not provider:
        provider = AIProvider.objects.filter(is_active=True, last_test_success=True).first()
    
    if not provider:
        return JsonResponse({'error': 'No AI provider configured'}, status=400)
    
    # Add user message to conversation
    book.add_to_conversation('user', user_message)
    
    # Build conversation context
    history = book.get_conversation_history()
    conversation_text = ""
    for msg in history[-10:]:  # Last 10 messages for context
        role = "Human" if msg['role'] == 'user' else "Annotator"
        conversation_text += f"{role}: {msg['content']}\n\n"
    
    prompt = f"""You are the press's literary annotator.

You're in a planning conversation about annotating "{book.title}" by {book.author}.

Your current approach plan:
{book.annotation_approach or 'Not yet defined.'}

Conversation so far:
{conversation_text}

Continue the conversation naturally. If the human gives you specific instructions or feedback,
acknowledge it and explain how you'll incorporate it. If they ask questions, answer helpfully.
Stay in character as the annotator - witty, knowledgeable, but conversational.

Respond only with your next message in the conversation (no meta-commentary)."""

    try:
        model = book.preferred_model or provider.default_model
        response = provider.generate_text(prompt, model=model)
        
        # Add assistant response to conversation
        book.add_to_conversation('assistant', response)
        
        return JsonResponse({
            'success': True,
            'response': response,
            'model_used': model
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def annotation_preview_sample(request, book_id):
    """Generate a sample annotation to preview the theme/style"""
    book = get_object_or_404(Book, id=book_id)
    
    # Get the primary provider
    provider = AIProvider.objects.filter(is_active=True, is_primary=True).first()
    if not provider:
        provider = AIProvider.objects.filter(is_active=True, last_test_success=True).first()
    
    if not provider:
        return JsonResponse({'error': 'No AI provider configured'}, status=400)
    
    # Read a sample passage from the manuscript
    manuscript_path = os.path.join(PIPELINE_DIR, book.manuscript_path) if not os.path.isabs(book.manuscript_path) else book.manuscript_path
    sample_text = ""
    if os.path.exists(manuscript_path):
        with open(manuscript_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find a good representative passage
            lines = content.split('\n')
            # Skip headers and find actual content
            start_idx = 0
            for i, line in enumerate(lines):
                if line.strip() and len(line.strip()) > 80 and not line.strip().startswith(('Title:', 'Author:', 'CHAPTER', 'THE PROJECT', '***')):
                    start_idx = i
                    break
            sample_text = '\n'.join(lines[start_idx:start_idx+5])[:400]
    
    if not sample_text:
        return JsonResponse({'error': 'Could not read manuscript sample'}, status=400)
    
    # Build annotation prompt with any custom instructions
    custom_instructions = ""
    if book.annotation_instructions:
        custom_instructions = f"\n\nAdditional instructions from the editor:\n{book.annotation_instructions}"
    
    prompt = f"""You are the press's witty annotator for classic science fiction.

Your style: SHORT, FUNNY, and insightful. Think dry wit meets scholarly observation.
{custom_instructions}

For this text, provide commentary in this EXACT format:

1. **Annotator says**: Your pithy, humorous one-liner reaction (1 sentence max, be funny!)
2. ONE of these (pick the most relevant, 1-2 sentences with a touch of wit):
   • **Science Note**: Amusing observation about the science (accurate or hilariously wrong)
   • **Context Note**: Historical tidbit with a wry twist
   • **Futurist Note**: Tongue-in-cheek modern relevance
   • **Humanist Note**: Self-aware insight about human nature

KEEP IT SHORT. Be clever, not verbose. Wit over length.

Text:
{sample_text}

Your annotation:"""

    try:
        model = book.preferred_model or provider.default_model
        response = provider.generate_text(prompt, model=model)
        
        return JsonResponse({
            'success': True,
            'sample_text': sample_text,
            'annotation': response,
            'model_used': model
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def annotation_save_instructions(request, book_id):
    """Save custom annotation instructions"""
    book = get_object_or_404(Book, id=book_id)
    
    try:
        data = json.loads(request.body)
    except:
        data = request.POST
    
    # Save the instructions
    book.annotation_instructions = data.get('instructions', '')
    book.preferred_model = data.get('preferred_model', '')
    book.planning_completed = data.get('planning_completed', False)
    book.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Instructions saved'
    })


@require_http_methods(["POST"])
def annotation_clear_conversation(request, book_id):
    """Clear the annotation planning conversation"""
    book = get_object_or_404(Book, id=book_id)
    book.annotation_conversation = '[]'
    book.save()
    
    return JsonResponse({'success': True})


def ai_discover_models(request):
    """API endpoint to discover all available models across all providers"""
    providers = AIProvider.objects.filter(is_active=True)
    
    all_models = []
    errors = []
    
    for provider in providers:
        try:
            # Test/refresh the connection to get current models
            success, message = provider.test_connection()
            
            if success:
                models = provider.get_available_models_list()
                for model in models:
                    all_models.append({
                        'name': model,
                        'provider': provider.name,
                        'provider_id': provider.id,
                        'provider_type': provider.provider_type,
                        'is_qwen': 'qwen' in model.lower(),
                        'is_llama': 'llama' in model.lower(),
                        'is_mistral': 'mistral' in model.lower(),
                    })
            else:
                errors.append({'provider': provider.name, 'error': message})
        except Exception as e:
            errors.append({'provider': provider.name, 'error': str(e)})
    
    # Sort: qwen first, then llama, then others
    def model_sort_key(m):
        if m['is_qwen']:
            return (0, m['name'])
        elif m['is_llama']:
            return (1, m['name'])
        else:
            return (2, m['name'])
    
    all_models.sort(key=model_sort_key)
    
    return JsonResponse({
        'models': all_models,
        'errors': errors,
        'provider_count': providers.count(),
        'model_count': len(all_models)
    })


# ==================== Audio Asset Management Views ====================

def audio_assets(request):
	"""Manage audio assets (bumpers, outros, legal disclaimers)"""
	assets = AudioAsset.objects.all().order_by('asset_type', 'name')
	bumpers = assets.filter(asset_type='bumper')
	outros = assets.filter(asset_type='outro')
	legals = assets.filter(asset_type='legal')
	transitions = assets.filter(asset_type='transition')
	effects = assets.filter(asset_type='effect')
	
	return render(request, "books/audio_assets.html", {
		"assets": assets,
		"bumpers": bumpers,
		"outros": outros,
		"legals": legals,
		"transitions": transitions,
		"effects": effects,
	})


@csrf_exempt
@require_http_methods(["POST"])
def audio_asset_create(request):
	"""Create an audio asset from uploaded file or TTS text"""
	name = request.POST.get('name')
	asset_type = request.POST.get('asset_type', 'bumper')
	description = request.POST.get('description', '')
	source_text = request.POST.get('source_text', '')
	
	if not name:
		return JsonResponse({'error': 'Name is required'}, status=400)
	
	# Check if file was uploaded
	uploaded_file = request.FILES.get('audio_file')
	
	asset = AudioAsset(
		name=name,
		asset_type=asset_type,
		description=description,
		source_text=source_text,
	)
	
	if uploaded_file:
		asset.audio_file = uploaded_file
	
	asset.save()
	
	# Get file metadata if available
	if asset.get_audio_path() and os.path.exists(asset.get_audio_path()):
		asset.file_size = os.path.getsize(asset.get_audio_path())
		try:
			import wave
			with wave.open(asset.get_audio_path(), 'rb') as wav:
				frames = wav.getnframes()
				rate = wav.getframerate()
				asset.duration_seconds = frames / float(rate)
				asset.sample_rate = rate
		except:
			pass
		asset.save()
	
	return JsonResponse({
		'success': True,
		'id': asset.id,
		'name': asset.name,
	})


@csrf_exempt
@require_http_methods(["POST"])
def audio_asset_delete(request, asset_id):
	"""Delete an audio asset"""
	asset = get_object_or_404(AudioAsset, id=asset_id)
	asset.delete()
	return JsonResponse({'success': True})


@csrf_exempt
@require_http_methods(["POST"])
def generate_audio_file(request):
	"""Generate downloadable audio file from text using TTS"""
	voice_id = request.POST.get('voice_id')
	sample_text = request.POST.get('sample_text', '')
	provider_id = request.POST.get('provider_id')
	filename = request.POST.get('filename', 'audio')
	output_format = request.POST.get('format', 'wav')  # wav or mp3
	
	if not sample_text:
		return JsonResponse({'error': 'Text is required'}, status=400)
	
	# Get voice profile
	voice = None
	if voice_id:
		try:
			voice = VoiceProfile.objects.get(id=voice_id)
		except VoiceProfile.DoesNotExist:
			pass
	
	# Get TTS provider
	provider = None
	if provider_id:
		try:
			provider = TTSProvider.objects.get(id=provider_id)
		except TTSProvider.DoesNotExist:
			pass
	
	if not provider:
		provider = TTSProvider.objects.filter(is_primary=True, is_active=True).first()
	
	if not provider:
		return JsonResponse({'error': 'No TTS provider configured'}, status=400)
	
	try:
		# Import audio generator
		pipeline_dir = os.path.join(settings.BASE_DIR.parent, 'pipeline')
		sys.path.insert(0, pipeline_dir)
		from scripts.audio_generator import AudioGenerator, VoiceConfig
		
		# Create generator
		generator = AudioGenerator(
			provider=provider.provider_type,
			server_url=provider.server_url,
			sample_rate=provider.sample_rate
		)
		
		# Create voice config
		if voice:
			voice_config = VoiceConfig(
				name=voice.name,
				voice_id=voice.voice_id or '',
				pitch=voice.pitch,
				speed=voice.speed,
				tone=voice.tone,
				description=voice.description,
				persona_text=voice.persona_text,
			)
		else:
			voice_config = VoiceConfig(
				name='Default',
				voice_id='',
				pitch=1.0,
				speed=1.0,
				tone='neutral',
			)
		
		# Generate audio
		audio_data = generator.synthesize_text(sample_text, voice_config)
		
		# Convert to MP3 if requested and ffmpeg is available
		if output_format == 'mp3':
			try:
				import tempfile
				import subprocess
				
				# Write WAV to temp file
				with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_tmp:
					wav_tmp.write(audio_data)
					wav_path = wav_tmp.name
				
				mp3_path = wav_path.replace('.wav', '.mp3')
				
				# Convert WAV to MP3
				result = subprocess.run([
					'ffmpeg', '-y', '-i', wav_path,
					'-codec:a', 'libmp3lame', '-qscale:a', '2',
					mp3_path
				], capture_output=True)
				
				if result.returncode == 0 and os.path.exists(mp3_path):
					with open(mp3_path, 'rb') as f:
						audio_data = f.read()
					os.unlink(mp3_path)
				os.unlink(wav_path)
			except:
				output_format = 'wav'  # Fall back to WAV
		
		# Clean filename
		safe_filename = "".join(c for c in filename if c.isalnum() or c in '._- ').strip()
		safe_filename = safe_filename or 'audio'
		
		# Return as downloadable file
		content_type = 'audio/mpeg' if output_format == 'mp3' else 'audio/wav'
		ext = '.mp3' if output_format == 'mp3' else '.wav'
		
		response = HttpResponse(audio_data, content_type=content_type)
		response['Content-Disposition'] = f'attachment; filename="{safe_filename}{ext}"'
		return response
		
	except Exception as e:
		return JsonResponse({'error': str(e)}, status=500)


def audio_asset_download(request, asset_id):
	"""Download an audio asset file"""
	asset = get_object_or_404(AudioAsset, id=asset_id)
	
	audio_path = asset.get_audio_path()
	if not audio_path or not os.path.exists(audio_path):
		return JsonResponse({'error': 'Audio file not found'}, status=404)
	
	# Determine content type
	ext = os.path.splitext(audio_path)[1].lower()
	content_type = 'audio/mpeg' if ext == '.mp3' else 'audio/wav'
	
	response = FileResponse(
		open(audio_path, 'rb'),
		content_type=content_type
	)
	filename = f"{asset.name}{ext}"
	response['Content-Disposition'] = f'attachment; filename="{filename}"'
	return response
