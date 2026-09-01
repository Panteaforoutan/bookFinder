import json
import os
from locate import localizer_events
from classify import classifier
from flask import Flask, request, jsonify, Response, stream_with_context
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/classify", methods=["POST"])
def classify_endpoint():
    """POST /classify: classify a book into bookstore categories.

    Expects a JSON body with a "title" field and an optional "author" field.

    Returns:
        JSON {"result": <classifier() output>}, or
        JSON {"error": <str>}, 400 if "title" is missing or blank.
    """
    data = request.get_json()
    title = (data.get("title") or "").strip()
    author = data.get("author", "")

    if not title:
        return jsonify({"error": "Missing title"}), 400

    result = classifier(title, author)
    return jsonify({"result": result})
    
    
@app.route("/locate", methods=["POST"])
def localize_endpoint():
    """POST /locate: find a book's location in an uploaded shelf photo.

    Expects multipart form data with an "image" file and a "query" field
    (the book title/author to search for). Saves the upload to uploads/
    before running localization.

    Streams newline-delimited JSON as the pipeline progresses:
        {"stage": <str>} after each pipeline step, then finally
        {"done": true, "result": <localizer() output>}.
    On a validation failure (before streaming starts), returns a plain
    JSON {"error": <str>}, 400 instead.
    """
    image_file = request.files.get("image")
    query = request.form.get("query")

    if image_file is None or query is None:
        return jsonify({"error": "Missing image or query"}), 400

    filename = secure_filename(image_file.filename)

    if not image_file.content_type.startswith("image/"):
        return jsonify({"error": "Uploaded file is not an image"}), 400

    temp_path = os.path.join("uploads", filename) #uploads needs to already exist
    image_file.save(temp_path)

    def generate():
        for event in localizer_events(temp_path, query):
            yield json.dumps(event) + "\n"

    return Response(stream_with_context(generate()), mimetype="application/x-ndjson")

# This line is optional convention 
# if __name__ == "__main__": -> "was this file executed directly, or was it imported by something else?"
# __name__ is a special variable Python sets automatically:
# it equals "__main__" when the file is run directly, but 
# equals the modules name (e.g. "app") when the file is 
# imported by another file. 
# That if block just means "only start the server when
# I run this file directly — don't start it if someone 
# else imports app from this module
if __name__ == "__main__":
    # this is the actual call that starts the server loop. It has to be invoked somewhere
    app.run(debug=True, port=5001)
    
# curl (Client URL)
# curl -X POST http://127.0.0.1:5001/classify \
#   -H "Content-Type: application/json" \
#   -d '{"title": "Dune", "author": "Frank Herbert"}'

# curl -X POST http://127.0.0.1:5001/localize \
#   -H "Content-Type: application/json" \
#   -d '{"img_path": "shelf.png" ,"title": "Tom Lake"}'

# curl -X POST http://127.0.0.1:5001/localize \
#   -F "image=@shelf.png" \
#   -F "query=Tom Lake"