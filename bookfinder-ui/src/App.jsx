import ClassifySection from "./components/ClassifySection";
import LocateSection from "./components/LocateSection";
import "./App.css";

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>bookFinder</h1>
        <p className="tagline">Classify any title, then find it on the shelf.</p>
      </header>
      <main className="sections">
        <ClassifySection />
        <LocateSection />
      </main>
    </div>
  );
}

export default App;