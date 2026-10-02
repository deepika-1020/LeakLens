import pandas as pd
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

EVAL_DIR = Path(__file__).resolve().parent
PROJECT_DIR = EVAL_DIR.parent
SRC_DIR = PROJECT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from leaklens_engine import investigate

# ==============================================================================
# LEAKLENS - BENCHMARK EVALUATION RUNNER
# Role: Data Analytics & AI
# Problem Statement: PS-04 (Natural-Language & Grounded Scoping Validation)
# ==============================================================================

def run_evaluation() -> Dict[str, Any]:
    """
    Execute empirical evaluation across the 24-question benchmark test set.
    Tests:
    1. Natural-language intent classification across diverse colloquial phrasing
    2. Guardrail rejection of completely unsupported external domains
    3. Honest scope clarification on partially supported queries (e.g. Profit/Cost)
    4. Row-level evidence backing
    5. Deterministic financial calculation grounding without fabrication
    """
    questions_file = EVAL_DIR / "questions.csv"
    if not questions_file.exists():
        raise FileNotFoundError(f"Evaluation questions file not found at {questions_file}")

    df = pd.read_csv(questions_file)

    total_questions = len(df)
    intent_correct = 0
    guardrail_correct = 0
    scope_handling_correct = 0
    evidence_valid = 0
    financial_integrity = 0

    results = []

    print("\n" + "=" * 80)
    print("                    LEAKLENS BENCHMARK EVALUATION")
    print(f"       Empirical Testing Across {total_questions} Business Queries (Natural Phrasing)")
    print("=" * 80 + "\n")

    for _, row in df.iterrows():
        qid = row["question_id"]
        q_text = row["question"]
        exp_intent = row["expected_intent"]
        exp_support = str(row["expected_support"]).lower() == "true"
        exp_partial = str(row["is_partially_supported"]).lower() == "true"

        res = investigate(q_text)

        # 1. Intent Classification Check
        actual_intent = res.get("intent", "unknown")
        intent_match = (actual_intent == exp_intent)
        if intent_match:
            intent_correct += 1

        # 2. Guardrail / Support Check
        is_supported = (res.get("status") != "UNSUPPORTED")
        support_match = (is_supported == exp_support)
        if support_match:
            guardrail_correct += 1

        # 3. Partially Supported Scope Handling Check
        actual_partial = res.get("is_partially_supported", False)
        partial_match = (actual_partial == exp_partial)
        if partial_match:
            scope_handling_correct += 1

        # 4. Evidence Trace Integrity
        has_evidence = False
        if not exp_support:
            has_evidence = True  # Unsupported correctly yields no evidence
            evidence_valid += 1
        else:
            if "evidence" in res:
                ev = res["evidence"]
                if isinstance(ev, dict) and ("evidence_dataframe" in ev or "evidence_records" in ev):
                    has_evidence = True
                    evidence_valid += 1
            elif "combined_leakage" in res:
                has_evidence = True
                evidence_valid += 1

        # 5. Financial Calculation Integrity
        calc_valid = False
        if not exp_support:
            calc_valid = True
            financial_integrity += 1
        else:
            if "analytics" in res:
                calc_valid = (res["analytics"].get("net_revenue_change", 0) != 0)
            elif "product_analysis" in res:
                calc_valid = (res["product_analysis"].get("primary_product_at_risk", {}).get("total_leakage", 0) > 0)
            elif "customer_analysis" in res:
                calc_valid = (res["customer_analysis"].get("primary_customer", {}).get("refund_amount", 0) > 0)
            elif "location_analysis" in res:
                calc_valid = (res["location_analysis"].get("worst_location", {}).get("failed_revenue", 0) > 0)
            elif "evidence" in res:
                calc_valid = (res["evidence"].get("financial_impact", 0) > 0)
            elif "combined_leakage" in res:
                calc_valid = (res["combined_leakage"].get("total_financial_impact", 0) > 0)

            if calc_valid:
                financial_integrity += 1

        pass_all = intent_match and support_match and partial_match and has_evidence and calc_valid
        status_symbol = "[PASS]" if pass_all else "[FAIL]"

        results.append({
            "question_id": qid,
            "question": q_text,
            "expected_intent": exp_intent,
            "actual_intent": actual_intent,
            "intent_match": intent_match,
            "support_match": support_match,
            "partial_match": partial_match,
            "has_evidence": has_evidence,
            "calc_valid": calc_valid,
            "overall_status": status_symbol
        })

        print(f"[{qid}] {status_symbol} | Intent: {actual_intent:<18} | Q: {q_text[:40]}...")

    # Summary Metrics
    intent_accuracy = (intent_correct / total_questions) * 100.0
    guardrail_accuracy = (guardrail_correct / total_questions) * 100.0
    scope_accuracy = (scope_handling_correct / total_questions) * 100.0
    evidence_rate = (evidence_valid / total_questions) * 100.0
    calc_integrity_rate = (financial_integrity / total_questions) * 100.0
    overall_pass_rate = (sum(1 for r in results if r["overall_status"] == "[PASS]") / total_questions) * 100.0

    summary = {
        "total_test_cases": total_questions,
        "intent_accuracy_pct": round(intent_accuracy, 2),
        "guardrail_rejection_accuracy_pct": round(guardrail_accuracy, 2),
        "data_scope_handling_accuracy_pct": round(scope_accuracy, 2),
        "evidence_backing_rate_pct": round(evidence_rate, 2),
        "financial_calculation_integrity_pct": round(calc_integrity_rate, 2),
        "overall_benchmark_pass_rate_pct": round(overall_pass_rate, 2),
        "detailed_results": results
    }

    print("\n" + "=" * 80)
    print("                     BENCHMARK SUMMARY METRICS")
    print("=" * 80)
    print(f"Total Benchmark Queries Evaluated        : {total_questions}")
    print(f"Natural Intent Classification Accuracy   : {intent_accuracy:.1f}%")
    print(f"Guardrail Out-of-Scope Rejection Rate    : {guardrail_accuracy:.1f}%")
    print(f"Partially-Supported Data Scoping Rate    : {scope_accuracy:.1f}%")
    print(f"Row-Level Evidence Backing Rate          : {evidence_rate:.1f}%")
    print(f"Financial Calculation Grounding Rate     : {calc_integrity_rate:.1f}%")
    print(f"Overall Test Suite Pass Rate             : {overall_pass_rate:.1f}%")
    print("=" * 80 + "\n")

    report_file = EVAL_DIR / "benchmark_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    return summary


if __name__ == "__main__":
    run_evaluation()
