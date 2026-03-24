import { useEffect, useState } from "react";
import {
  createProduct,
  deleteProduct,
  fetchAnalyticsDashboard,
  fetchAnalyticsEvaluation,
  fetchProducts,
  fetchImageResults,
  fetchMultiAgentResults,
  fetchUserProfile,
  fetchVectorIndexStatus,
  rebuildVectorIndex,
  saveUserProfile,
  sendFeedbackEvent,
  updateProduct,
} from "./services/api";
import "./app.css";

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

function formatMoney(value) {
  if (typeof value !== "number") {
    return "-";
  }
  return `¥${value.toFixed(2)}`;
}

function formatPercent(value) {
  return `${((value || 0) * 100).toFixed(0)}%`;
}

function formatDateTime(value) {
  if (!value) {
    return "暂无";
  }
  return value.replace("T", " ").slice(0, 16);
}

function formatRatio(value) {
  if (typeof value !== "number") {
    return "-";
  }
  return `${(value * 100).toFixed(0)}%`;
}

function getEvaluationIssues(item) {
  const issues = [];

  if (!item.top1_hit) {
    issues.push("Top1 未命中");
  }
  if (!item.category_hit) {
    issues.push("类目未命中");
  }
  if (item.brand_hit === false) {
    issues.push("品牌未命中");
  }
  if (item.budget_hit === false) {
    issues.push("预算未命中");
  }

  return issues;
}

function summarizeEvaluationIssues(items) {
  const counts = new Map();

  items.forEach((item) => {
    if (item.passed) {
      return;
    }

    const issues = getEvaluationIssues(item);
    const normalizedIssues = issues.length ? issues : ["需要进一步排查"];
    normalizedIssues.forEach((issue) => {
      counts.set(issue, (counts.get(issue) || 0) + 1);
    });
  });

  return [...counts.entries()]
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0], "zh-CN"))
    .slice(0, 3)
    .map(([label, count]) => ({ label, count }));
}

function summarizeCategoryIssues(items) {
  const categoryMap = new Map();

  items.forEach((item) => {
    if (item.passed) {
      return;
    }

    const category = item.expected_category || item.actual_category || "其他";
    const issues = getEvaluationIssues(item);
    const normalizedIssues = issues.length ? issues : ["需要进一步排查"];

    if (!categoryMap.has(category)) {
      categoryMap.set(category, new Map());
    }

    const issueMap = categoryMap.get(category);
    normalizedIssues.forEach((issue) => {
      issueMap.set(issue, (issueMap.get(issue) || 0) + 1);
    });
  });

  return [...categoryMap.entries()]
    .map(([category, issueMap]) => {
      const [topIssue, count] = [...issueMap.entries()].sort(
        (left, right) => right[1] - left[1] || left[0].localeCompare(right[0], "zh-CN")
      )[0] || ["需要进一步排查", 0];

      return { category, topIssue, count };
    })
    .sort((left, right) => right.count - left.count || left.category.localeCompare(right.category, "zh-CN"))
    .slice(0, 3);
}

function summarizeCategoryProductSignals(items) {
  const categoryMap = new Map();

  items.forEach((item) => {
    if (item.passed) {
      return;
    }

    const category = item.expected_category || item.actual_category || "其他";
    if (!categoryMap.has(category)) {
      categoryMap.set(category, {
        count: 0,
        expectedProducts: new Map(),
        expectedBrands: new Map(),
        actualProducts: new Map(),
        actualBrands: new Map(),
      });
    }

    const bucket = categoryMap.get(category);
    bucket.count += 1;

    const expectedProduct = item.expected_top_product || "未定义目标商品";
    const expectedBrand = item.expected_brand || "未定义目标品牌";
    const actualProduct = item.actual_top_product || "无结果";
    const actualBrand = item.actual_brand || "未知品牌";

    bucket.expectedProducts.set(expectedProduct, (bucket.expectedProducts.get(expectedProduct) || 0) + 1);
    bucket.expectedBrands.set(expectedBrand, (bucket.expectedBrands.get(expectedBrand) || 0) + 1);
    bucket.actualProducts.set(actualProduct, (bucket.actualProducts.get(actualProduct) || 0) + 1);
    bucket.actualBrands.set(actualBrand, (bucket.actualBrands.get(actualBrand) || 0) + 1);
  });

  const pickTop = (map, fallback) =>
    [...map.entries()].sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0], "zh-CN"))[0]?.[0] ||
    fallback;

  return [...categoryMap.entries()]
    .map(([category, bucket]) => ({
      category,
      count: bucket.count,
      targetProduct: pickTop(bucket.expectedProducts, "未定义目标商品"),
      targetBrand: pickTop(bucket.expectedBrands, "未定义目标品牌"),
      actualProduct: pickTop(bucket.actualProducts, "无结果"),
      actualBrand: pickTop(bucket.actualBrands, "未知品牌"),
    }))
    .sort((left, right) => right.count - left.count || left.category.localeCompare(right.category, "zh-CN"))
    .slice(0, 3);
}

function StatCard({ label, value, hint, tone = "workspace" }) {
  return (
    <div className={`stat-card stat-card--${tone}`}>
      <div className="stat-card__eyebrow">{label}</div>
      <div className="stat-card__value">{value}</div>
      {hint ? <div className="stat-card__hint">{hint}</div> : null}
    </div>
  );
}

