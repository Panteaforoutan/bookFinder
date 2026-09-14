import { useState } from "react";
import ClassifyResult from "./ClassifyResult";

function ClassifySection() {
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [result, setResult] = useState(null);
  const [classifyError, setClassifyError] = useState("");

  async function handleSubmit() {
    if (!title.trim()) {
      setClassifyError("Please enter a title.");
      return;
    }
    setClassifyError("");
    setResult(null);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/classify`, {
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

  function handleClear() {
    setTitle("");
    setAuthor("");
    setResult(null);
    setClassifyError("");
  }

  return (
    <section className="panel">
      <h2>Find a Book's Section</h2>
      <div className="field-group">
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
        <div className="button-row">
          <button className="btn-primary" onClick={handleSubmit} disabled={!title.trim()}>
            Classify
          </button>
          <button
            className="btn-secondary"
            onClick={handleClear}
            disabled={!title && !author && !result}
          >
            Clear
          </button>
        </div>
      </div>

      {classifyError && <p className="error">{classifyError}</p>}

      <ClassifyResult result={result} />
    </section>
  );
}

export default ClassifySection;