function ClassifyResult({ result }) {
  if (!result) return null;

  if (result.result.message) {
    return <p>{result.result.message}</p>;
  }

  return (
    <div>
      <h3>
        {result.result.title} by {result.result.author}
      </h3>
      <ul className="category-list">
        {result.result.categories.map((cat, index) => (
          <li key={index}>
            <strong>{cat.category}</strong>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default ClassifyResult;