import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from query_router import route_query
from trend_analyzer import compare_periods, get_monthly_metrics
from revenue_investigator import investigate_revenue_decline
from evidence_engine import refund_evidence, delivery_evidence, discount_evidence
from product_analyzer import analyze_product_leakage
from customer_analyzer import analyze_customer_leakage, analyze_location_delivery_risk
from reasoner import generate_business_explanation
from audit_logger import log_decision, get_audit_trail
from data_loader import get_unified_orders

# ==============================================================================
# LEAKLENS - UNIFIED DECISION & INVESTIGATION ORCHESTRATOR
# Role: Data Analytics & AI
# Problem Statement: PS-04 (Natural-Language Decision Engine)
# ==============================================================================

def investigate(question: str) -> Dict[str, Any]:
    """
    Main entry point for natural-language business investigations.
    Orchestrates query interpretation, deterministic analytical modules,
    record-level evidence extraction, AI synthesis, and human approval readiness.
    """
    query_id = f"QRY-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    # Step 1: Intelligent NLU Query Routing & Filter Extraction
    route = route_query(question)

    if not route["is_supported"]:
        return {
            "status": "UNSUPPORTED",
            "query_id": query_id,
            "question": question,
            "intent": route["intent"],
            "message": route["rejection_reason"],
            "requires_human_approval": False
        }

    intent = route["intent"]
    unified_df = get_unified_orders()
    filters = route.get("extracted_filters", {})
    is_partially_supported = route.get("is_partially_supported", False)
    scope_clarification = route.get("scope_clarification", "")

    # Step 2: Dispatch to Analytical Core
    if intent == "revenue_trend":
        investigation_result = investigate_revenue_decline(
            unified_df=unified_df,
            current_period=route.get("target_period"),
            previous_period=route.get("comparison_period")
        )
        
        structured_facts = {
            "investigation_type": "revenue_trend",
            "current_label": investigation_result.get("current_label"),
            "previous_label": investigation_result.get("previous_label"),
            "net_revenue_change": investigation_result.get("net_revenue_change", 0.0),
            "percentage_change": investigation_result.get("percentage_change", 0.0),
            "direction": "DECLINE" if investigation_result.get("status") == "DECLINE_DETECTED" else "GROWTH",
            "primary_driver": investigation_result.get("primary_driver", {}).get("name", "N/A"),
            "top_category": investigation_result.get("root_cause_dimensions", {}).get("top_category", {}).get("name", "N/A"),
            "top_location": investigation_result.get("root_cause_dimensions", {}).get("top_location", {}).get("name", "N/A"),
            "is_partially_supported": is_partially_supported,
            "scope_clarification": scope_clarification
        }

        ai_synthesis = generate_business_explanation(structured_facts, question)

        return {
            "status": "SUCCESS",
            "query_id": query_id,
            "question": question,
            "intent": "revenue_trend",
            "is_partially_supported": is_partially_supported,
            "scope_clarification": scope_clarification,
            "route_details": route,
            "analytics": investigation_result,
            "ai_synthesis": ai_synthesis,
            "evidence": investigation_result.get("evidence_trace", {}),
            "requires_human_approval": True,
            "approval_status": "PENDING"
        }

    elif intent == "product_leakage":
        prod_result = analyze_product_leakage(
            unified_df=unified_df,
            category=filters.get("category"),
            period=route.get("target_period") if route.get("has_explicit_period") else None
        )

        p_info = prod_result["primary_product_at_risk"]
        structured_facts = {
            "investigation_type": "product_leakage",
            "primary_product": p_info["product_id"],
            "category": p_info["category"],
            "total_leakage": p_info["total_leakage"],
            "leakage_ratio_pct": p_info["leakage_ratio_pct"],
            "net_revenue": p_info["net_revenue"],
            "is_partially_supported": is_partially_supported,
            "scope_clarification": scope_clarification
        }

        ai_synthesis = generate_business_explanation(structured_facts, question)

        return {
            "status": "SUCCESS",
            "query_id": query_id,
            "question": question,
            "intent": "product_leakage",
            "is_partially_supported": is_partially_supported,
            "scope_clarification": scope_clarification,
            "route_details": route,
            "product_analysis": prod_result,
            "evidence": prod_result.get("evidence_trace", {}),
            "ai_synthesis": ai_synthesis,
            "requires_human_approval": True,
            "approval_status": "PENDING"
        }

    elif intent == "customer_leakage":
        cust_result = analyze_customer_leakage(unified_df=unified_df)
        c_info = cust_result["primary_customer"]
        s_info = cust_result["primary_segment"]

        structured_facts = {
            "investigation_type": "customer_leakage",
            "top_customer": c_info["customer_id"],
            "refund_amount": c_info["refund_amount"],
            "top_segment": s_info["name"],
            "segment_leakage": s_info["leakage_amount"],
            "is_partially_supported": is_partially_supported,
            "scope_clarification": scope_clarification
        }

        ai_synthesis = generate_business_explanation(structured_facts, question)

        return {
            "status": "SUCCESS",
            "query_id": query_id,
            "question": question,
            "intent": "customer_leakage",
            "is_partially_supported": is_partially_supported,
            "scope_clarification": scope_clarification,
            "route_details": route,
            "customer_analysis": cust_result,
            "evidence": cust_result.get("evidence_trace", {}),
            "ai_synthesis": ai_synthesis,
            "requires_human_approval": True,
            "approval_status": "PENDING"
        }

    elif intent == "refund_leakage":
        evidence = refund_evidence(
            unified_df=unified_df,
            category=filters.get("category"),
            period=route.get("target_period") if route.get("has_explicit_period") else None
        )

        structured_facts = {
            "investigation_type": "refund_leakage",
            "primary_category": evidence["primary_category"],
            "primary_reason": evidence["primary_reason"],
            "financial_impact": evidence["financial_impact"],
            "category_share": evidence["category_share"]
        }

        ai_synthesis = generate_business_explanation(structured_facts, question)

        return {
            "status": "SUCCESS",
            "query_id": query_id,
            "question": question,
            "intent": "refund_leakage",
            "is_partially_supported": is_partially_supported,
            "scope_clarification": scope_clarification,
            "route_details": route,
            "evidence": evidence,
            "ai_synthesis": ai_synthesis,
            "requires_human_approval": True,
            "approval_status": "PENDING"
        }

    elif intent == "delivery_risk":
        # Check if question was city/location focused
        if "city" in question.lower() or "location" in question.lower() or filters.get("location"):
            loc_result = analyze_location_delivery_risk(unified_df=unified_df)
            w_loc = loc_result["worst_location"]

            structured_facts = {
                "investigation_type": "delivery_risk",
                "primary_category": "Logistics",
                "primary_location": w_loc["name"],
                "financial_impact": w_loc["failed_revenue"],
                "category_share": w_loc["loss_share_pct"]
            }
            ai_synthesis = generate_business_explanation(structured_facts, question)

            return {
                "status": "SUCCESS",
                "query_id": query_id,
                "question": question,
                "intent": "delivery_risk",
                "route_details": route,
                "location_analysis": loc_result,
                "evidence": loc_result.get("evidence_trace", {}),
                "ai_synthesis": ai_synthesis,
                "requires_human_approval": True,
                "approval_status": "PENDING"
            }
        else:
            evidence = delivery_evidence(
                unified_df=unified_df,
                category=filters.get("category"),
                location=filters.get("location"),
                period=route.get("target_period") if route.get("has_explicit_period") else None
            )

            structured_facts = {
                "investigation_type": "delivery_risk",
                "primary_category": evidence["primary_category"],
                "primary_location": evidence["primary_location"],
                "financial_impact": evidence["financial_impact"],
                "category_share": evidence["category_share"]
            }

            ai_synthesis = generate_business_explanation(structured_facts, question)

            return {
                "status": "SUCCESS",
                "query_id": query_id,
                "question": question,
                "intent": "delivery_risk",
                "route_details": route,
                "evidence": evidence,
                "ai_synthesis": ai_synthesis,
                "requires_human_approval": True,
                "approval_status": "PENDING"
            }

    elif intent == "discount_leakage":
        evidence = discount_evidence(
            unified_df=unified_df,
            period=route.get("target_period") if route.get("has_explicit_period") else None
        )

        structured_facts = {
            "investigation_type": "discount_leakage",
            "primary_category": evidence["primary_category"],
            "financial_impact": evidence["financial_impact"],
            "category_share": evidence["category_share"]
        }

        ai_synthesis = generate_business_explanation(structured_facts, question)

        return {
            "status": "SUCCESS",
            "query_id": query_id,
            "question": question,
            "intent": "discount_leakage",
            "route_details": route,
            "evidence": evidence,
            "ai_synthesis": ai_synthesis,
            "requires_human_approval": True,
            "approval_status": "PENDING"
        }

    else:
        # full_investigation or category_performance
        ref_ev = refund_evidence(unified_df=unified_df)
        del_ev = delivery_evidence(unified_df=unified_df)
        disc_ev = discount_evidence(unified_df=unified_df)
        total_leakage = ref_ev["financial_impact"] + del_ev["financial_impact"] + disc_ev["financial_impact"]

        structured_facts = {
            "investigation_type": "full_investigation",
            "financial_impact": round(total_leakage, 2),
            "refund_impact": ref_ev["financial_impact"],
            "delivery_impact": del_ev["financial_impact"],
            "discount_impact": disc_ev["financial_impact"],
            "is_partially_supported": is_partially_supported,
            "scope_clarification": scope_clarification
        }

        ai_synthesis = generate_business_explanation(structured_facts, question)

        return {
            "status": "SUCCESS",
            "query_id": query_id,
            "question": question,
            "intent": "full_investigation",
            "is_partially_supported": is_partially_supported,
            "scope_clarification": scope_clarification,
            "route_details": route,
            "combined_leakage": {
                "total_financial_impact": round(total_leakage, 2),
                "refund_leakage": ref_ev,
                "delivery_leakage": del_ev,
                "discount_leakage": disc_ev
            },
            "ai_synthesis": ai_synthesis,
            "requires_human_approval": True,
            "approval_status": "PENDING"
        }