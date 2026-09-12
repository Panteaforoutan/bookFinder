import { useEffect, useRef, useState } from "react";
import ImageUploadField from "./ImageUploadField";
import LocateImagePreview from "./LocateImagePreview";

function LocateSection() {
  const [image, setImage] = useState(null);
  const [imageUrl, setImageUrl] = useState(null);
  const [query, setQuery] = useState("");
  const [locateResult, setLocateResult] = useState(null);
  const [locateError, setLocateError] = useState("");
  const [locateStage, setLocateStage] = useState("");
  const [converting, setConverting] = useState(false);
  const uploadFieldRef = useRef(null);

  useEffect(() => {
    if (!image) {
      setImageUrl(null);
      return;
    }
    const url = URL.createObjectURL(image);
    setImageUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [image]);

  function handleImageSelected(file) {
    setLocateResult(null);
    setLocateError("");
    setLocateStage("");
    setImage(file);
  }

  function handleClear() {
    setImage(null);
    setLocateResult(null);
    setLocateError("");
    setLocateStage("");
    setQuery("");
    uploadFieldRef.current?.reset();
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
    <section className="panel">
      <h2>Locate a Book on a Shelf</h2>
      <div className="field-group">
        <ImageUploadField
          ref={uploadFieldRef}
          onImageSelected={handleImageSelected}
          converting={converting}
          setConverting={setConverting}
        />
        <input
          type="text"
          placeholder="Title"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="button-row">
          <button
            className="btn-primary"
            onClick={handleLocate}
            disabled={(!!locateStage && !locateResult) || converting || !image}
          >
            Locate
          </button>
          <button className="btn-secondary" onClick={handleClear} disabled={!image}>
            Clear
          </button>
        </div>
      </div>

      {locateError && <p className="error">{locateError}</p>}

      {locateResult && !locateResult.result.found && (
        <p>{locateResult.result.message}</p>
      )}

      <LocateImagePreview
        imageUrl={imageUrl}
        box={locateResult?.result.found ? locateResult.result.box : null}
        currentStage={locateResult ? null : locateStage}
      />
    </section>
  );
}

export default LocateSection;