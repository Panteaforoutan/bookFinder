"""Classify a book into bookstore sections by title.

Pipeline: look up the book's description via the Google Books API
(`fetch_description`) -> build a classification prompt listing the
bookstore's categories (`build_prompt`) -> ask Gemini to pick the best-fit
categories (`classify_book`) -> return the result (`classifier`).
"""

import argparse
import json
import os

from dotenv import load_dotenv
from google import genai
from googleapiclient.discovery import build
from models import Book

from categories import BN_CATEGORIES

load_dotenv()  # reads .env in your project root and loads it into the environment

BOOKS_API_KEY = os.environ["BOOKS_API_KEY"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_MODEL = "gemini-3.6-flash"


TITLE_MATCH_THRESHOLD = 0.5


def containment(query, title):
    """Fraction of `query`'s words that also appear in `title`.

    Unlike Jaccard similarity, this doesn't penalize `title` for having
    extra words beyond `query` (e.g. a subtitle), which matters since
    Google Books often returns a fuller canonical title than what the
    user typed.

    Returns:
        Float in [0, 1]: |query_words & title_words| / |query_words|.
        Returns 0.0 if `query` has no words.
    """
    query_words = set(query.lower().split())
    title_words = set(title.lower().split())
    if not query_words:
        return 0.0
    return len(query_words & title_words) / len(query_words)


def fetch_description(books_service, title):
    """Look up a book by title via the Google Books API.

    Returns:
        A Book with title/author/description populated from the top
        match, or with author and description left as None if no
        match was found or the top match's title doesn't sufficiently
        overlap with the query (title falls back to the input query).
    """
    request = books_service.volumes().list(q=title, maxResults=1)
    response = request.execute()

    items = response.get("items", [])
    if not items:
        return Book(title=title, author=None, description=None)

    info = items[0]["volumeInfo"]
    result_title = info.get("title", title)

    if containment(title, result_title) < TITLE_MATCH_THRESHOLD:
        return Book(title=title, author=None, description=None)

    return Book(
        title=result_title,
        author=info.get("authors"),
        description=info.get("description"),
    )


def build_prompt(title, description, categories):
    """Build the classification prompt for a book against the given category list."""
    categories_str = "\n".join(f"- {c}" for c in categories)
    return f"""You are classifying a book into sections used by a physical bookstore (Barnes & Noble).

        Book title: {title}
        Book description: {description}

        Available categories:
        {categories_str}

        Based on the title and description, pick the top 2-3 categories from the list above that this book is most likely shelved under. Some books genuinely fit multiple sections (e.g. a memoir about grief could be Self-Help, Psychology, or Spirituality) — it's fine and expected to return more than one.

        Respond ONLY with valid JSON in this exact format, no other text:
        {{
        "categories": [
            {{"category": "<exact category name from the list>", "reason": "<one short sentence>"}},
            ...
        ]
        }}
    """


def classify_book(genai_client, prompt):
    """Send a classification prompt to Gemini and return the parsed categories list."""
    interaction = genai_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    raw_text = interaction.text.strip()

    # Models sometimes wrap JSON in markdown code fences despite instructions not to —
    # strip those off if present
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = raw_text.removeprefix("json").strip()

    result = json.loads(raw_text)
    return result["categories"]


def print_categories(categories):
    """Print each category entry as "<category> - <reason>", one per line.

    Args:
        categories: List of dicts with "category" and "reason" keys, as
            returned by `classify_book()`.
    """
    for entry in categories:
        print(entry["category"], "-", entry["reason"])


def classifier(title, author=""):
    """Classify a book into bookstore categories by title and author.

    Looks up the book's description via the Google Books API, then asks
    Gemini to pick the top matching categories from BN_CATEGORIES.

    Args:
        title: Book title to search for.
        author: Book author. Unused — the returned "author" comes from
            the Google Books lookup instead.

    Returns:
        Dict with "title", "author", and "categories" (the list of
        {"category", "reason"} dicts returned by `classify_book()`).
        If no Google Books match was found, "categories" is an empty
        list and a "message" key explains that the book wasn't found.
    """
    books_service = build("books", "v1", developerKey=BOOKS_API_KEY)
    book = fetch_description(books_service, title)

    if book.description is None:
        return {
            "title": book.title,
            "author": book.author,
            "categories": [],
            "message": f"Book '{book.title}' not found.",
        }

    genai_client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = build_prompt(book.title, book.description, BN_CATEGORIES)
    book.categories = classify_book(genai_client, prompt)
    

    return {
        "title": book.title,
        "author": book.author,
        "categories": book.categories,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Locate a book in a bookstore")
    parser.add_argument("-b", "--bookname", nargs="+", help="Name of the book searching for")
    parser.add_argument("-w", "--author", nargs="+", help="Book author to search for")
    args = parser.parse_args()
    result = classifier(" ".join(args.bookname), " ".join(args.author))
    print_categories(result["categories"])
