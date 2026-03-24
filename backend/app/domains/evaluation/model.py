def evaluate_case(case: dict, results: list[dict]) -> dict:
    top_result = results[0] if results else {}
    expected_top_product = case.get("expected_top_product")
    expected_category = case.get("expected_category")
    expected_brand = case.get("expected_brand")
    max_price = case.get("max_price")

    actual_product = top_result.get("name")
    actual_category = top_result.get("category")
    actual_brand = top_result.get("brand")
    actual_price = top_result.get("price")

    top1_hit = bool(expected_top_product and actual_product == expected_top_product)
    category_hit = bool(expected_category and actual_category == expected_category)
    brand_hit = bool(expected_brand and actual_brand == expected_brand)
    budget_hit = bool(max_price is None or (isinstance(actual_price, (int, float)) and actual_price <= max_price))

    passed = top1_hit and category_hit and brand_hit if expected_brand else top1_hit and category_hit
    if max_price is not None:
        passed = passed and budget_hit

    return {
        "case_id": case.get("case_id"),
        "query": case.get("query", ""),
        "user_id": case.get("user_id"),
        "expected_top_product": expected_top_product,
        "expected_category": expected_category,
        "expected_brand": expected_brand,
        "max_price": max_price,
        "result_count": len(results),
        "actual_top_product": actual_product,
        "actual_category": actual_category,
        "actual_brand": actual_brand,
        "actual_price": actual_price,
        "top1_hit": top1_hit,
        "category_hit": category_hit,
        "brand_hit": brand_hit if expected_brand else None,
        "budget_hit": budget_hit if max_price is not None else None,
        "passed": passed,
    }


def summarize_evaluation(case_results: list[dict]) -> dict:
    total_cases = len(case_results)
    if total_cases == 0:
        return {
            "total_cases": 0,
            "passed_cases": 0,
            "pass_rate": 0.0,
            "top1_hit_rate": 0.0,
            "category_hit_rate": 0.0,
            "brand_hit_rate": 0.0,
            "budget_hit_rate": 0.0,
        }

    top1_hits = sum(1 for item in case_results if item["top1_hit"])
    category_hits = sum(1 for item in case_results if item["category_hit"])
    brand_cases = [item for item in case_results if item["brand_hit"] is not None]
    budget_cases = [item for item in case_results if item["budget_hit"] is not None]
    passed_cases = sum(1 for item in case_results if item["passed"])

    return {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "pass_rate": round(passed_cases / total_cases, 2),
        "top1_hit_rate": round(top1_hits / total_cases, 2),
        "category_hit_rate": round(category_hits / total_cases, 2),
        "brand_hit_rate": round(
            sum(1 for item in brand_cases if item["brand_hit"]) / max(len(brand_cases), 1),
            2,
        ),
        "budget_hit_rate": round(
            sum(1 for item in budget_cases if item["budget_hit"]) / max(len(budget_cases), 1),
            2,
        ),
    }
