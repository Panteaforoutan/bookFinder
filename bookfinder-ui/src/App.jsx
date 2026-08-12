import { useState } from "react";
import "./App.css";

function App() {
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [result, setResult] = useState(null);
  const [classifyError, setClassifyError] = useState("");

  const [image, setImage] = useState(null);
  const [query, setQuery] = useState("");
  const [locateResult, setLocateResult] = useState(null);
  const [locateError, setLocateError] = useState("");

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

    const formData = new FormData();
    formData.append("image", image);
    formData.append("query", query);

    try {
      const response = await fetch("http://127.0.0.1:5001/locate", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) {
        setLocateError(data.error || "Something went wrong.");
        return;
      }
      setLocateResult(data);
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
        {result && (
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
        )}
      </section>

      <hr />

      <section>
        <h2>Locate a Book on a Shelf</h2>
        <input type="file" onChange={(e) => setImage(e.target.files[0])} />
        <input
          type="text"
          placeholder="Book title"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button onClick={handleLocate}>Locate</button>

        {locateError && <p className="error">{locateError}</p>}

        {locateResult && <pre>{JSON.stringify(locateResult, null, 2)}</pre>}
      </section>
    </div>
  );
}

export default App;