function SectionCard({
  title,
  subtitle,
  actions,
  children,
  tone = "workspace",
  eyebrow = "Workspace Module",
}) {
  return (
    <section className={`panel panel--${tone}`}>
      <div className="panel__header">
        <div>
          <div className="panel__eyebrow">{eyebrow}</div>
          <h2 className="panel__title">{title}</h2>
          {subtitle ? <p className="panel__subtitle">{subtitle}</p> : null}
        </div>
        {actions ? <div className="panel__actions">{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}

function SegmentedTabs({ options, value, onChange, dark = false }) {
  return (
    <div className={`segmented-tabs${dark ? " segmented-tabs--dark" : ""}`}>
      {options.map((option) => {
        const active = value === option.value;
        return (
          <button
            key={option.value}
            onClick={() => onChange(option.value)}
            className={`segmented-tabs__item${active ? " is-active" : ""}`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

function MiniList({ title, items, renderItem, emptyText = "暂无数据", tone = "workspace" }) {
  return (
    <div className={`mini-panel mini-panel--${tone}`}>
      <div className="mini-panel__title">{title}</div>
      {items?.length > 0 ? (
        <div className="mini-panel__body">{items.map(renderItem)}</div>
      ) : (
        <div className="mini-panel__empty">{emptyText}</div>
      )}
    </div>
  );
}

function ResultCard({ product, query, userId, feedbackLoadingKey, onFeedback }) {
  const matchedFeatures = [
    ...(product.matched_features?.matched_terms || []),
    ...(product.matched_features?.matched_required_features || []),
  ]
    .filter(Boolean)
    .slice(0, 4);

  return (
    <article className="result-card">
      <div className="result-card__glow result-card__glow--top" />
      <div className="result-card__glow result-card__glow--bottom" />

      <div className="result-card__header">
        <div>
          <div className="result-card__badge">Curated Pick</div>
          <div className="result-card__title">{product.name}</div>
          <div className="result-card__meta">
            {product.brand} · {product.category}
            {product.subcategory ? ` · ${product.subcategory}` : ""}
          </div>
        </div>
        {product.match_score != null ? (
          <div className="result-card__score">匹配分 {product.match_score}</div>
        ) : null}
      </div>

      <p className="result-card__reason">{product.reason}</p>

      <div className="chip-row">
        <span className="chip chip--emerald">月销 {product.monthly_sales ?? "-"}</span>
        <span className="chip chip--amber">{product.promotion_tag || "常规价"}</span>
        <span className="chip chip--sky">库存 {product.inventory_total ?? "-"}</span>
        {matchedFeatures.map((feature) => (
          <span key={`${product.id}-${feature}`} className="chip chip--neutral">
            {feature}
          </span>
        ))}
      </div>

      {product.best_offer ? (
        <div className="best-offer">
          <div className="best-offer__header">
            <div>
              <div className="best-offer__title">最佳报价</div>
              <div className="best-offer__meta">
                {product.best_offer.store} · {product.best_offer.stock_status}
              </div>
            </div>
            <div className="best-offer__price-wrap">
              <div className="best-offer__price">{formatMoney(product.best_offer.sale_price)}</div>
              {product.best_offer.discount > 0 ? (
                <div className="best-offer__list-price">
                  {formatMoney(product.best_offer.list_price)}
                </div>
              ) : null}
            </div>
          </div>

          <div className="best-offer__grid">
            <div>促销: {product.best_offer.promotion || "-"}</div>
            <div>履约: {product.best_offer.fulfillment_type || "-"}</div>
            <div>仓库: {product.best_offer.fulfillment_warehouse || "-"}</div>
            <div>
              时效:{" "}
              {product.best_offer.estimated_delivery ||
                `${product.best_offer.shipping_days}天发货`}
            </div>
          </div>
        </div>
      ) : null}

      <div className="feedback-row">
        {[
          ["click", "记录点击"],
          ["favorite", "收藏"],
          ["purchase", "想下单"],
        ].map(([eventType, label]) => (
          <button
            key={`${product.id}-${eventType}`}
            onClick={() => onFeedback(eventType, product)}
            className={`button button--ghost${
              feedbackLoadingKey === `${eventType}-${product.id}` ? " is-loading" : ""
            }`}
            disabled={feedbackLoadingKey === `${eventType}-${product.id}`}
          >
            {label}
          </button>
        ))}
      </div>

      <details className="offer-details">
        <summary className="offer-details__summary">
          查看 {product.available?.length || 0} 个商家报价
          {query ? ` · 查询词：${query}` : ""}
          {userId ? ` · 用户：${userId}` : ""}
        </summary>

        <div className="offer-details__list">
          {product.available?.map((item, index) => (
            <div
              key={`${product.id}-${item.store}-${index}`}
              className="offer-details__item"
            >
              <div className="offer-details__item-header">
                <div className="offer-details__store">{item.store}</div>
                <div className="offer-details__price">{formatMoney(item.sale_price)}</div>
              </div>
              <div className="offer-details__item-meta">
                {item.promotion} · {item.stock_status} · {item.shipping_days}天发货
              </div>
            </div>
          ))}
        </div>
      </details>
    </article>
  );
}

export default function App() {
  const [activeView, setActiveView] = useState("workspace");
  const [adminTab, setAdminTab] = useState("dashboard");
  const [query, setQuery] = useState("");
  const [file, setFile] = useState(null);
  const [userId, setUserId] = useState("");
  const [results, setResults] = useState([]);
  const [analyticsDashboard, setAnalyticsDashboard] = useState(null);
  const [analyticsEvaluation, setAnalyticsEvaluation] = useState(null);
  const [evaluationFilter, setEvaluationFilter] = useState("all");
  const [vectorStatus, setVectorStatus] = useState(null);
  const [vectorActionLoading, setVectorActionLoading] = useState(false);
  const [products, setProducts] = useState([]);
  const [productForm, setProductForm] = useState(EMPTY_PRODUCT_FORM);
  const [productActionLoading, setProductActionLoading] = useState(false);
  const [profileForm, setProfileForm] = useState(EMPTY_PROFILE_FORM);
  const [profileActionLoading, setProfileActionLoading] = useState(false);
  const [feedbackLoadingKey, setFeedbackLoadingKey] = useState("");
  const isWorkspaceView = activeView === "workspace";

  const analyticsSummary = analyticsDashboard?.summary;
  const evaluationCases = analyticsEvaluation?.cases || [];

  const filteredEvaluationCases = evaluationCases.filter((item) => {
    if (evaluationFilter === "all") {
      return true;
    }
    if (evaluationFilter === "failed") {
      return !item.passed;
    }
    if (evaluationFilter === "profile") {
      return Boolean(item.user_id);
    }
    if (evaluationFilter === "budget") {
      return item.max_price != null;
    }
    return item.expected_category === evaluationFilter;
  });

  const sortedEvaluationCases = [...filteredEvaluationCases].sort((left, right) => {
    if (left.passed !== right.passed) {
      return left.passed ? 1 : -1;
    }
    return left.query.localeCompare(right.query, "zh-CN");
  });
  const topEvaluationIssues = summarizeEvaluationIssues(filteredEvaluationCases);
  const categoryIssueInsights = summarizeCategoryIssues(filteredEvaluationCases);
  const categoryProductSignals = summarizeCategoryProductSignals(filteredEvaluationCases);

  const filteredEvaluationSummary = (() => {
    if (!filteredEvaluationCases.length) {
      return {
        totalCases: 0,
        passedCases: 0,
        passRate: 0,
        top1HitRate: 0,
        categoryHitRate: 0,
        brandHitRate: 0,
        budgetHitRate: 0,
        failedCases: 0,
      };
    }

    const passedCases = filteredEvaluationCases.filter((item) => item.passed).length;
    const top1Hits = filteredEvaluationCases.filter((item) => item.top1_hit).length;
    const categoryHits = filteredEvaluationCases.filter((item) => item.category_hit).length;
    const brandCases = filteredEvaluationCases.filter((item) => item.brand_hit != null);
    const budgetCases = filteredEvaluationCases.filter((item) => item.budget_hit != null);
    return {
      totalCases: filteredEvaluationCases.length,
      passedCases,
      passRate: passedCases / filteredEvaluationCases.length,
      top1HitRate: top1Hits / filteredEvaluationCases.length,
      categoryHitRate: categoryHits / filteredEvaluationCases.length,
      brandHitRate: brandCases.length
        ? brandCases.filter((item) => item.brand_hit).length / brandCases.length
        : 0,
      budgetHitRate: budgetCases.length
        ? budgetCases.filter((item) => item.budget_hit).length / budgetCases.length
        : 0,
      failedCases: filteredEvaluationCases.length - passedCases,
    };
  })();

  const refreshAnalyticsInsights = async () => {
    const [analyticsData, evaluationData] = await Promise.all([
      fetchAnalyticsDashboard(),
      fetchAnalyticsEvaluation(),
    ]);
    setAnalyticsDashboard(analyticsData.dashboard);
    setAnalyticsEvaluation(evaluationData.evaluation);
    return {
      dashboard: analyticsData.dashboard,
      evaluation: evaluationData.evaluation,
    };
  };

  useEffect(() => {
    let cancelled = false;

    async function loadAdminData() {
      try {
        const [dashboard, evaluationData, vectorData, productData] = await Promise.all([
          fetchAnalyticsDashboard(),
          fetchAnalyticsEvaluation(),
          fetchVectorIndexStatus(),
          fetchProducts(),
        ]);
        if (!cancelled) {
          setAnalyticsDashboard(dashboard.dashboard);
          setAnalyticsEvaluation(evaluationData.evaluation);
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

  const handleSearch = async () => {
    if (!query) return;
    try {
      const data = await fetchMultiAgentResults(query, userId);
      const uniqueResults = [];
      const seen = new Set();
      data.results.forEach((product) => {
        if (!seen.has(product.id)) {
          seen.add(product.id);
          uniqueResults.push(product);
        }
      });
      setResults(uniqueResults);
      await refreshAnalyticsInsights();
      setActiveView("workspace");
    } catch (err) {
      console.error(err);
    }
  };

  const handleImageSearch = async () => {
    if (!file) return;
    try {
      const data = await fetchImageResults(file, userId);
      const uniqueResults = [];
      const seen = new Set();
      data.results.forEach((product) => {
        if (!seen.has(product.id)) {
          seen.add(product.id);
          uniqueResults.push(product);
        }
      });
      setResults(uniqueResults);
      await refreshAnalyticsInsights();
      setActiveView("workspace");
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
    setAdminTab("products");
    setActiveView("admin");
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
    await refreshAnalyticsInsights();
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
      setAdminTab("profiles");
      setActiveView("admin");
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

  const handleFeedback = async (eventType, product) => {
    const loadingKey = `${eventType}-${product.id}`;
    setFeedbackLoadingKey(loadingKey);
    try {
      await sendFeedbackEvent({
        event_type: eventType,
        product_id: product.id,
        product_name: product.name,
        query,
        user_id: userId || undefined,
      });
      await refreshAnalyticsInsights();
    } catch (err) {
      console.error(err);
    } finally {
      setFeedbackLoadingKey("");
    }
  };

  const quickStats = analyticsSummary
    ? [
        {
          label: "请求总量",
          value: analyticsSummary.total_requests,
          hint: `文本 ${analyticsSummary.text_requests} · 图片 ${analyticsSummary.image_requests}`,
        },
        {
          label: "点击反馈",
          value: analyticsSummary.feedback_counts?.click ?? 0,
          hint: `点击率 ${formatPercent(analyticsSummary.feedback_rates?.click_rate)}`,
        },
        {
          label: "收藏反馈",
          value: analyticsSummary.feedback_counts?.favorite ?? 0,
          hint: `收藏率 ${formatPercent(analyticsSummary.feedback_rates?.favorite_rate)}`,
        },
        {
          label: "购买意向",
          value: analyticsSummary.feedback_counts?.purchase ?? 0,
          hint: `想下单率 ${formatPercent(analyticsSummary.feedback_rates?.purchase_rate)}`,
        },
      ]
    : [];

  const adminOverview = [
    {
      label: "当前模块",
      value:
        {
          dashboard: "效果看板",
          vector: "向量索引",
          profiles: "用户画像",
          products: "商品管理",
        }[adminTab] || "运营工作台",
      hint: "当前聚焦区域",
    },
    {
      label: "索引状态",
      value: vectorStatus?.ready ? "已就绪" : "待检查",
      hint: vectorStatus?.backend || "等待初始化",
    },
    {
      label: "商品目录",
      value: `${products.length} 件`,
      hint: "当前商品池规模",
    },
    {
      label: "当前用户",
      value: userId?.trim() || "未指定",
      hint: analyticsEvaluation
        ? `评估通过率 ${formatRatio(analyticsEvaluation.summary?.pass_rate)}`
        : "画像调试入口",
    },
  ];

  const heroContent = isWorkspaceView
    ? {
        eyebrow: "Search Atelier",
        title: "像 AI 导购陈列馆一样，优雅地完成搜索、比价与推荐决策",
        subtitle:
          "搜索工作台更偏体验与发现，用更温润的层级承接查询、推荐理由和最佳报价，让用户像在逛一间被精心策展过的商品馆。",
      }
    : {
        eyebrow: "Operations Console",
        title: "像策略驾驶舱一样，冷静地观察指标、索引与商品运营动作",
        subtitle:
          "运营工作台更偏效率与控制，用更理性克制的视觉语言承载效果看板、画像维护、索引管理与商品编排，让信息密度更高但不凌乱。",
      };

  return (
    <div className="app-shell">
      <div className="app-shell__backdrop app-shell__backdrop--cyan" />
      <div className="app-shell__backdrop app-shell__backdrop--amber" />
      <div className="app-shell__backdrop app-shell__backdrop--emerald" />

      <main className="app-frame">
        <header className={`hero ${isWorkspaceView ? "hero--workspace" : "hero--admin"}`}>
          <div className="hero__inner">
            <div className="hero__copy">
              <div className="hero__eyebrow">{heroContent.eyebrow}</div>
              <h1 className="hero__title">{heroContent.title}</h1>
              <p className="hero__subtitle">{heroContent.subtitle}</p>
            </div>

            <SegmentedTabs
              options={[
                { label: "搜索工作台", value: "workspace" },
                { label: "运营管理台", value: "admin" },
              ]}
              value={activeView}
              onChange={setActiveView}
              dark
            />
          </div>

          {quickStats.length > 0 ? (
            <div className="hero__stats">
              {quickStats.map((stat) => (
                <div key={stat.label} className="hero-stat">
                  <div className="hero-stat__label">{stat.label}</div>
                  <div className="hero-stat__value">{stat.value}</div>
                  <div className="hero-stat__hint">{stat.hint}</div>
                </div>
              ))}
            </div>
          ) : null}
        </header>

        {activeView === "workspace" ? (
          <section className="workspace-theme">
            <div className="view-intro view-intro--workspace">
              <div className="view-intro__eyebrow">AI Shopping Flow</div>
              <div className="view-intro__headline">搜索工作台</div>
              <div className="view-intro__copy">
                面向用户体验的导购视图。重点突出查询输入、推荐理由、最佳报价和反馈动作，让每次搜索都像一次被策展过的商品探索。
              </div>
              <div className="view-intro__chips">
                <span className="view-intro__chip">场景搜索</span>
                <span className="view-intro__chip">推荐理由</span>
                <span className="view-intro__chip">最佳报价</span>
                <span className="view-intro__chip">即时反馈</span>
              </div>
            </div>

            <div className="workspace-layout">
            <div className="workspace-main">
              <SectionCard
                title="搜索工作台"
                subtitle="把用户 ID、文本需求和图片搜索放到同一区域，先找到结果，再决定是否记录反馈。"
                tone="workspace"
                eyebrow="Search Session"
              >
                <div className="search-grid">
                  <input
                    type="text"
                    value={userId}
                    onChange={(e) => setUserId(e.target.value)}
                    placeholder="可选用户 ID，如 demo_student"
                    className="field"
                  />
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="输入想要的商品、预算或场景"
                    className="field"
                  />
                  <button onClick={handleSearch} className="button button--primary">
                    开始搜索
                  </button>
                </div>

                <div className="upload-row">
                  <label className="upload-card">
                    <span className="upload-card__title">图片搜索</span>
                    <span className="upload-card__hint">上传一张商品图，做相似推荐</span>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => setFile(e.target.files?.[0] || null)}
                      className="upload-card__input"
                    />
                  </label>
                  <button onClick={handleImageSearch} className="button button--accent">
                    上传图片搜索
                  </button>
                </div>
              </SectionCard>

              <SectionCard
                title="推荐结果"
                subtitle={
                  results.length > 0
                    ? `当前展示 ${results.length} 个推荐结果`
                    : "先执行一次搜索，结果会展示在这里。"
                }
                tone="workspace"
                eyebrow="Curated Results"
              >
                {results.length > 0 ? (
                  <div className="results-grid">
                    {results.map((product, index) => (
                      <ResultCard
                        key={`${product.id}-${index}`}
                        product={product}
                        query={query}
                        userId={userId}
                        feedbackLoadingKey={feedbackLoadingKey}
                        onFeedback={handleFeedback}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">
                    还没有结果。可以先试试 “通勤降噪耳机” 或 “学生 预算6000 轻薄本”。
                  </div>
                )}
              </SectionCard>
            </div>

            <aside className="workspace-side">
              <SectionCard
                title="当前会话"
                subtitle="把最关键的运营信息收在侧边，不打断主搜索流。"
                tone="workspace"
                eyebrow="Session Pulse"
              >
                <div className="side-stats">
                  <StatCard
                    label="最近请求"
                    value={formatDateTime(analyticsSummary?.last_event_at)}
                    hint={userId ? `当前用户：${userId}` : "当前为匿名会话"}
                    tone="workspace"
                  />
                  <StatCard
                    label="平均返回数"
                    value={analyticsSummary?.average_result_count ?? 0}
                    hint={results.length > 0 ? `当前结果 ${results.length} 条` : "等待下一次搜索"}
                    tone="workspace"
                  />
                </div>
              </SectionCard>

              <MiniList
                title="热门查询"
                items={analyticsSummary?.top_queries || []}
                tone="workspace"
                renderItem={(item) => (
                  <div key={item.name} className="list-chip">
                    <span>{item.name}</span>
                    <span className="list-chip__count">{item.count}</span>
                  </div>
                )}
              />

              <MiniList
                title="最近反馈"
                items={analyticsDashboard?.recent_feedback || []}
                tone="workspace"
                renderItem={(item) => (
                  <div key={item.event_id} className="mini-item">
                    <div className="mini-item__title">{item.product_name || `商品 ${item.product_id}`}</div>
                    <div className="mini-item__meta">
                      {item.event_type} · {item.query || "无查询上下文"}
                    </div>
                  </div>
                )}
              />
            </aside>
            </div>
          </section>
        ) : (
          <section className="admin-theme">
            <div className="view-intro view-intro--admin">
              <div className="view-intro__eyebrow">Ops & Strategy</div>
              <div className="view-intro__headline">运营工作台</div>
              <div className="view-intro__copy">
                面向策略和运营的控制视图。重点突出指标、索引状态、用户画像与商品维护，用更冷静的结构承接高密度信息。
              </div>
              <div className="view-intro__chips">
                <span className="view-intro__chip">效果看板</span>
                <span className="view-intro__chip">索引控制</span>
                <span className="view-intro__chip">画像维护</span>
                <span className="view-intro__chip">商品治理</span>
              </div>
            </div>

            <div className="admin-layout">
            <div className="admin-topbar">
              <div className="admin-topbar__summary">
                {adminOverview.map((item) => (
                  <div key={item.label} className="admin-overview-card">
                    <div className="admin-overview-card__label">{item.label}</div>
                    <div className="admin-overview-card__value">{item.value}</div>
                    <div className="admin-overview-card__hint">{item.hint}</div>
                  </div>
                ))}
              </div>

              <div className="admin-topbar__tabs">
                <SegmentedTabs
                  options={[
                    { label: "效果看板", value: "dashboard" },
                    { label: "向量索引", value: "vector" },
                    { label: "用户画像", value: "profiles" },
                    { label: "商品管理", value: "products" },
                  ]}
                  value={adminTab}
                  onChange={setAdminTab}
                  dark
                />
              </div>
            </div>

            {adminTab === "dashboard" && analyticsDashboard ? (
              <div className="admin-stack">
                <SectionCard
                  title="推荐效果看板"
                  subtitle="漏斗、热门查询和商品反馈都集中展示，适合做本机调优观察。"
                  tone="admin"
                  eyebrow="Performance Lens"
                >
                  <div className="stats-grid stats-grid--dashboard">
                    <StatCard label="请求" value={analyticsDashboard.funnel.requests} tone="admin" />
                    <StatCard label="点击" value={analyticsDashboard.funnel.clicks} tone="admin" />
                    <StatCard label="收藏" value={analyticsDashboard.funnel.favorites} tone="admin" />
                    <StatCard label="想下单" value={analyticsDashboard.funnel.purchases} tone="admin" />
                  </div>
                </SectionCard>

                {analyticsEvaluation ? (
                  <SectionCard
                    title="推荐评估样本"
                    subtitle="固定样本集用于追踪推荐质量变化，帮助判断模型、规则和排序调整是否真的变好。"
                    tone="admin"
                    eyebrow="Evaluation Suite"
                  >
                    <div className="stats-grid stats-grid--dashboard">
                      <StatCard
                        label="样本总数"
                        value={filteredEvaluationSummary.totalCases}
                        hint="当前筛选下的评估 case 数"
                        tone="admin"
                      />
                      <StatCard
                        label="通过率"
                        value={formatRatio(filteredEvaluationSummary.passRate)}
                        hint={`通过 ${filteredEvaluationSummary.passedCases} 条 · 待优化 ${filteredEvaluationSummary.failedCases} 条`}
                        tone="admin"
                      />
                      <StatCard
                        label="Top1 命中"
                        value={formatRatio(filteredEvaluationSummary.top1HitRate)}
                        hint={`类目命中 ${formatRatio(filteredEvaluationSummary.categoryHitRate)}`}
                        tone="admin"
                      />
                      <StatCard
                        label="预算命中"
                        value={formatRatio(filteredEvaluationSummary.budgetHitRate)}
                        hint={`品牌命中 ${formatRatio(filteredEvaluationSummary.brandHitRate)}`}
                        tone="admin"
                      />
                    </div>

                    <div className="eval-toolbar">
                      <div className="eval-toolbar__meta">
                        <div className="eval-toolbar__label">按维度查看</div>
                        <div className="eval-toolbar__hint">失败样本会自动排在前面，方便集中定位问题。</div>
                      </div>
                      <SegmentedTabs
                        options={[
                          { label: "全部", value: "all" },
                          { label: "待优化", value: "failed" },
                          { label: "耳机", value: "耳机" },
                          { label: "手机", value: "手机" },
                          { label: "笔记本", value: "笔记本" },
                          { label: "用户画像", value: "profile" },
                          { label: "预算约束", value: "budget" },
                        ]}
                        value={evaluationFilter}
                        onChange={setEvaluationFilter}
                      />
                    </div>

                    <div className="eval-summary-row">
                      <span className="chip chip--neutral">当前筛选 {filteredEvaluationSummary.totalCases} 条</span>
                      <span className="chip chip--amber">待优化 {filteredEvaluationSummary.failedCases} 条</span>
                      <span className="chip chip--emerald">通过 {filteredEvaluationSummary.passedCases} 条</span>
                    </div>

                    {topEvaluationIssues.length ? (
                      <div className="eval-insight-banner">
                        <div className="eval-insight-banner__label">问题热点</div>
                        <div className="eval-insight-banner__content">
                          {topEvaluationIssues.map((issue) => (
                            <span key={issue.label} className="eval-insight-badge">
                              {issue.label} · {issue.count} 条
                            </span>
                          ))}
                        </div>
                      </div>
                    ) : null}

                    {categoryIssueInsights.length ? (
                      <div className="eval-category-banner">
                        <div className="eval-category-banner__label">类目诊断</div>
                        <div className="eval-category-banner__content">
                          {categoryIssueInsights.map((item) => (
                            <div key={item.category} className="eval-category-card">
                              <div className="eval-category-card__title">{item.category}类</div>
                              <div className="eval-category-card__issue">最常见: {item.topIssue}</div>
                              <div className="eval-category-card__meta">涉及 {item.count} 条待优化样本</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : null}

                    {categoryProductSignals.length ? (
                      <div className="eval-product-banner">
                        <div className="eval-category-banner__label">问题商品与品牌线索</div>
                        <div className="eval-product-banner__content">
                          {categoryProductSignals.map((item) => (
                            <div key={item.category} className="eval-product-card">
                              <div className="eval-product-card__title">{item.category}类</div>
                              <div className="eval-product-card__row">
                                <span className="eval-product-card__tag">目标</span>
                                <div>
                                  <div className="eval-product-card__value">{item.targetProduct}</div>
                                  <div className="eval-product-card__meta">{item.targetBrand}</div>
                                </div>
                              </div>
                              <div className="eval-product-card__row">
                                <span className="eval-product-card__tag eval-product-card__tag--actual">当前偏向</span>
                                <div>
                                  <div className="eval-product-card__value">{item.actualProduct}</div>
                                  <div className="eval-product-card__meta">{item.actualBrand}</div>
                                </div>
                              </div>
                              <div className="eval-product-card__foot">涉及 {item.count} 条待优化样本</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : null}

                    <div className="eval-case-grid">
                      {sortedEvaluationCases.map((item) => {
                        const issues = getEvaluationIssues(item);
                        return (
                          <div
                            key={item.case_id}
                            className={`eval-case${item.passed ? "" : " eval-case--attention"}`}
                          >
                            <div className="eval-case__header">
                              <div>
                                <div className="eval-case__title">{item.query}</div>
                                <div className="eval-case__meta">
                                  期望 Top1: {item.expected_top_product || "未定义"}
                                </div>
                              </div>
                              <span
                                className={`status-pill ${
                                  item.passed ? "status-pill--success" : "status-pill--warning"
                                }`}
                              >
                                {item.passed ? "通过" : "待优化"}
                              </span>
                            </div>

                            <div className="eval-case__body">
                              <div>实际 Top1: {item.actual_top_product || "无结果"}</div>
                              <div>类目: {item.actual_category || "-"}</div>
                              <div>品牌: {item.actual_brand || "-"}</div>
                              <div>
                                价格: {typeof item.actual_price === "number" ? formatMoney(item.actual_price) : "-"}
                              </div>
                            </div>

                            {!item.passed ? (
                              <div className="eval-case__diagnosis">
                                <div className="eval-case__diagnosis-title">待优化原因</div>
                                <div className="eval-case__diagnosis-list">
                                  {issues.length ? (
                                    issues.map((issue) => (
                                      <span key={`${item.case_id}-${issue}`} className="eval-issue-badge">
                                        {issue}
                                      </span>
                                    ))
                                  ) : (
                                    <span className="eval-issue-badge">需要进一步排查</span>
                                  )}
                                </div>
                              </div>
                            ) : null}

                            <div className="chip-row chip-row--admin">
                              <span className={`chip ${item.top1_hit ? "chip--emerald" : "chip--neutral"}`}>
                                Top1 {item.top1_hit ? "命中" : "未命中"}
                              </span>
                              <span className={`chip ${item.category_hit ? "chip--sky" : "chip--neutral"}`}>
                                类目 {item.category_hit ? "命中" : "未命中"}
                              </span>
                              {item.user_id ? <span className="chip chip--sky">画像样本</span> : null}
                              {item.brand_hit != null ? (
                                <span className={`chip ${item.brand_hit ? "chip--emerald" : "chip--neutral"}`}>
                                  品牌 {item.brand_hit ? "命中" : "未命中"}
                                </span>
                              ) : null}
                              {item.budget_hit != null ? (
                                <span className={`chip ${item.budget_hit ? "chip--amber" : "chip--neutral"}`}>
                                  预算 {item.budget_hit ? "命中" : "未命中"}
                                </span>
                              ) : null}
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {filteredEvaluationCases.length === 0 ? (
                      <div className="empty-state empty-state--compact">当前筛选下暂无评估样本。</div>
                    ) : null}
                  </SectionCard>
                ) : null}

                <div className="admin-grid">
                  <MiniList
                    title="热门查询表现"
                    items={analyticsDashboard.query_performance}
                    tone="admin"
                    renderItem={(item) => (
                      <div key={item.query} className="mini-item">
                        <div className="mini-item__title">{item.query}</div>
                        <div className="mini-item__meta">
                          请求 {item.request_count} · 点击 {item.click_count} · 收藏 {item.favorite_count} · 想下单 {item.purchase_count}
                        </div>
                        <div className="mini-item__meta">
                          点击率 {formatPercent(item.click_rate)} · 想下单率 {formatPercent(item.purchase_rate)}
                        </div>
                      </div>
                    )}
                  />

                  <MiniList
                    title="商品反馈表现"
                    items={analyticsDashboard.product_performance}
                    tone="admin"
                    renderItem={(item) => (
                      <div key={item.product_name} className="mini-item">
                        <div className="mini-item__title">{item.product_name}</div>
                        <div className="mini-item__meta">
                          被推荐 {item.recommend_count} · 点击 {item.click_count} · 收藏 {item.favorite_count} · 想下单 {item.purchase_count}
                        </div>
                        <div className="mini-item__meta">
                          点击率 {formatPercent(item.click_rate)} · 想下单率 {formatPercent(item.purchase_rate)}
                        </div>
                      </div>
                    )}
                  />
                </div>

                <div className="admin-grid">
                  <MiniList
                    title="最近搜索"
                    items={analyticsDashboard.recent_searches}
                    tone="admin"
                    renderItem={(item) => (
                      <div key={item.event_id} className="mini-item">
                        <div className="mini-item__title">{item.query || "图片搜索"}</div>
                        <div className="mini-item__meta">
                          Top 商品 {item.top_product_name || "暂无"} · 商家 {item.best_store || "暂无"}
                        </div>
                      </div>
                    )}
                  />

                  <MiniList
                    title="最近反馈"
                    items={analyticsDashboard.recent_feedback}
                    tone="admin"
                    renderItem={(item) => (
                      <div key={item.event_id} className="mini-item">
                        <div className="mini-item__title">{item.product_name || `商品 ${item.product_id}`}</div>
                        <div className="mini-item__meta">
                          {item.event_type} · {item.query || "无查询上下文"}
                        </div>
                      </div>
                    )}
                  />
                </div>
              </div>
            ) : null}

            {adminTab === "vector" && vectorStatus ? (
              <SectionCard
                title="本机向量索引"
                subtitle="只保留和索引维护相关的信息，避免和其他模块混在一起。"
                tone="admin"
                eyebrow="Vector Runtime"
                actions={
                  <>
                    <button
                      onClick={() => handleRebuildVectorIndex(true)}
                      className="button button--primary"
                      disabled={vectorActionLoading}
                    >
                      重建并落盘
                    </button>
                    <button
                      onClick={() => handleRebuildVectorIndex(false)}
                      className="button button--ghost"
                      disabled={vectorActionLoading}
                    >
                      仅重建内存索引
                    </button>
                  </>
                }
              >
                <div className="stats-grid stats-grid--dashboard">
                  <StatCard label="后端" value={vectorStatus.backend} tone="admin" />
                  <StatCard label="状态" value={vectorStatus.ready ? "Ready" : "Not Ready"} tone="admin" />
                  <StatCard label="来源" value={vectorStatus.load_source} tone="admin" />
                  <StatCard label="商品数" value={vectorStatus.product_count} tone="admin" />
                </div>
              </SectionCard>
            ) : null}

            {adminTab === "profiles" ? (
              <SectionCard
                title="用户画像管理"
                subtitle="先在搜索工作台填好用户 ID，也可以直接在这里载入并维护画像。"
                tone="admin"
                eyebrow="Profile Studio"
                actions={
                  <>
                    <button
                      onClick={handleLoadProfile}
                      className="button button--ghost"
                      disabled={profileActionLoading || !userId.trim()}
                    >
                      载入画像
                    </button>
                    <button
                      onClick={handleSaveProfile}
                      className="button button--primary"
                      disabled={profileActionLoading || !userId.trim()}
                    >
                      保存画像
                    </button>
                  </>
                }
              >
                <div className="form-grid">
                  <input
                    type="text"
                    value={profileForm.preferredBrand}
                    onChange={(e) => handleProfileFormChange("preferredBrand", e.target.value)}
                    placeholder="偏好品牌，逗号分隔"
                    className="field"
                  />
                  <input
                    type="text"
                    value={profileForm.preferredCategories}
                    onChange={(e) => handleProfileFormChange("preferredCategories", e.target.value)}
                    placeholder="偏好分类，逗号分隔"
                    className="field"
                  />
                  <input
                    type="number"
                    value={profileForm.budgetMin}
                    onChange={(e) => handleProfileFormChange("budgetMin", e.target.value)}
                    placeholder="预算下限"
                    className="field"
                  />
                  <input
                    type="number"
                    value={profileForm.budgetMax}
                    onChange={(e) => handleProfileFormChange("budgetMax", e.target.value)}
                    placeholder="预算上限"
                    className="field"
                  />
                  <input
                    type="text"
                    value={profileForm.interests}
                    onChange={(e) => handleProfileFormChange("interests", e.target.value)}
                    placeholder="兴趣点，逗号分隔"
                    className="field"
                  />
                  <select
                    value={profileForm.priceSensitivity}
                    onChange={(e) => handleProfileFormChange("priceSensitivity", e.target.value)}
                    className="field"
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
                    className="field field--full"
                  />
                </div>
              </SectionCard>
            ) : null}

            {adminTab === "products" ? (
              <div className="product-layout">
                <SectionCard
                  title="商品表单"
                  subtitle="新增或编辑商品时，集中维护核心字段；商品列表放到右侧，避免目录和表单互相打断。"
                  tone="admin"
                  eyebrow="Catalog Editor"
                  actions={
                    <>
                      <button
                        onClick={handleSaveProduct}
                        className="button button--primary"
                        disabled={productActionLoading}
                      >
                        {productForm.id ? "保存修改" : "新增商品"}
                      </button>
                      <button
                        onClick={resetProductForm}
                        className="button button--ghost"
                        disabled={productActionLoading}
                      >
                        清空
                      </button>
                    </>
                  }
                >
                  <div className="form-grid">
                    <input
                      type="text"
                      value={productForm.name}
                      onChange={(e) => handleProductFormChange("name", e.target.value)}
                      placeholder="商品名"
                      className="field"
                    />
                    <input
                      type="text"
                      value={productForm.brand}
                      onChange={(e) => handleProductFormChange("brand", e.target.value)}
                      placeholder="品牌"
                      className="field"
                    />
                    <input
                      type="text"
                      value={productForm.category}
                      onChange={(e) => handleProductFormChange("category", e.target.value)}
                      placeholder="分类"
                      className="field"
                    />
                    <input
                      type="text"
                      value={productForm.subcategory}
                      onChange={(e) => handleProductFormChange("subcategory", e.target.value)}
                      placeholder="子分类"
                      className="field"
                    />
                    <input
                      type="number"
                      value={productForm.price}
                      onChange={(e) => handleProductFormChange("price", e.target.value)}
                      placeholder="价格"
                      className="field"
                    />
                    <input
                      type="number"
                      step="0.1"
                      value={productForm.rating}
                      onChange={(e) => handleProductFormChange("rating", e.target.value)}
                      placeholder="评分"
                      className="field"
                    />
                    <input
                      type="number"
                      value={productForm.monthlySales}
                      onChange={(e) => handleProductFormChange("monthlySales", e.target.value)}
                      placeholder="月销量"
                      className="field"
                    />
                    <input
                      type="number"
                      value={productForm.inventoryTotal}
                      onChange={(e) => handleProductFormChange("inventoryTotal", e.target.value)}
                      placeholder="总库存"
                      className="field"
                    />
                    <input
                      type="text"
                      value={productForm.promotionTag}
                      onChange={(e) => handleProductFormChange("promotionTag", e.target.value)}
                      placeholder="促销标签"
                      className="field"
                    />
                    <input
                      type="text"
                      value={productForm.tags}
                      onChange={(e) => handleProductFormChange("tags", e.target.value)}
                      placeholder="标签，逗号分隔"
                      className="field"
                    />
                  </div>
                  <textarea
                    value={productForm.description}
                    onChange={(e) => handleProductFormChange("description", e.target.value)}
                    placeholder="商品描述"
                    rows={4}
                    className="textarea"
                  />
                </SectionCard>

                <SectionCard
                  title="商品目录"
                  subtitle="右侧只保留浏览和快速操作，方便更快定位要维护的商品。"
                  tone="admin"
                  eyebrow="Catalog Browser"
                >
                  <div className="catalog-list">
                    {products.map((product) => (
                      <div key={product.id} className="catalog-item">
                        <div>
                          <div className="catalog-item__title">{product.name}</div>
                          <div className="catalog-item__meta">
                            {product.brand} · {product.category} · ¥{product.price}
                          </div>
                        </div>
                        <div className="catalog-item__actions">
                          <button
                            onClick={() => handleEditProduct(product)}
                            className="button button--ghost"
                          >
                            编辑
                          </button>
                          <button
                            onClick={() => handleDeleteProduct(product.id)}
                            className="button button--danger"
                            disabled={productActionLoading}
                          >
                            删除
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </SectionCard>
              </div>
            ) : null}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
