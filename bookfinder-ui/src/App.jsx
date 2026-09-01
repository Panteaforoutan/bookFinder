import { useState, useEffect, useRef } from "react";
import "./App.css";

function boxStyle([left, top, right, bottom], { width, height }) {
  return {
    position: "absolute",
    left: `${(left / width) * 100}%`,
    top: `${(top / height) * 100}%`,
    width: `${((right - left) / width) * 100}%`,
    height: `${((bottom - top) / height) * 100}%`,
  };
}

function App() {
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [result, setResult] = useState(null);
  const [classifyError, setClassifyError] = useState("");

  const [image, setImage] = useState(null);
  const [imageUrl, setImageUrl] = useState(null);
  const [imageSize, setImageSize] = useState(null);
  const [query, setQuery] = useState("");
  const [locateResult, setLocateResult] = useState(null);
  const [locateError, setLocateError] = useState("");
  const [locateStage, setLocateStage] = useState("");
  const fileInputRef = useRef(null);

  function handleClear() {
    setImage(null);
    setImageSize(null);
    setLocateResult(null);
    setLocateError("");
    setLocateStage("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  useEffect(() => {
    if (!image) {
      setImageUrl(null);
      return;
    }
    const url = URL.createObjectURL(image);
    setImageUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [image]);

  async function handleSubmit() {
    if (!title.trim()) {
      setClassifyError("Please enter a title.");
      return;
    }
    setClassifyError("");
    setResult(null);

    try {
      const response = await fetch("http://127.0.0.1:5001/classify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, author }),
      });
      const data = await response.json();
      if (!response.ok) {
        setClassifyError(data.error || "Something went wrong.");
        return;
      }
      setResult(data);
    } catch {
      setClassifyError("Something went wrong. Please try again.");
    }
  }

  async function handleLocate() {
    setLocateError("");
    setLocateResult(null);
    setLocateStage("");

    const formData = new FormData();
    formData.append("image", image);
    formData.append("query", query);

    try {
      const response = await fetch("http://127.0.0.1:5001/locate", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        setLocateError(data.error || "Something went wrong.");
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // last entry may be an incomplete line

        for (const line of lines) {
          if (!line.trim()) continue;
          const event = JSON.parse(line);
          if (event.done) {
            setLocateResult({ result: event.result });
          } else {
            setLocateStage(event.stage);
          }
        }
      }
    } catch {
      setLocateError("Something went wrong. Please try again.");
    }
  }

  return (
    <div>
      <h1>bookFinder</h1>

      <section>
        <h2>Find a Book's Section</h2>
        <input
          type="text"
          placeholder="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <input
          type="text"
          placeholder="Author"
          value={author}
          onChange={(e) => setAuthor(e.target.value)}
        />
        <button onClick={handleSubmit} disabled={!title.trim()}>
          Classify
        </button>

        {classifyError && <p className="error">{classifyError}</p>}

        {/* {result && <pre>{JSON.stringify(result, null, 2)}</pre>} */}
        {result && result.result.message ? (
          <p>{result.result.message}</p>
        ) : (
          result && (
            <div>
              <h3>{result.result.title} by {result.result.author}</h3>
              <ul className="category-list">
                {result.result.categories.map((cat, index) => (
                  <li key={index}>
                    <strong>{cat.category}</strong>
                  </li>
                ))}
              </ul>
            </div>
          )
        )}
      </section>

      <hr />

      <section>
        <h2>Locate a Book on a Shelf</h2>
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => {
            setImage(e.target.files[0]);
            setLocateResult(null);
            setImageSize(null);
          }}
        />
        <input
          type="text"
          placeholder="Book title"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button onClick={handleLocate} disabled={!!locateStage && !locateResult}>
          Locate
        </button>
        <button onClick={handleClear} disabled={!image}>
          Clear
        </button>

        {locateError && <p className="error">{locateError}</p>}

        {locateStage && !locateResult && <p>{locateStage}</p>}

        {locateResult && !locateResult.result.found && (
          <p>{locateResult.result.message}</p>
        )}

        {imageUrl && (
          <div className="locate-image-wrapper">
            <img
              src={imageUrl}
              alt="Uploaded shelf"
              onLoad={(e) =>
                setImageSize({
                  width: e.target.naturalWidth,
                  height: e.target.naturalHeight,
                })
              }
              style={{ width: "100%", display: "block" }}
            />
            {locateResult?.result.found && imageSize && (
              <div
                className="locate-box"
                style={boxStyle(locateResult.result.box, imageSize)}
              />
            )}
          </div>
        )}
      </section>
    </div>
  );
}

export default App;
