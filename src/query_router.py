import re
from typing import Dict, Any, Optional, List

# ==============================================================================
# LEAKLENS - INTELLIGENT NATURAL-LANGUAGE QUERY ROUTER
# Role: Data Analytics & AI
# Problem Statement: PS-04 (Natural-Language Intent, Entity & Scope Resolution)
# ==============================================================================

VALID_CATEGORIES = ["Electronics", "Home", "Fashion", "Beauty"]
VALID_LOCATIONS = ["Chennai", "Bangalore", "Hyderabad", "Mumbai", "Delhi"]
VALID_SEGMENTS = ["Standard", "Premium", "Enterprise"]

MONTH_NAME_MAP = {
    "january": "2026-01", "jan": "2026-01",
    "february": "2026-02", "feb": "2026-02",
    "march": "2026-03", "mar": "2026-03",
    "april": "2026-04", "apr": "2026-04",
    "may": "2026-05",
    "june": "2026-06", "jun": "2026-06",
    "july": "2026-07", "jul": "2026-07",
    "august": "2026-08", "aug": "2026-08",
    "september": "2026-09", "sep": "2026-09", "sept": "2026-09"
}

# Domains completely outside operating transactional data
COMPLETELY_UNSUPPORTED_DOMAINS = [
    "stock price", "stock", "share price", "weather", "salary", "employee", 
    "crypto", "bitcoin", "competitor", "marketing budget", 
    "ad spend", "facebook ads", "google ads", "instagram",
    "ceo", "hiring", "interview", "predict tomorrow"
]

# Business metrics that are legitimately asked by business users but unrecorded in basic sales/ERP datasets
PARTIALLY_SUPPORTED_METRICS = {
    "profit": "product cost / unit margin / COGS",
    "margin": "gross margin / product acquisition cost",
    "product cost": "Cost of Goods Sold (COGS)",
    "cogs": "Cost of Goods Sold (COGS)",
    "lifetime value": "historical multi-year retention LTV",
    "clv": "Customer Lifetime Value (CLV)",
    "ltv": "Customer Lifetime Value (LTV)"
}


