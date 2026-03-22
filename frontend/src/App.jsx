import { useEffect, useState } from "react";
import {
  createProduct,
  deleteProduct,
  fetchProducts,
  fetchImageResults,
  fetchMultiAgentResults,
  fetchUserProfile,
  fetchVectorIndexStatus,
  rebuildVectorIndex,
  saveUserProfile,
  updateProduct,
} from "./services/api";

const EMPTY_PRODUCT_FORM = {
  id: null,
  name: "",
  description: "",
  category: "耳机",
  subcategory: "",
  brand: "",
  price: "",
  rating: "",
  tags: "",
  monthlySales: "",
  promotionTag: "",
  inventoryTotal: "",
};

const EMPTY_PROFILE_FORM = {
  preferredBrand: "",
  budgetMin: "",
  budgetMax: "",
  interests: "",
  preferredCategories: "",
  priceSensitivity: "medium",
  city: "",
};

function mapProductToForm(product) {
  return {
    id: product.id,
    name: product.name || "",
    description: product.description || "",
    category: product.category || "耳机",
    subcategory: product.subcategory || "",
    brand: product.brand || "",
    price: product.price ?? "",
    rating: product.rating ?? "",
    tags: Array.isArray(product.tags) ? product.tags.join(", ") : "",
    monthlySales: product.monthly_sales ?? "",
    promotionTag: product.promotion_tag || "",
    inventoryTotal: product.inventory_total ?? "",
  };
}

function buildProductPayload(form) {
  return {
    name: form.name.trim(),
    description: form.description.trim(),
    category: form.category.trim(),
    subcategory: form.subcategory.trim(),
    brand: form.brand.trim(),
    price: Number(form.price || 0),
    rating: Number(form.rating || 0),
    tags: form.tags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean),
    monthly_sales: Number(form.monthlySales || 0),
    promotion_tag: form.promotionTag.trim(),
    inventory_total: Number(form.inventoryTotal || 0),
  };
}

function mapProfileToForm(profile) {
  if (!profile) {
    return EMPTY_PROFILE_FORM;
  }

  return {
    preferredBrand: (profile.preferred_brand || []).join(", "),
    budgetMin: profile.budget_range?.[0] ?? "",
    budgetMax: profile.budget_range?.[1] ?? "",
    interests: (profile.interests || []).join(", "),
    preferredCategories: (profile.preferred_categories || []).join(", "),
    priceSensitivity: profile.price_sensitivity || "medium",
    city: profile.city || "",
  };
}

function buildProfilePayload(form) {
  return {
    preferred_brand: form.preferredBrand
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean),
    budget_range: [Number(form.budgetMin || 0), Number(form.budgetMax || 15000)],
    interests: form.interests
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean),
    preferred_categories: form.preferredCategories
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean),
    price_sensitivity: form.priceSensitivity,
    city: form.city.trim(),
  };
}

