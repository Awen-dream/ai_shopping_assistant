def ensure_query_category(
    query: str,
    user_profile: dict,
    category_embedding,
    fallback_category_classifier,
) -> dict:
    normalized_profile = dict(user_profile or {})
    if not normalized_profile.get("category"):
        normalized_profile["category"] = (
            category_embedding.classify_query(query)
            or fallback_category_classifier(query)
            or ""
        )
    return normalized_profile


def hybrid_recall_candidates(
    query: str,
    query_context: dict,
    vector_retriever,
    keyword_retriever,
    products: list[dict],
) -> list[dict]:
    vector_results = vector_retriever.search(query, topk=20)
    keyword_results = keyword_retriever.search(query)
    merged: dict[int, dict] = {}

    max_keyword_score = max((score for _, score in keyword_results), default=1.0)
    vector_scores = [score for _, score in vector_results]
    max_vector_score = max(vector_scores, default=1.0)
    min_vector_score = min(vector_scores, default=0.0)

    for product, score in keyword_results:
        merged[product["id"]] = {
            "product": product,
            "keyword_score": min(score / max_keyword_score, 1.0),
            "vector_score": 0.0,
        }

    for product, score in vector_results:
        if max_vector_score == min_vector_score:
            normalized_vector_score = 1.0 if max_vector_score > 0 else 0.0
        else:
            normalized_vector_score = (score - min_vector_score) / (max_vector_score - min_vector_score)
        merged.setdefault(
            product["id"],
            {"product": product, "keyword_score": 0.0, "vector_score": 0.0},
        )
        merged[product["id"]]["vector_score"] = max(
            merged[product["id"]]["vector_score"],
            normalized_vector_score,
        )

    candidates = list(merged.values()) or [
        {"product": product, "keyword_score": 0.0, "vector_score": 0.0}
        for product in products
    ]

    if query_context["category"]:
        candidates = [
            item for item in candidates
            if item["product"].get("category") == query_context["category"]
        ] or candidates

    if query_context["preferred_brand"]:
        brand_matched = [
            item for item in candidates
            if item["product"].get("brand") in query_context["preferred_brand"]
        ]
        if brand_matched:
            candidates = brand_matched

    if query_context["preferred_categories"] and not query_context["category"]:
        preferred_category_candidates = [
            item for item in candidates
            if item["product"].get("category") in query_context["preferred_categories"]
        ]
        if preferred_category_candidates:
            candidates = preferred_category_candidates

    budget_low, budget_high = query_context["budget_range"]
    budget_matched = [
        item for item in candidates
        if budget_low <= item["product"].get("price", 0) <= budget_high
    ]
    if budget_matched:
        candidates = budget_matched

    return candidates


def materialize_recommendation_results(top_ranked_items, reasons: list[str]) -> list[dict]:
    results = []
    for (product, score, detail), reason in zip(top_ranked_items, reasons):
        matched_features = {
            "matched_terms": detail.get("matched_terms", [])[:4],
            "matched_interests": detail.get("matched_interests", []),
            "matched_required_features": detail.get("matched_required_features", []),
            "matched_feature_highlights": detail.get("matched_feature_highlights", []),
            "matched_use_cases": detail.get("matched_use_cases", []),
            "matched_target_users": detail.get("matched_target_users", []),
            "category_match": detail.get("category_match", False),
            "brand_match": detail.get("brand_match", False),
            "budget_match": detail.get("budget_match", False),
            "scenario_score": detail.get("scenario_score", 0.0),
            "sort_bonus": detail.get("sort_bonus", 0.0),
        }

        item = product.copy()
        item["reason"] = reason
        item["match_score"] = round(score, 4)
        item["matched_features"] = matched_features
        results.append(item)

    return results


def recommend_products_with_components(
    query: str,
    user_profile: dict | None,
    *,
    intent_agent,
    category_embedding,
    fallback_category_classifier,
    query_context_builder,
    ranker,
    reasoner,
    vector_retriever,
    keyword_retriever,
    products: list[dict],
    topk: int = 5,
) -> list[dict]:
    resolved_profile = user_profile or intent_agent.parse_intent(query)
    resolved_profile = ensure_query_category(
        query,
        resolved_profile,
        category_embedding,
        fallback_category_classifier,
    )
    query_context = query_context_builder.build(query, resolved_profile)
    recalled = hybrid_recall_candidates(
        query,
        query_context,
        vector_retriever,
        keyword_retriever,
        products,
    )
    ranked = ranker.rank(recalled, query_context)
    top_ranked_items = ranked[:topk]
    reasons = reasoner.generate_batch(top_ranked_items, resolved_profile)
    return materialize_recommendation_results(top_ranked_items, reasons)
