import { useState } from "react";
import { getRecommendations } from "./services/api";
import ChatWindow from "./components/ChatWindow";

function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);

  const handleSearch = async () => {
    const res = await getRecommendations(query);
    setResults(res);
  };

  return (
    <div className="App">
      <h1>AI Shopping Assistant</h1>
      <input value={query} onChange={e => setQuery(e.target.value)} />
      <button onClick={handleSearch}>Search</button>
      <ChatWindow results={results} />
    </div>
  );
}

export default App;