export default function App() {
  const [query, setQuery] = useState("");
  const [file, setFile] = useState(null);
  const [userId, setUserId] = useState("");
  const [results, setResults] = useState([]);
  const [vectorStatus, setVectorStatus] = useState(null);
  const [vectorActionLoading, setVectorActionLoading] = useState(false);
  const [products, setProducts] = useState([]);
  const [productForm, setProductForm] = useState(EMPTY_PRODUCT_FORM);
  const [productActionLoading, setProductActionLoading] = useState(false);
  const [profileForm, setProfileForm] = useState(EMPTY_PROFILE_FORM);
  const [profileActionLoading, setProfileActionLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadAdminData() {
      try {
        const [vectorData, productData] = await Promise.all([
          fetchVectorIndexStatus(),
          fetchProducts(),
        ]);
        if (!cancelled) {
          setVectorStatus(vectorData.status);
          setProducts(productData.products);
        }
      } catch (err) {
        console.error(err);
      }
    }

    loadAdminData();
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

  const handleProductFormChange = (field, value) => {
    setProductForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const handleEditProduct = (product) => {
    setProductForm(mapProductToForm(product));
  };

  const resetProductForm = () => {
    setProductForm(EMPTY_PRODUCT_FORM);
  };

  const refreshProducts = async () => {
    const [productData, vectorData] = await Promise.all([
      fetchProducts(),
      fetchVectorIndexStatus(),
    ]);
    setProducts(productData.products);
    setVectorStatus(vectorData.status);
  };

  const handleDeleteProduct = async (productId) => {
    setProductActionLoading(true);
    try {
      await deleteProduct(productId);
      await refreshProducts();
      if (productForm.id === productId) {
        resetProductForm();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setProductActionLoading(false);
    }
  };

  const handleSaveProduct = async () => {
    setProductActionLoading(true);
    try {
      const payload = buildProductPayload(productForm);
      if (productForm.id) {
        await updateProduct(productForm.id, payload);
      } else {
        await createProduct(payload);
      }
      await refreshProducts();
      resetProductForm();
    } catch (err) {
      console.error(err);
    } finally {
      setProductActionLoading(false);
    }
  };

  const handleProfileFormChange = (field, value) => {
    setProfileForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const handleLoadProfile = async () => {
    if (!userId.trim()) return;
    setProfileActionLoading(true);
    try {
      const data = await fetchUserProfile(userId.trim());
      setProfileForm(mapProfileToForm(data.profile));
    } catch (err) {
      console.error(err);
    } finally {
      setProfileActionLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    if (!userId.trim()) return;
    setProfileActionLoading(true);
    try {
      await saveUserProfile(userId.trim(), buildProfilePayload(profileForm));
      await handleLoadProfile();
    } catch (err) {
      console.error(err);
    } finally {
      setProfileActionLoading(false);
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

      <div className="mb-6 rounded border p-4">
        <div className="font-semibold mb-3">用户画像管理</div>
        <div className="text-sm text-gray-500 mb-3">
          先在顶部输入用户 ID，再在这里载入或保存画像。
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
          <input
            type="text"
            value={profileForm.preferredBrand}
            onChange={(e) => handleProfileFormChange("preferredBrand", e.target.value)}
            placeholder="偏好品牌，逗号分隔"
            className="border p-2 rounded"
          />
          <input
            type="text"
            value={profileForm.preferredCategories}
            onChange={(e) => handleProfileFormChange("preferredCategories", e.target.value)}
            placeholder="偏好分类，逗号分隔"
            className="border p-2 rounded"
          />
          <input
            type="number"
            value={profileForm.budgetMin}
            onChange={(e) => handleProfileFormChange("budgetMin", e.target.value)}
            placeholder="预算下限"
            className="border p-2 rounded"
          />
          <input
            type="number"
            value={profileForm.budgetMax}
            onChange={(e) => handleProfileFormChange("budgetMax", e.target.value)}
            placeholder="预算上限"
            className="border p-2 rounded"
          />
          <input
            type="text"
            value={profileForm.interests}
            onChange={(e) => handleProfileFormChange("interests", e.target.value)}
            placeholder="兴趣点，逗号分隔"
            className="border p-2 rounded"
          />
          <select
            value={profileForm.priceSensitivity}
            onChange={(e) => handleProfileFormChange("priceSensitivity", e.target.value)}
            className="border p-2 rounded"
          >
            <option value="low">价格不敏感</option>
            <option value="medium">价格中等敏感</option>
            <option value="high">价格敏感</option>
          </select>
          <input
            type="text"
            value={profileForm.city}
            onChange={(e) => handleProfileFormChange("city", e.target.value)}
            placeholder="城市"
            className="border p-2 rounded"
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleLoadProfile}
            className="border px-4 py-2 rounded disabled:opacity-50"
            disabled={profileActionLoading || !userId.trim()}
          >
            载入画像
          </button>
          <button
            onClick={handleSaveProfile}
            className="bg-black text-white px-4 py-2 rounded disabled:opacity-50"
            disabled={profileActionLoading || !userId.trim()}
          >
            保存画像
          </button>
        </div>
      </div>

      <div className="mb-6 rounded border p-4">
        <div className="font-semibold mb-3">商品管理</div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
          <input
            type="text"
            value={productForm.name}
            onChange={(e) => handleProductFormChange("name", e.target.value)}
            placeholder="商品名"
            className="border p-2 rounded"
          />
          <input
            type="text"
            value={productForm.brand}
            onChange={(e) => handleProductFormChange("brand", e.target.value)}
            placeholder="品牌"
            className="border p-2 rounded"
          />
          <input
            type="text"
            value={productForm.category}
            onChange={(e) => handleProductFormChange("category", e.target.value)}
            placeholder="分类"
            className="border p-2 rounded"
          />
          <input
            type="text"
            value={productForm.subcategory}
            onChange={(e) => handleProductFormChange("subcategory", e.target.value)}
            placeholder="子分类"
            className="border p-2 rounded"
          />
          <input
            type="number"
            value={productForm.price}
            onChange={(e) => handleProductFormChange("price", e.target.value)}
            placeholder="价格"
            className="border p-2 rounded"
          />
          <input
            type="number"
            step="0.1"
            value={productForm.rating}
            onChange={(e) => handleProductFormChange("rating", e.target.value)}
            placeholder="评分"
            className="border p-2 rounded"
          />
          <input
            type="number"
            value={productForm.monthlySales}
            onChange={(e) => handleProductFormChange("monthlySales", e.target.value)}
            placeholder="月销量"
            className="border p-2 rounded"
          />
          <input
            type="number"
            value={productForm.inventoryTotal}
            onChange={(e) => handleProductFormChange("inventoryTotal", e.target.value)}
            placeholder="总库存"
            className="border p-2 rounded"
          />
          <input
            type="text"
            value={productForm.promotionTag}
            onChange={(e) => handleProductFormChange("promotionTag", e.target.value)}
            placeholder="促销标签"
            className="border p-2 rounded"
          />
          <input
            type="text"
            value={productForm.tags}
            onChange={(e) => handleProductFormChange("tags", e.target.value)}
            placeholder="标签，逗号分隔"
            className="border p-2 rounded"
          />
        </div>
        <textarea
          value={productForm.description}
          onChange={(e) => handleProductFormChange("description", e.target.value)}
          placeholder="商品描述"
          className="border p-2 rounded w-full mb-3"
          rows={3}
        />
        <div className="flex gap-2 mb-4">
          <button
            onClick={handleSaveProduct}
            className="bg-black text-white px-4 py-2 rounded disabled:opacity-50"
            disabled={productActionLoading}
          >
            {productForm.id ? "保存修改" : "新增商品"}
          </button>
          <button
            onClick={resetProductForm}
            className="border px-4 py-2 rounded"
            disabled={productActionLoading}
          >
            清空
          </button>
        </div>

        <div className="space-y-2 max-h-72 overflow-auto">
          {products.map((product) => (
            <div key={product.id} className="border rounded p-3 flex items-center justify-between gap-3">
              <div>
                <div className="font-medium">{product.name}</div>
                <div className="text-sm text-gray-500">
                  {product.brand} · {product.category} · ¥{product.price}
                </div>
              </div>
              <button
                onClick={() => handleEditProduct(product)}
                className="border px-3 py-1 rounded"
              >
                编辑
              </button>
              <button
                onClick={() => handleDeleteProduct(product.id)}
                className="border px-3 py-1 rounded text-red-600"
                disabled={productActionLoading}
              >
                删除
              </button>
            </div>
          ))}
        </div>
      </div>

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
