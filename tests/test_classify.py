from unittest.mock import MagicMock

import pytest

import classify

#python -m pytest tests/test_classify.py -v


def test_fetch_description_returns_book_from_top_match():
    fake_response = {
        "items": [
            {
                "volumeInfo": {
                    "title": "Tom Lake",
                    "authors": ["Ann Patchett"],
                    "description": "A story about a summer romance.",
                }
            }
        ]
    }
    fake_books_service = MagicMock()
    fake_books_service.volumes.return_value.list.return_value.execute.return_value = fake_response

    book = classify.fetch_description(fake_books_service, "Tom Lake")

    assert book.title == "Tom Lake"
    assert book.author == ["Ann Patchett"]
    assert book.description == "A story about a summer romance."


def test_fetch_description_returns_none_fields_when_no_items():
    fake_books_service = MagicMock()
    fake_books_service.volumes.return_value.list.return_value.execute.return_value = {"items": []}

    book = classify.fetch_description(fake_books_service, "Nonexistent Book")

    assert book.title == "Nonexistent Book"
    assert book.author is None
    assert book.description is None


def test_fetch_description_falls_back_to_query_title_when_missing():
    fake_response = {"items": [{"volumeInfo": {}}]}
    fake_books_service = MagicMock()
    fake_books_service.volumes.return_value.list.return_value.execute.return_value = fake_response

    book = classify.fetch_description(fake_books_service, "Tom Lake")

    assert book.title == "Tom Lake"
    assert book.author is None
    assert book.description is None


def test_build_prompt_includes_title_description_and_categories():
    prompt = classify.build_prompt("Dune", "A desert planet epic.", ["Science Fiction & Fantasy", "Poetry"])

    assert "Dune" in prompt
    assert "A desert planet epic." in prompt
    assert "- Science Fiction & Fantasy" in prompt
    assert "- Poetry" in prompt


def test_classify_book_parses_plain_json():
    fake_genai_client = MagicMock()
    fake_genai_client.models.generate_content.return_value.text = (
        '{"categories": [{"category": "Science Fiction & Fantasy", "reason": "Set on another planet."}]}'
    )

    categories = classify.classify_book(fake_genai_client, "some prompt")

    assert categories == [{"category": "Science Fiction & Fantasy", "reason": "Set on another planet."}]


def test_classify_book_strips_markdown_code_fences():
    fake_genai_client = MagicMock()
    fake_genai_client.models.generate_content.return_value.text = (
        '```json\n{"categories": [{"category": "Mystery", "reason": "A whodunit."}]}\n```'
    )

    categories = classify.classify_book(fake_genai_client, "some prompt")

    assert categories == [{"category": "Mystery", "reason": "A whodunit."}]


def test_classifier_returns_categories_when_book_found(monkeypatch):
    fake_book = classify.Book(title="Tom Lake", author=["Ann Patchett"], description="A summer romance.")
    monkeypatch.setattr(classify, "build", lambda *args, **kwargs: MagicMock())
    monkeypatch.setattr(classify, "fetch_description", lambda books_service, title: fake_book)
    monkeypatch.setattr(classify.genai, "Client", lambda **kwargs: MagicMock())
    monkeypatch.setattr(
        classify, "classify_book",
        lambda genai_client, prompt: [{"category": "Literary Fiction", "reason": "A character-driven drama."}],
    )

    result = classify.classifier("Tom Lake")

    assert result == {
        "title": "Tom Lake",
        "author": ["Ann Patchett"],
        "categories": [{"category": "Literary Fiction", "reason": "A character-driven drama."}],
    }


def test_classifier_returns_message_when_book_not_found(monkeypatch):
    fake_book = classify.Book(title="Nonexistent Book", author=None, description=None)
    monkeypatch.setattr(classify, "build", lambda *args, **kwargs: MagicMock())
    monkeypatch.setattr(classify, "fetch_description", lambda books_service, title: fake_book)

    result = classify.classifier("Nonexistent Book")

    assert result == {
        "title": "Nonexistent Book",
        "author": None,
        "categories": [],
        "message": "Book 'Nonexistent Book' not found.",
    }
