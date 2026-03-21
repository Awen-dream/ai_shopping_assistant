import { useState } from 'react';
import { fetchMultiAgentResults } from '../services/api';
import ProductCard from './ProductCard';

export default function ChatWindow() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const handleSearch = async () => {
    const res = await fetchMultiAgentResults(query);
    setResults(res.results);
  };

  return (
    <div>
      <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search products..." />
      <button onClick={handleSearch}>Search</button>
      <div>
        {results.map(r => <ProductCard key={r.name} product={r} />)}
      </div>
    </div>
  );
}
