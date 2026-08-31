from unittest.mock import MagicMock

import pytest
from PIL import Image

import locate

#python -m pytest tests/test_locate.py -v

def test_segmentation_returns_predictions_list(monkeypatch):
    fake_predictions = [{"x": 1, "y": 2, "width": 3, "height": 4}]
    fake_client = MagicMock()
    fake_client.run_workflow.return_value = [
        {
            "predictions": {"predictions": fake_predictions},
            "annotated_image": "fake_b64_image",
        }
    ]

    monkeypatch.setattr(locate, "InferenceHTTPClient", lambda **kwargs: fake_client)

    predictions, annotated_image_b64 = locate.segmentation("shelf.png")

    assert predictions == fake_predictions
    assert annotated_image_b64 == "fake_b64_image"


def test_crop_book_leaves_wide_book_unrotated():
    img = Image.new("RGB", (200, 200))
    boundary = (0, 0, 200, 50)  # right - left (200) > bottom - top (50)

    crop = locate.crop_book(img, boundary)

    assert crop.size == (200, 50)


def test_crop_book_rotates_tall_book():
    img = Image.new("RGB", (200, 200))
    boundary = (0, 0, 50, 200)  # bottom - top (200) > right - left (50)

    crop = locate.crop_book(img, boundary)

    # crop.size before rotation would be (50, 200); ROTATE_90 swaps width/height
    assert crop.size == (200, 50)


def test_ocr_crops_and_reads_each_detection(monkeypatch, tmp_path):
    img_path = tmp_path / "shelf.png"
    Image.new("RGB", (400, 400)).save(img_path)

    fake_client = MagicMock()
    fake_client.run_workflow.side_effect = [
        [{"recognized_text": "Tom Lake"}],
        [{"recognized_text": "Dune"}],
    ]
    monkeypatch.setattr(locate, "InferenceHTTPClient", lambda **kwargs: fake_client)

    detections = [
        {"x": 50, "y": 50, "width": 100, "height": 100},
        {"x": 200, "y": 200, "width": 100, "height": 100},
    ]

    titles, boundaries = locate.OCR(str(img_path), detections)

    assert titles == ["Tom Lake", "Dune"]
    assert boundaries == [(0.0, 0.0, 100.0, 100.0), (150.0, 150.0, 250.0, 250.0)]


def test_jaccard_identical_strings_score_one():
    assert locate.jaccard("Tom Lake", "Tom Lake") == 1.0


def test_jaccard_partial_overlap():
    # {"tom", "lake"} vs {"tom", "sawyer"} -> intersection 1, union 3
    assert locate.jaccard("Tom Lake", "Tom Sawyer") == pytest.approx(1 / 3)


def test_jaccard_no_overlap_scores_zero():
    assert locate.jaccard("Dune", "Beloved") == 0.0


def test_jaccard_empty_string_scores_zero():
    assert locate.jaccard("", "Dune") == 0.0
    assert locate.jaccard("Dune", "") == 0.0


def test_fuzzy_match_returns_index_of_best_match():
    titles = ["Tom Sawyer", "Tom Lake", "Beloved"]

    assert locate.fuzzy_match("Tom Lake", titles) == 1


def test_fuzzy_match_returns_none_when_no_title_overlaps():
    titles = ["Dune", "Beloved"]

    assert locate.fuzzy_match("Tom Lake", titles) is None


def test_fuzzy_match_returns_none_for_empty_titles():
    assert locate.fuzzy_match("Tom Lake", []) is None


def test_localizer_returns_box_when_match_found(monkeypatch):
    monkeypatch.setattr(locate, "segmentation", lambda img_path: ("fake detections", "fake_b64"))
    monkeypatch.setattr(locate, "save_annotated_image", lambda annotated_image_b64, img_path: None)
    monkeypatch.setattr(
        locate, "OCR",
        lambda img_path, detections: (
            ["Tom Sawyer", "Tom Lake"],
            [(0, 0, 10, 10), (5.4, 5.6, 15.2, 15.8)],
        ),
    )

    result = locate.localizer("shelf.png", "Tom Lake")

    # boundaries[1] is the exact match; box values are truncated to int
    assert result == {"found": True, "box": [5, 5, 15, 15]}


def test_localizer_returns_not_found_when_no_title_matches(monkeypatch):
    monkeypatch.setattr(locate, "segmentation", lambda img_path: ("fake detections", "fake_b64"))
    monkeypatch.setattr(locate, "save_annotated_image", lambda annotated_image_b64, img_path: None)
    monkeypatch.setattr(locate, "OCR", lambda img_path, detections: (["Beloved"], [(0, 0, 10, 10)]))

    result = locate.localizer("shelf.png", "Tom Lake")

    assert result == {"found": False, "message": "No match found for 'Tom Lake'."}
