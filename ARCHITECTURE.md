# Architecture

Compact reference for BookFinder. Update this table whenever an endpoint or file is added, removed, or changes purpose.

## Endpoints (app.py)

| Method | Path        | Handler            | Request                                      | Response                                                        |
|--------|-------------|---------------------|-----------------------------------------------|-------------------------------------------------------------------|
| POST   | `/classify` | `classify_endpoint` | JSON `{title, author}`                        | `{"result": {title, author, categories}}`                        |
| POST   | `/locate`   | `localize_endpoint` | multipart form `image` (file) + `query` (str)  | `{"result": {found, box}}` or `400 {"error": ...}`               |

## Files

| File                  | Purpose                                                                              |
|------------------------|---------------------------------------------------------------------------------------|
| `app.py`               | Flask app; defines the HTTP endpoints above, delegates to `classify.py`/`locate.py`  |
| `locate.py`            | Finds a book's position in a shelf photo: segmentation → OCR → fuzzy title match      |
| `classify.py`          | Classifies a book into bookstore categories using Google Books + Gemini              |
| `models.py`            | `Book` data class (title, author, categories, description, boundary_box)             |
| `categories.py`        | `BN_CATEGORIES` — list of bookstore category names used by `classify.py`             |
| `bookfinder-ui/`       | React (Vite) frontend that calls the `/classify` and `/locate` endpoints             |
| `tests/`               | `test_section_classifier.py`, `test_shelf_localizer.py`                              |

## Data flow

- **Classify**: `app.py` → `classify.classifier()` → Google Books API (description) → Gemini (`GEMINI_MODEL`) → categories list.
- **Locate**: `app.py` saves upload to `uploads/` → `locate.localizer()` → Roboflow segmentation workflow → per-crop Roboflow OCR workflow → Jaccard fuzzy match against `query` → bounding box.
