# BookFinder

Snap a photo of a bookshelf and find a specific book on it, or classify a book into a bookstore section by title/author.

- **Classify** — given a title (and optional author), fetches the description from Google Books and uses Gemini to assign bookstore categories.
- **Locate** — given a shelf photo and a title/author query, segments the shelf image, runs OCR on each book spine crop (via Roboflow), fuzzy-matches against the query, and returns a bounding box for the match.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the endpoint reference and file layout.

## Stack

- **Backend**: Flask (`app.py`), Google Books API + Gemini for classification, Roboflow (segmentation + OCR) for localization.
- **Frontend**: React + Vite ([bookfinder-ui/](bookfinder-ui/)).

## Setup

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root with:

```
BOOKS_API_KEY=...
GEMINI_API_KEY=...
ROBOFLOW_API_KEY=...
```

Make sure an `uploads/` directory exists (used to store shelf photos during `/locate`), then run the server:

```bash
python app.py
```

The API is served at `http://127.0.0.1:5001`.

### Frontend

```bash
cd bookfinder-ui
npm install
npm run dev
```

## Docker

```bash
docker build -t bookfinder .
docker run -p 5001:5001 --env-file .env bookfinder
```

## Tests

```bash
pytest
```
