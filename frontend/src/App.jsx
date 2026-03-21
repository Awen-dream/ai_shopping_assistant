import { useState } from "react";
import { fetchImageResults, fetchMultiAgentResults } from "./services/api";

export default function App() {
  const [query, setQuery] = useState("");
  const [file, setFile] = useState(null);
  const [results, setResults] = useState([]);

  // 文字搜索
  const handleSearch = async () => {
    if (!query) return;
    try {
      const data = await fetchMultiAgentResults(query);
      // 去重商品，避免重复 id
      const uniqueResults = [];
      const seen = new Set();
      data.results.forEach((p) => {
        if (!seen.has(p.id)) {
          seen.add(p.id);
          uniqueResults.push(p);
        }
      });
      setResults(uniqueResults);
    } catch (err) {
      console.error(err);
    }
  };

  // 图片搜索
  const handleImageSearch = async () => {
    if (!file) return;
    try {
      const data = await fetchImageResults(file);
      const uniqueResults = [];
      const seen = new Set();
      data.results.forEach((p) => {
        if (!seen.has(p.id)) {
          seen.add(p.id);
          uniqueResults.push(p);
        }
      });
      setResults(uniqueResults);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">AI Shopping Assistant</h1>

      {/* 文字搜索 */}
      <div className="flex mb-2 gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="输入想要的商品或需求"
          className="border p-2 flex-1 rounded"
        />
        <button
          onClick={handleSearch}
          className="bg-blue-500 text-white px-4 rounded"
        >
          查询
        </button>
      </div>

      {/* 图片搜索 */}
      <div className="flex mb-4 gap-2">
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <button
          onClick={handleImageSearch}
          className="bg-green-500 text-white px-4 rounded"
        >
          上传图片搜索
        </button>
      </div>

      {/* 搜索结果 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {results.map((p, idx) => (
          <div key={`${p.id}-${idx}`} className="border p-4 rounded shadow">
            <div className="font-bold text-lg mb-1">{p.name}</div>
            <div className="text-sm text-gray-600 mb-2">{p.reason}</div>

            {/* 多商家价格 */}
            <div className="mb-2">
              <div className="font-semibold">多商家价格:</div>
              {p.available?.map((item, i) => (
                <div key={i}>
                  {item.store}: ¥{item.price.toFixed(2)}
                </div>
              ))}
            </div>

            {/* 可选图片 */}
            {p.image && (
              <img
                src={p.image}
                alt={p.name}
                className="mt-2 w-full h-40 object-contain border rounded"
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
