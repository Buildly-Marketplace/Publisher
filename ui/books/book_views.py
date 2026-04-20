"""Additional book management views"""
import os
import json
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from .models import Book

PIPELINE_DIR = os.path.join(settings.BASE_DIR, '..', 'pipeline')
MANUSCRIPTS_DIR = os.path.join(PIPELINE_DIR, 'manuscripts')
ANNOTATIONS_DIR = os.path.join(PIPELINE_DIR, 'annotations')


def book_create(request):
	"""Create a new book"""
	if request.method == "POST":
		title = request.POST.get("title", "").strip()
		author = request.POST.get("author", "").strip()
		manuscript = request.POST.get("manuscript", "").strip()
		
		if not title or not author:
			return render(request, "books/book_edit.html", {
				"error": "Title and author are required",
				"book": None,
			})
		
		# Generate slug
		slug = title.lower().replace(" ", "-").replace("_", "-")
		slug = "".join(c for c in slug if c.isalnum() or c == "-")
		
		# Create manuscript file
		manuscript_filename = f"{slug}.txt"
		manuscript_path = os.path.join(MANUSCRIPTS_DIR, manuscript_filename)
		with open(manuscript_path, "w", encoding="utf-8") as f:
			f.write(manuscript)
		
		# Create empty annotation file
		annotations_filename = f"{slug}_notes.json"
		annotations_path = os.path.join(ANNOTATIONS_DIR, annotations_filename)
		with open(annotations_path, "w", encoding="utf-8") as f:
			json.dump([], f)
		
		# Create book record
		book = Book.objects.create(
			title=title,
			author=author,
			slug=slug,
			manuscript_path=f"manuscripts/{manuscript_filename}",
			annotations_path=f"annotations/{annotations_filename}",
		)
		
		return redirect("book_edit", book_id=book.id)
	
	return render(request, "books/book_edit.html", {"book": None})


def book_edit(request, book_id):
	"""Edit book content, annotations, and cover"""
	book = get_object_or_404(Book, id=book_id)
	
	# Load manuscript
	manuscript_path = os.path.join(PIPELINE_DIR, book.manuscript_path)
	try:
		with open(manuscript_path, "r", encoding="utf-8") as f:
			manuscript = f.read()
	except Exception:
		manuscript = ""
	
	# Load annotations
	annotations_path = os.path.join(PIPELINE_DIR, book.annotations_path)
	try:
		with open(annotations_path, "r", encoding="utf-8") as f:
			annotations = f.read()
	except Exception:
		annotations = "[]"
	
	saved = False
	error = None
	
	if request.method == "POST":
		try:
			# Update title/author
			book.title = request.POST.get("title", book.title)
			book.author = request.POST.get("author", book.author)
			book.save()
			
			# Save manuscript
			new_manuscript = request.POST.get("manuscript", "")
			with open(manuscript_path, "w", encoding="utf-8") as f:
				f.write(new_manuscript)
			manuscript = new_manuscript
			
			# Save annotations
			new_annotations = request.POST.get("annotations", "")
			try:
				json.loads(new_annotations)  # Validate JSON
				with open(annotations_path, "w", encoding="utf-8") as f:
					f.write(new_annotations)
				annotations = new_annotations
			except json.JSONDecodeError:
				error = "Invalid JSON in annotations"
			
			# Handle cover upload
			if request.FILES.get("cover"):
				cover_file = request.FILES["cover"]
				cover_filename = f"{book.slug}_cover{os.path.splitext(cover_file.name)[1]}"
				cover_path = os.path.join(PIPELINE_DIR, "assets", cover_filename)
				os.makedirs(os.path.dirname(cover_path), exist_ok=True)
				with open(cover_path, "wb") as f:
					for chunk in cover_file.chunks():
						f.write(chunk)
				book.cover_path = f"assets/{cover_filename}"
				book.save()
			
			if not error:
				saved = True
		except Exception as e:
			error = str(e)
	
	return render(request, "books/book_edit.html", {
		"book": book,
		"manuscript": manuscript,
		"annotations": annotations,
		"saved": saved,
		"error": error,
	})


def book_preview(request, book_id):
	"""Preview book as HTML"""
	book = get_object_or_404(Book, id=book_id)
	
	# Load manuscript
	manuscript_path = os.path.join(PIPELINE_DIR, book.manuscript_path)
	try:
		with open(manuscript_path, "r", encoding="utf-8") as f:
			manuscript = f.read()
	except Exception:
		manuscript = "Error loading manuscript"
	
	# Load annotations
	annotations_path = os.path.join(PIPELINE_DIR, book.annotations_path)
	try:
		with open(annotations_path, "r", encoding="utf-8") as f:
			annotations_data = json.load(f)
	except Exception:
		annotations_data = []
	
	# Simple HTML formatting
	paragraphs = manuscript.split("\n\n")
	
	return render(request, "books/book_preview.html", {
		"book": book,
		"paragraphs": paragraphs,
		"annotations": annotations_data,
	})
