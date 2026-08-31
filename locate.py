"""Locate a book by title in a photo of a bookshelf.

Pipeline: segment the shelf photo into individual book bounding boxes
(`segmentation`) -> crop and OCR each box to read its title (`OCR`) ->
fuzzy-match the search query against the recognized titles (`fuzzy_match`)
-> return the bounding box of the best match (`localizer`).
"""

import argparse
import base64
import os

from dotenv import load_dotenv
from inference_sdk import InferenceHTTPClient
from PIL import Image
from models import Book
import cv2

load_dotenv()  # reads .env in your project root and loads it into the environment

ROBOFLOW_API_KEY = os.environ["ROBOFLOW_API_KEY"]


def segmentation(img):
    """Run book segmentation on an image via the Roboflow workflow API.

    Args:
        img: Image source to segment (path, URL, or array) accepted by
            InferenceHTTPClient.run_workflow.

    Returns:
        Tuple of (predictions, annotated_image_b64):
            predictions: List of bounding-box predictions, one per detected book.
            annotated_image_b64: Base64-encoded JPEG of the input image with all
                detected books outlined, as returned by the workflow.
    """
    client = InferenceHTTPClient(
        api_url="https://serverless.roboflow.com",
        api_key=ROBOFLOW_API_KEY
    )

    raw_result = client.run_workflow(
        workspace_name="panteas-workspace",
        workflow_id="general-segmentation-api",
        images={"image": img},
        parameters={
            "classes": "book"
        },
        use_cache=True
    )
    result = raw_result[0]
    return result['predictions']['predictions'], result['annotated_image']


def save_annotated_image(annotated_image_b64, img_path):
    """Decode the workflow's annotated image and save it next to the source image.

    Args:
        annotated_image_b64: Base64-encoded JPEG string returned by `segmentation()`.
        img_path: Path to the original shelf image; the annotated copy is saved
            alongside it with a "_segmented.jpg" suffix.

    Returns:
        Path the annotated image was saved to.
    """
    root, _ = os.path.splitext(img_path)
    out_path = f"{root}_segmented.jpg"
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(annotated_image_b64))
    return out_path


def crop_book(img, boundary):
    """Crop a book region out of the shelf image and rotate it upright for OCR.

    Args:
        img: PIL Image of the full shelf photo.
        boundary: (left, top, right, bottom) tuple bounding the book.

    Returns:
        PIL Image of the cropped region, rotated 90 degrees if the book
        is standing upright (its spine text would otherwise run vertically).
    """
    left, top, right, bottom = boundary
    crop = img.crop(boundary)
    if (bottom - top) > (right - left):
        # Book is standing upright (taller than wide), so its spine
        # text runs vertically - rotate to make it horizontal for OCR.
        crop = crop.transpose(Image.Transpose.ROTATE_90)
    return crop


def OCR(img, detections):
    """Crop each detected book from the image and run OCR to read its title.

    For every prediction in `segmentations`, crops the corresponding region
    out of `img`, rotates it 90 degrees (books are typically photographed
    lying on their side), and sends the crop to the Roboflow OCR workflow
    to recognize the title text.

    Args:
        img: Path to the source image file.
        segmentations: Result returned by `segmentation()`, containing
            book bounding-box predictions at
            segmentations[0]['predictions']['predictions'].

    Returns:
        Tuple of (titles, boundaries):
            titles: List of recognized title text strings, one per
                detected book, in the same order as the input predictions.
            boundaries: List of (left, top, right, bottom) tuples, the
                crop region used for the corresponding book.
    """
    client = InferenceHTTPClient(
        api_url="https://serverless.roboflow.com",
        api_key=ROBOFLOW_API_KEY
    )

    img = Image.open(img)
    titles= []
    boundaries = []
    

    for _, pred in enumerate(detections):
        x, y, w, h = pred['x'], pred['y'], pred['width'], pred['height']
        left, top = x - w/2, y - h/2
        right, bottom = x + w/2, y + h/2
        boundaries.append((left, top, right, bottom))

        crop = crop_book(img, (left, top, right, bottom))

        ocr_result = client.run_workflow(
            workspace_name="panteas-workspace",
            workflow_id="doctr-demo-2",
            images={"image": crop},
            use_cache=False
        )
        titles.append(ocr_result[0]["recognized_text"])
        
        
    return titles, boundaries 
    

def jaccard(a, b):
    """Compute the Jaccard similarity between two strings' word sets.

    Args:
        a: First string.
        b: Second string.

    Returns:
        Float in [0, 1]: the size of the intersection of the strings'
        lowercased word sets divided by the size of their union. Returns
        0.0 if either string has no words.
    """
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def fuzzy_match(query, titles):
    """Find the title in `titles` most similar to `query`.

    Scores every title against the query using Jaccard word-set similarity
    and returns the index of the best match.

    Args:
        query: The search string (e.g. a book title typed by the user).
        titles: List of candidate title strings, such as those returned
            by `OCR()`.

    Returns:
        Index into `titles` of the entry with the highest Jaccard score,
        or None if no title shares any words with the query.
    """
    scores = []
    for i in titles:
        score = jaccard(i, query)
        scores.append(score)

    if not scores or max(scores) == 0.0:
        return None

    return scores.index(max(scores))


def draw_boundary(img_path, boundaries):
    """Draw a red rectangle around one detected book and display it.

    Args:
        img: Path to the source image file.
        book_index: Index into `boundaries` of the book to highlight.
        boundaries: List of (left, top, right, bottom) bounding boxes,
            one per detected book.
        query: Search string, used as the title of the display window.

    Side effects:
        Opens a window showing the annotated image and blocks until a
        key is pressed, then closes the window. Nothing is saved to disk.
    """
    image = cv2.imread(img_path)

    # Define coordinates: top-left (x1, y1) and bottom-right (x2, y2)
    x1, y1, x2, y2 = boundaries
    top_left = (x1, y1)
    bottom_right = (x2, y2)

    # Draw a red rectangle boundary (Color format is BGR: Blue, Green, Red)
    cv2.rectangle(image, top_left, bottom_right, (0, 0, 255), 3)
    
    cv2.imshow("found!", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# returns structured data which means a Python dict with clearly labeled fields, e.g.:{"found": True, "box": [120, 340, 260, 480]}
def localizer(img_path, query):
    """Locate a book matching `query` in a shelf photo and return its bounding box.

    Runs segmentation to detect books, OCR to read each title, then fuzzy
    matches `query` against the recognized titles.

    Args:
        img_path: Path to the shelf image file.
        query: Search string (e.g. a book title) to look for.

    Returns:
        Dict with either:
            {"found": True, "box": [left, top, right, bottom]} on a match, or
            {"found": False, "message": <str>} if no title matched.
        Either way, an annotated copy of `img_path` showing every detected
        book is saved alongside it (see `save_annotated_image`).
    """
    segmentations, annotated_image_b64 = segmentation(img_path)
    save_annotated_image(annotated_image_b64, img_path)
    titles, boundaries = OCR(img_path, segmentations)
    book_index = fuzzy_match(query, titles)
    if book_index is None:
        return {"found": False, "message": f"No match found for '{query}'."}
    box = [int(v) for v in boundaries[book_index]]
    return {"found": True, "box": box}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Locate a book by title in a photo of a bookshelf.")
    parser.add_argument("img_path", help="Path to the shelf image")
    parser.add_argument("query", nargs="+", help="Book name and/or author to search for")
    args = parser.parse_args()
    coordinates = localizer(args.img_path, " ".join(args.query))
    if coordinates['found']:
        draw_boundary(args.img_path, coordinates['box'])
    else: 
        print("Not found")