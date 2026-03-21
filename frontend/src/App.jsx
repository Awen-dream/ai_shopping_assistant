import { useEffect, useState } from "react";
import {
  fetchImageResults,
  fetchMultiAgentResults,
  fetchVectorIndexStatus,
  rebuildVectorIndex,
} from "./services/api";

export default function App() {
  const [query, setQuery] = useState("");
  const [file, setFile] = useState(null);
  const [userId, setUserId] = useState("");
  const [results, setResults] = useState([]);
  const [vectorStatus, setVectorStatus] = useState(null);
  const [vectorActionLoading, setVectorActionLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadVectorStatus() {
      try {
        const data = await fetchVectorIndexStatus();
        if (!cancelled) {
          setVectorStatus(data.status);
        }
      } catch (err) {
        console.error(err);
      }
    }

    loadVectorStatus();
    return () => {
      cancelled = true;
    };
  }, []);

  // 文字搜索
  const handleSearch = async () => {
    if (!query) return;
    try {
      const data = await fetchMultiAgentResults(query, userId);
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
      const data = await fetchImageResults(file, userId);
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

  const handleRebuildVectorIndex = async (persist) => {
    setVectorActionLoading(true);
    try {
      const data = await rebuildVectorIndex(persist);
      setVectorStatus(data.active_status);
    } catch (err) {
      console.error(err);
    } finally {
      setVectorActionLoading(false);
    }
  };

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">AI Shopping Assistant</h1>

      {vectorStatus && (
        <div className="mb-4 rounded border bg-gray-50 p-3 text-sm">
          <div className="font-semibold mb-1">本机向量索引</div>
          <div>后端: {vectorStatus.backend}</div>
          <div>状态: {vectorStatus.ready ? "ready" : "not ready"}</div>
          <div>来源: {vectorStatus.load_source}</div>
          <div>商品数: {vectorStatus.product_count}</div>
          <div className="mt-2 flex gap-2">
            <button
              onClick={() => handleRebuildVectorIndex(true)}
              className="bg-black text-white px-3 py-1 rounded disabled:opacity-50"
              disabled={vectorActionLoading}
            >
              重建并落盘
            </button>
            <button
              onClick={() => handleRebuildVectorIndex(false)}
              className="border px-3 py-1 rounded disabled:opacity-50"
              disabled={vectorActionLoading}
            >
              仅重建内存索引
            </button>
          </div>
        </div>
      )}

      {/* 文字搜索 */}
      <div className="flex mb-2 gap-2">
        <input
          type="text"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          placeholder="可选: 用户 ID，如 demo_apple_fan"
          className="border p-2 rounded w-72"
        />
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
            <div className="text-sm text-gray-500 mb-1">
              {p.brand} · {p.category}
              {p.subcategory ? ` · ${p.subcategory}` : ""}
            </div>
            <div className="text-sm text-gray-600 mb-2">{p.reason}</div>
            {p.match_score != null && (
              <div className="text-xs text-gray-500 mb-2">
                匹配分: {p.match_score}
              </div>
            )}
            <div className="text-xs text-gray-500 mb-2">
              月销 {p.monthly_sales ?? "-"} · {p.promotion_tag || "常规价"} · 总库存 {p.inventory_total ?? "-"}
            </div>

            {p.best_offer && (
              <div className="mb-3 rounded border bg-gray-50 p-2">
                <div className="font-semibold">最佳报价</div>
                <div>{p.best_offer.store}</div>
                <div>
                  ¥{p.best_offer.sale_price.toFixed(2)}
                  {p.best_offer.discount > 0 && (
                    <span className="ml-2 text-sm text-gray-500 line-through">
                      ¥{p.best_offer.list_price.toFixed(2)}
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-500">
                  {p.best_offer.promotion} · {p.best_offer.stock_status}
                </div>
              </div>
            )}

            {/* 多商家价格 */}
            <div className="mb-2">
              <div className="font-semibold">多商家价格:</div>
              {p.available?.map((item, i) => (
                <div key={i} className="mb-1 rounded border p-2 text-sm">
                  <div>{item.store}</div>
                  <div>
                    现价: ¥{item.sale_price.toFixed(2)}
                    {item.discount > 0 && (
                      <span className="ml-2 text-gray-500 line-through">
                        ¥{item.list_price.toFixed(2)}
                      </span>
                    )}
                  </div>
                  <div className="text-gray-500">
                    {item.promotion} · {item.stock_status} · {item.shipping_days}天发货
                  </div>
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