def route_query(question: str) -> Dict[str, Any]:
    """
    Intelligently interpret natural-language business questions, detect analytical intent,
    extract entities, and handle data scope boundaries gracefully without hallucination.
    """
    clean_q = question.lower().strip()

    # --------------------------------------------------------------------------
    # 1. Check for COMPLETELY UNSUPPORTED external domains (Stocks, Weather, HR)
    # --------------------------------------------------------------------------
    for phrase in COMPLETELY_UNSUPPORTED_DOMAINS:
        if phrase in clean_q:
            return {
                "intent": "unsupported",
                "is_supported": False,
                "is_partially_supported": False,
                "confidence": 0.98,
                "metric": "unsupported",
                "extracted_filters": {},
                "rejection_reason": (
                    f"LeakLens cannot answer this question because the operating datasets "
                    f"(orders, refunds, deliveries, customers) do not contain '{phrase}' data. "
                    "To prevent hallucination, the decision engine only analyzes verified business data."
                )
            }

    # --------------------------------------------------------------------------
    # 2. Extract Dimensional Filters (Category, Location, Segment)
    # --------------------------------------------------------------------------
    extracted_category = None
    for cat in VALID_CATEGORIES:
        if cat.lower() in clean_q:
            extracted_category = cat
            break

    extracted_location = None
    for loc in VALID_LOCATIONS:
        if loc.lower() in clean_q:
            extracted_location = loc
            break

    extracted_segment = None
    for seg in VALID_SEGMENTS:
        if seg.lower() in clean_q:
            extracted_segment = seg
            break

    # --------------------------------------------------------------------------
    # 3. Extract Temporal Period
    # --------------------------------------------------------------------------
    target_period = "2026-09"       # Default latest active month
    comparison_period = "2026-08"   # Default prior comparison month
    has_explicit_period = False

    for month_name, ym in MONTH_NAME_MAP.items():
        if re.search(r'\b' + re.escape(month_name) + r'\b', clean_q):
            target_period = ym
            has_explicit_period = True
            m_num = int(ym.split("-")[1])
            prev_num = max(1, m_num - 1)
            comparison_period = f"2026-{prev_num:02d}"
            break

    if any(p in clean_q for p in ["last month", "past month", "previous month", "recent month", "latest month", "this month"]):
        target_period = "2026-09"
        comparison_period = "2026-08"
        has_explicit_period = True

    # --------------------------------------------------------------------------
    # 4. Check for PARTIALLY SUPPORTED questions (Profit, Margin, COGS, Add/Remove)
    # --------------------------------------------------------------------------
    missing_metric = None
    for keyword, explanation in PARTIALLY_SUPPORTED_METRICS.items():
        if keyword in clean_q:
            missing_metric = explanation
            break

    if missing_metric or ("add" in clean_q and "remove" in clean_q and "product" in clean_q):
        # The user is asking a strategic business question about profit or product rationalization
        proxy_intent = "product_leakage" if "product" in clean_q else "category_performance"
        missing_text = missing_metric if missing_metric else "product cost / unit profit margin"

        return {
            "intent": proxy_intent,
            "is_supported": True,
            "is_partially_supported": True,
            "confidence": 0.88,
            "metric": "net_revenue_and_leakage",
            "missing_data_metric": missing_text,
            "scope_clarification": (
                f"I can analyze this using the available order, refund, delivery, and customer data, "
                f"but the dataset does not contain {missing_text} information, so I cannot reliably "
                f"determine exact profit margins. However, based on verified transaction, refund, and delivery "
                f"losses, here is the closest supported operational analysis of which products and categories "
                f"are generating the highest revenue versus the highest financial leakage."
            ),
            "target_period": target_period,
            "comparison_period": comparison_period,
            "has_explicit_period": has_explicit_period,
            "extracted_filters": {
                "category": extracted_category,
                "location": extracted_location,
                "customer_segment": extracted_segment
            }
        }

    # --------------------------------------------------------------------------
    # 5. Natural-Language Intent Classification
    # --------------------------------------------------------------------------
    # 5a. Customer / Segment Specific Questions
    if any(k in clean_q for k in ["which customer", "which customers", "customer refund", "customer segment", "who returns"]):
        intent = "customer_leakage"
        metric = "refund_amount"

    # 5b. Product Specific Questions (hurting business, high refunds, worst products)
    elif any(k in clean_q for k in [
        "which product", "which products", "products are hurting", "products hurting",
        "selling poorly", "poorly selling", "products have high refunds", "worst product",
        "product is hurting", "product performance", "low performing product"
    ]):
        intent = "product_leakage"
        metric = "total_leakage"

    # 5c. Category Specific Performance Questions
    elif any(k in clean_q for k in [
        "performing poorly", "poor performing category",
        "category should management", "management focus", "focus on"
    ]) or ("which category" in clean_q and not any(w in clean_q for w in ["refund", "return", "delivery", "shipping", "discount"])):
        intent = "category_performance"
        metric = "net_realized_revenue"

    # 5d. Location / Geographic Delivery Inquiries
    elif any(k in clean_q for k in [
        "which city", "which location", "biggest delivery problem", "delivery problem",
        "shipping losses in", "delivery failure in", "delivery problems in"
    ]):
        intent = "delivery_risk"
        metric = "delivery_failure_value"

    # 5e. Promotional Discount Leakage
    elif any(k in clean_q for k in ["discount", "discounts", "promo", "coupon", "discount leakage", "discount policy"]):
        intent = "discount_leakage"
        metric = "discount_amount"

    # 5f. Refund / Return Inquiries
    elif any(k in clean_q for k in [
        "refund", "refunds", "refunded", "return", "returns", 
        "refunds increasing", "highest refunds", "customer returns"
    ]):
        intent = "refund_leakage"
        metric = "refund_amount"

    # 5g. Delivery / Shipping / Fulfillment Losses
    elif any(k in clean_q for k in [
        "delivery", "deliveries", "shipping", "courier", 
        "failed delivery", "logistics", "cancelled delivery"
    ]):
        intent = "delivery_risk"
        metric = "delivery_failure_value"

    # 5h. Revenue Drop / Sales Decline Trends (broad natural phrasing)
    elif any(k in clean_q for k in [
        "revenue decline", "revenue drop", "revenue fell", "revenue fall",
        "revenue become less", "sales drop", "sales decline", "sales fell",
        "sales fall", "sales decrease", "revenue decrease", "why did revenue",
        "why did sales", "drop in revenue", "drop in sales", "less money this month",
        "revenue fall", "revenue falling", "revenue going down"
    ]):
        intent = "revenue_trend"
        metric = "net_realized_revenue"

    # 5i. Broad Operational Loss & Strategic Advisory Inquiries
    elif any(k in clean_q for k in [
        "where are we losing", "losing money", "loss", "losses",
        "reduce revenue leakage", "reduce leakage", "investigate first",
        "financial loss", "improve business performance", "improve performance",
        "how can we improve", "revenue leakage", "full scan", "audit"
    ]):
        intent = "full_investigation"
        metric = "total_leakage"

    # 5j. Fallback: Contains general revenue / sales term
    elif "revenue" in clean_q or "sales" in clean_q:
        intent = "revenue_trend"
        metric = "net_realized_revenue"

    else:
        # Check if dimensional entity is present
        if extracted_category or extracted_location or extracted_segment:
            intent = "full_investigation"
            metric = "total_leakage"
        else:
            return {
                "intent": "unsupported",
                "is_supported": False,
                "is_partially_supported": False,
                "confidence": 0.40,
                "metric": "unknown",
                "extracted_filters": {},
                "rejection_reason": (
                    "Could not map query to available analytical modules. "
                    "Try asking about: Revenue Decline, Refund Leakage, Delivery Failures, "
                    "Product Performance, or Regional Logistics Risk."
                )
            }

    return {
        "intent": intent,
        "is_supported": True,
        "is_partially_supported": False,
        "confidence": 0.92,
        "metric": metric,
        "target_period": target_period,
        "comparison_period": comparison_period,
        "has_explicit_period": has_explicit_period,
        "extracted_filters": {
            "category": extracted_category,
            "location": extracted_location,
            "customer_segment": extracted_segment
        },
        "query_summary": f"Interpreted query as '{intent}' pipeline for period {target_period} vs {comparison_period}."
    }
