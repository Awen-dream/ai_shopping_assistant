from .runtime import get_coordinator
from ..domains.evaluation import evaluate_case, load_evaluation_cases, summarize_evaluation


class EvaluationApplicationService:
    def run_recommendation_evaluation(self):
        coordinator = get_coordinator()
        cases = load_evaluation_cases()
        case_results = []

        for case in cases:
            results = coordinator.handle_query(
                query=case.get("query", ""),
                user_id=case.get("user_id"),
            )
            case_results.append(evaluate_case(case, results))

        return {
            "summary": summarize_evaluation(case_results),
            "cases": case_results,
        }
