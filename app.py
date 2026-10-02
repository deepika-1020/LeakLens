import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# ------------------------------------------------------------------------------
# LEAKLENS — ENTERPRISE DECISION SUPPORT APPLICATION
# Role: AI & Data Analytics (Data Analytics / AI)
# Problem Statement: PS-04 (AI Decision Engine for Business Data)
# ------------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from leaklens_engine import investigate
from audit_logger import log_decision, get_audit_trail
from trend_analyzer import get_monthly_metrics

# ------------------------------------------------------------------------------
# PAGE SETUP & BRANDING
# ------------------------------------------------------------------------------

st.set_page_config(
    page_title="LeakLens | AI Decision Engine",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Business Decision Engine
st.markdown("""
<style>
    .layer-header {
        font-size: 1.15rem;
        font-weight: 700;
        padding: 6px 12px;
        border-radius: 6px;
        margin-top: 18px;
        margin-bottom: 12px;
    }
    .layer-1-data {
        background-color: #e8f4f8;
        border-left: 5px solid #0288d1;
        color: #01579b;
    }
    .layer-2-ai {
        background-color: #f3e5f5;
        border-left: 5px solid #8e24aa;
        color: #4a148c;
    }
    .layer-3-human {
        background-color: #fff8e1;
        border-left: 5px solid #f57f17;
        color: #e65100;
    }
    .badge-approved {
        background-color: #d4edda;
        color: #155724;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.9rem;
    }
    .badge-rejected {
        background-color: #f8d7da;
        color: #721c24;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.9rem;
    }
    .badge-pending {
        background-color: #fff3cd;
        color: #856404;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ------------------------------------------------------------------------------

if "active_investigation" not in st.session_state:
    st.session_state.active_investigation = None
if "approval_status" not in st.session_state:
    st.session_state.approval_status = "PENDING"
if "approval_msg" not in st.session_state:
    st.session_state.approval_msg = None
if "question_input" not in st.session_state:
    st.session_state.question_input = "Why did revenue decline last month?"
if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0

# ------------------------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------------------------

with st.sidebar:
    st.title("🔎 LeakLens")
    st.caption("AI Decision Engine for Business Data")
    st.markdown("**Role:** `Data Analytics & AI`")
    st.markdown("**Challenge:** `Build Fast with AI 2026 (PS-04)`")
    st.divider()

    st.markdown("### 🏛️ Architecture Principles")
    st.markdown("""
    - **Layer 1 (Data):** Deterministic Python/Pandas math (No LLM numbers).
    - **Layer 2 (AI):** Grounded NLU interpretation & executive briefing.
    - **Layer 3 (Human):** Mandatory human signoff before action dispatch.
    """)
    st.divider()

    st.markdown("### 📦 Operating Datasets")
    st.markdown("""
    - `orders.csv` (2,000 transactions, P001–P100)
    - `customers.csv` (300 accounts, 5 metro hubs)
    - `refunds.csv` (Quality & customer returns)
    - `deliveries.csv` (3PL carrier logs)
    """)
    st.divider()

    trail = get_audit_trail()
    st.markdown(f"### 📜 Decision History (`{len(trail)}`)")
    if trail:
        for t in trail[:3]:
            icon = "🟢" if t["decision"] == "APPROVED" else "🔴"
            st.markdown(f"**{icon} {t['decision']}** — `{t['audit_id']}`")
            st.caption(f"{t['timestamp_utc']} | Q: {t['question'][:32]}...")
    else:
        st.info("No decisions recorded yet.")

# ------------------------------------------------------------------------------
# MAIN INTERFACE: HEADER & NATURAL-LANGUAGE QUERY INPUT
# ------------------------------------------------------------------------------

st.markdown("# 🔎 LeakLens Decision Support Engine")
st.markdown("### Ask anything about your business data")
st.caption(
    "Type your question in natural business language. LeakLens investigates underlying transaction, "
    "delivery, customer, and refund streams to isolate root causes and formulate actionable playbooks."
)

col_search, col_action = st.columns([5, 1])

with col_search:
    user_query = st.text_input(
        "Business Question:",
        value=st.session_state.question_input,
        placeholder="e.g. Why did revenue decline last month? / Which products are hurting our business?"
    )

with col_action:
    st.write("")
    st.write("")
    if st.button("🔍 Investigate", type="primary", use_container_width=True):
        if user_query.strip():
            with st.spinner("Analyzing operational records and running deterministic calculations..."):
                st.session_state.question_input = user_query
                st.session_state.active_investigation = investigate(user_query)
                st.session_state.approval_status = "PENDING"
                st.session_state.approval_msg = None
        else:
            st.warning("Please enter a business question.")

# Example Question Chips (Explicitly labeled as examples, not limitations)
st.markdown("**Example Questions (Click any to test natural-language understanding):**")
example_cols = st.columns(4)

with example_cols[0]:
    if st.button("📉 Why did revenue decline last month?", use_container_width=True):
        st.session_state.question_input = "Why did revenue decline last month?"
        st.session_state.active_investigation = investigate("Why did revenue decline last month?")
        st.session_state.approval_status = "PENDING"
        st.session_state.approval_msg = None
    if st.button("📦 Which products are hurting our business?", use_container_width=True):
        st.session_state.question_input = "Which products are hurting our business?"
        st.session_state.active_investigation = investigate("Which products are hurting our business?")
        st.session_state.approval_status = "PENDING"
        st.session_state.approval_msg = None

with example_cols[1]:
    if st.button("💰 Which category has highest refunds?", use_container_width=True):
        st.session_state.question_input = "Which category has the highest refunds?"
        st.session_state.active_investigation = investigate("Which category has the highest refunds?")
        st.session_state.approval_status = "PENDING"
        st.session_state.approval_msg = None
    if st.button("🏷️ Show me discount leakage", use_container_width=True):
        st.session_state.question_input = "Show me discount leakage."
        st.session_state.active_investigation = investigate("Show me discount leakage.")
        st.session_state.approval_status = "PENDING"
        st.session_state.approval_msg = None

with example_cols[2]:
    if st.button("🚚 Which city has biggest delivery problem?", use_container_width=True):
        st.session_state.question_input = "Which city has the biggest delivery problem?"
        st.session_state.active_investigation = investigate("Which city has the biggest delivery problem?")
        st.session_state.approval_status = "PENDING"
        st.session_state.approval_msg = None
    if st.button("👥 Which customers generate most refunds?", use_container_width=True):
        st.session_state.question_input = "Which customers generate the most refunds?"
        st.session_state.active_investigation = investigate("Which customers generate the most refunds?")
        st.session_state.approval_status = "PENDING"
        st.session_state.approval_msg = None

with example_cols[3]:
    if st.button("💡 How to improve profit by adding/removing products?", use_container_width=True):
        st.session_state.question_input = "How to improve profit by adding what product and by removing what product?"
        st.session_state.active_investigation = investigate("How to improve profit by adding what product and by removing what product?")
        st.session_state.approval_status = "PENDING"
        st.session_state.approval_msg = None
    if st.button("🔮 Predict tomorrow's stock price (Scope test)", use_container_width=True):
        st.session_state.question_input = "Predict tomorrow's stock price"
        st.session_state.active_investigation = investigate("Predict tomorrow's stock price")
        st.session_state.approval_status = "PENDING"
        st.session_state.approval_msg = None

st.divider()

# ------------------------------------------------------------------------------
# NAVIGATION TABS: INVESTIGATION | DECISION HISTORY | MONTHLY BASELINE
# ------------------------------------------------------------------------------

tab_investigate, tab_history, tab_baseline = st.tabs([
    "🔍 Active Investigation",
    "📜 Decision History (Audit Trail)",
    "📊 Monthly Revenue Baseline"
])

# ==============================================================================
# TAB 1: ACTIVE INVESTIGATION
# ==============================================================================
with tab_investigate:
    inv = st.session_state.active_investigation

    if inv is None:
        st.info("💡 **Enter any business question above or click an example question to start an investigation.**")
    
    elif inv["status"] == "UNSUPPORTED":
        st.error("⚠️ **Analytical Scope Notice: Query Outside Data Domain**")
        st.write(f"**Question Asked:** *\"{inv['question']}\"*")
        st.write(inv["message"])
        st.info(
            "**Data-Grounding Guarantee:** LeakLens does not invent answers or guess future market events. "
            "It only answers questions that can be deterministically calculated from your operational datasets."
        )

    else:
        # Check for Partially Supported Questions (e.g. Profit / Cost / Add-Remove)
        if inv.get("is_partially_supported"):
            st.warning(f"⚠️ **Data Scope Clarification:** {inv.get('scope_clarification')}")

        ai = inv.get("ai_synthesis", {})
        intent = inv["intent"]

        # ----------------------------------------------------------------------
        # LAYER 1: WHAT THE DATA SHOWS (DETERMINISTIC FACTS)
        # ----------------------------------------------------------------------
        st.markdown('<div class="layer-header layer-1-data">📊 LAYER 1: WHAT THE DATA SHOWS (Deterministic Calculated Facts)</div>', unsafe_allow_html=True)

        finding_text = ""
        evidence_summary_for_log = {}

        if intent == "revenue_trend":
            analytics = inv["analytics"]
            finding_text = (
                f"Net revenue changed by ₹{analytics['net_revenue_change']:,.2f} ({analytics['percentage_change']:+.2f}%). "
                f"Primary observed contributor: {analytics['primary_driver']['name']} "
                f"(₹{analytics['primary_driver']['financial_impact']:,.2f} impact in {analytics['root_cause_dimensions']['top_category']['name']})."
            )

            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric(
                    "Net Revenue Variance",
                    f"₹{analytics['net_revenue_change']:,.2f}",
                    f"{analytics['percentage_change']:+.2f}%",
                    delta_color="inverse"
                )
            with col_m2:
                st.metric(f"Baseline ({analytics['previous_label']})", f"₹{analytics['comparison']['net_revenue']['previous']:,.2f}")
            with col_m3:
                st.metric(f"Current Period ({analytics['current_label']})", f"₹{analytics['comparison']['net_revenue']['current']:,.2f}")
            with col_m4:
                st.metric("Top Driver", analytics["primary_driver"]["name"], f"₹{analytics['primary_driver']['financial_impact']:,.2f}")

            # Revenue Trajectory Bar Chart
            st.markdown("#### Monthly Net Revenue vs Operational Losses")
            monthly_df = pd.DataFrame(analytics["comparison"]["all_monthly_metrics"])
            st.bar_chart(monthly_df.set_index("month_label")[["net_realized_revenue", "refund_amount", "delivery_failure_value"]])

            # Ranked Drivers Table
            st.markdown("#### Ranked Revenue Variance Contributors")
            drivers_df = pd.DataFrame(analytics["ranked_drivers"])[["name", "type", "financial_impact", "share_of_decline", "description"]]
            drivers_df.columns = ["Driver Name", "Driver Category", "Impact (₹)", "Share (%)", "Variance Explanation"]
            st.dataframe(drivers_df, use_container_width=True)

            # Dimensions Drilldown
            dims = analytics["root_cause_dimensions"]
            cd1, cd2, cd3 = st.columns(3)
            with cd1:
                st.markdown(f"**Top Concentration Category:** `{dims['top_category']['name']}` (₹{dims['top_category']['net_decline']:,.2f} decline)")
            with cd2:
                st.markdown(f"**Logistics Hub Bottleneck:** `{dims['top_location']['name']}` (₹{dims['top_location']['failed_delivery_impact']:,.2f} failed deliveries)")
            with cd3:
                st.markdown(f"**Primary Customer Segment:** `{dims['top_segment']['name']}` (₹{dims['top_segment']['leakage_impact']:,.2f} total leakage)")

            # Evidence Trace
            st.markdown("#### Supporting Evidence (Record-Level Trace)")
            ev = analytics["evidence_trace"]
            evidence_summary_for_log = {"records": ev["sample_record_count"], "filter": ev["filter_applied"]}
            with st.expander(f"🔍 Inspect {ev['sample_record_count']} Supporting Order Records", expanded=False):
                st.caption(f"Sources: {', '.join(ev['source_datasets'])} | Filter: {ev['filter_applied']}")
                st.dataframe(ev["evidence_dataframe"], use_container_width=True)

        elif intent == "product_leakage":
            prod_info = inv["product_analysis"]
            p_top = prod_info["primary_product_at_risk"]
            finding_text = (
                f"Product {p_top['product_id']} ({p_top['category']}) generated the highest operational loss: "
                f"₹{p_top['total_leakage']:,.2f} lost to refunds and delivery failures ({p_top['leakage_ratio_pct']}% leakage ratio)."
            )

            p1, p2, p3 = st.columns(3)
            with p1:
                st.metric("Primary Loss Product", f"{p_top['product_id']} ({p_top['category']})")
            with p2:
                st.metric("Total Product Leakage", f"₹{p_top['total_leakage']:,.2f}")
            with p3:
                st.metric("Leakage / Sales Ratio", f"{p_top['leakage_ratio_pct']}%")

            st.markdown("#### Products with Highest Operational Loss (Refunds + Delivery Failures)")
            worst_p_df = pd.DataFrame(prod_info["worst_leakage_products"])[["product_id", "category", "billed_revenue", "refund_amount", "failed_delivery_val", "total_leakage", "leakage_ratio_pct"]]
            worst_p_df.columns = ["Product ID", "Category", "Billed Sales (₹)", "Refunds (₹)", "Delivery Loss (₹)", "Total Loss (₹)", "Loss Ratio (%)"]
            st.dataframe(worst_p_df, use_container_width=True)

            st.markdown("#### Top Revenue Generating Products (Healthy Core)")
            best_p_df = pd.DataFrame(prod_info["top_performing_products"])[["product_id", "category", "units_sold", "billed_revenue", "net_revenue"]]
            best_p_df.columns = ["Product ID", "Category", "Units Sold", "Billed Sales (₹)", "Net Realized (₹)"]
            st.dataframe(best_p_df, use_container_width=True)

            ev = prod_info["evidence_trace"]
            evidence_summary_for_log = {"records": ev["sample_record_count"], "filter": ev["filter_applied"]}
            with st.expander(f"🔍 Inspect Supporting Records for {p_top['product_id']}", expanded=False):
                st.dataframe(ev["evidence_dataframe"], use_container_width=True)

        elif intent == "customer_leakage":
            cust_info = inv["customer_analysis"]
            c_top = cust_info["primary_customer"]
            s_top = cust_info["primary_segment"]
            finding_text = (
                f"Customer segment '{s_top['name']}' accounted for ₹{s_top['leakage_amount']:,.2f} in total leakage. "
                f"Top refund claimant {c_top['customer_id']} logged ₹{c_top['refund_amount']:,.2f} in returns."
            )

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Top Leakage Segment", s_top["name"])
            with c2:
                st.metric("Segment Leakage", f"₹{s_top['leakage_amount']:,.2f}", f"{s_top['leakage_share']}% of total")
            with c3:
                st.metric("Highest Refund Customer", f"{c_top['customer_id']} (₹{c_top['refund_amount']:,.2f})")

            st.markdown("#### Top Customer Accounts by Refund Claims")
            top_c_df = pd.DataFrame(cust_info["top_refund_customers"])[["customer_id", "customer_segment", "location", "order_count", "total_spent", "refund_amount", "refund_rate_pct"]]
            top_c_df.columns = ["Customer ID", "Segment", "Location", "Orders", "Total Spent (₹)", "Refunds (₹)", "Refund Rate (%)"]
            st.dataframe(top_c_df, use_container_width=True)

            ev = cust_info["evidence_trace"]
            evidence_summary_for_log = {"records": ev["sample_record_count"], "filter": ev["filter_applied"]}
            with st.expander(f"🔍 Inspect Records for Customer {c_top['customer_id']}", expanded=False):
                st.dataframe(ev["evidence_dataframe"], use_container_width=True)

        elif "location_analysis" in inv:
            loc_info = inv["location_analysis"]
            w_loc = loc_info["worst_location"]
            finding_text = (
                f"Logistics hub in {w_loc['name']} is the largest source of delivery failure: "
                f"₹{w_loc['failed_revenue']:,.2f} in failed/cancelled shipments ({w_loc['failure_rate_pct']}% failure rate)."
            )

            l1, l2, l3 = st.columns(3)
            with l1:
                st.metric("Highest Loss Hub", w_loc["name"])
            with l2:
                st.metric("Delivery Loss", f"₹{w_loc['failed_revenue']:,.2f}")
            with l3:
                st.metric("Order Failure Rate", f"{w_loc['failure_rate_pct']}%")

            st.markdown("#### Regional Hub Logistics Performance")
            loc_df = pd.DataFrame(loc_info["location_rankings"])[["location", "total_orders", "failed_orders", "failure_rate_pct", "failed_revenue", "loss_share_pct"]]
            loc_df.columns = ["Location", "Total Orders", "Failed Orders", "Failure Rate (%)", "Delivery Loss (₹)", "Share of Total Loss (%)"]
            st.dataframe(loc_df, use_container_width=True)

            ev = loc_info["evidence_trace"]
            evidence_summary_for_log = {"records": ev["sample_record_count"], "filter": ev["filter_applied"]}
            with st.expander(f"🔍 Inspect Delivery Failure Records in {w_loc['name']}", expanded=False):
                st.dataframe(ev["evidence_dataframe"], use_container_width=True)

        elif "evidence" in inv:
            ev = inv["evidence"]
            finding_text = f"{ev['primary_category']} is the largest contributor to {ev['decision_type']}: ₹{ev['primary_category_impact']:,.2f} ({ev['category_share']}%)"

            col_e1, col_e2, col_e3 = st.columns(3)
            with col_e1:
                st.metric("Total Leakage Impact", f"₹{ev['financial_impact']:,.2f}")
            with col_e2:
                st.metric("Primary Category", ev["primary_category"])
            with col_e3:
                st.metric("Share of Leakage", f"{ev['category_share']:.1f}%")

            st.markdown(f"**Calculation Formula:** `{ev['calculation']}`")
            st.markdown(f"**Observed Finding:** {ev['conclusion']}")

            evidence_summary_for_log = {"records": len(ev["evidence_records"]), "filter": ev["filter"]}
            with st.expander("🔍 Inspect Underlying Audit Records", expanded=False):
                st.caption(f"Sources: {', '.join(ev['sources'])} | Filter: {ev['filter']}")
                st.dataframe(ev["evidence_records"], use_container_width=True)

        elif "combined_leakage" in inv:
            comb = inv["combined_leakage"]
            finding_text = f"Total operational revenue leakage across all streams reached ₹{comb['total_financial_impact']:,.2f}."
            st.metric("Total Cross-Source Revenue Leakage", f"₹{comb['total_financial_impact']:,.2f}")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Refund Leakage", f"₹{comb['refund_leakage']['financial_impact']:,.2f}")
            with c2:
                st.metric("Delivery Failure Loss", f"₹{comb['delivery_leakage']['financial_impact']:,.2f}")
            with c3:
                st.metric("Discount Leakage", f"₹{comb['discount_leakage']['financial_impact']:,.2f}")

        # ----------------------------------------------------------------------
        # LAYER 2: AI RECOMMENDATION & PLAYBOOK
        # ----------------------------------------------------------------------
        st.markdown('<div class="layer-header layer-2-ai">💡 LAYER 2: AI RECOMMENDATION & OPERATIONAL PLAYBOOK (Grounded Synthesis)</div>', unsafe_allow_html=True)
        st.info(f"**Executive Briefing:** {ai.get('executive_summary')}")
        st.markdown(f"""
        ```text
        {ai.get('actionable_playbook')}
        ```
        """)
        st.caption(f"Reasoning Grounding Engine: `{ai.get('model_used')}`")

        # ----------------------------------------------------------------------
        # LAYER 3: HUMAN DECISION & GOVERNANCE
        # ----------------------------------------------------------------------
        st.markdown('<div class="layer-header layer-3-human">👤 LAYER 3: HUMAN DECISION & GOVERNANCE (Mandatory Signoff)</div>', unsafe_allow_html=True)
        st.caption("Compliance Guardrail: AI suggestions cannot automatically dispatch actions. A reviewer must evaluate evidence and record a binding decision.")

        col_r1, col_r2 = st.columns([1, 2])
        with col_r1:
            reviewer_role = st.selectbox(
                "Reviewer Role:",
                ["Data Analytics & AI Reviewer", "Revenue Operations Lead", "Director of Supply Chain & Fulfillment"]
            )
        with col_r2:
            reviewer_note = st.text_input("Reviewer Justification / Notes:", placeholder="e.g. Approved courier SLA review in South Hub.")

        btn_approve, btn_reject, _ = st.columns([1, 1, 3])

        with btn_approve:
            if st.button("✅ Approve Action", type="primary", use_container_width=True):
                log_decision(
                    query_id=inv["query_id"],
                    question=inv["question"],
                    investigation_type=inv["intent"],
                    finding=finding_text,
                    calculated_metrics={"intent": inv["intent"]},
                    recommendation=ai.get("actionable_playbook", "Standard operational playbook"),
                    decision="APPROVED",
                    reviewer=reviewer_role,
                    notes=reviewer_note,
                    evidence_summary=evidence_summary_for_log
                )
                st.session_state.approval_status = "APPROVED"
                st.session_state.approval_msg = "Decision APPROVED. Action logged into audit_trail.json for operational dispatch."

        with btn_reject:
            if st.button("❌ Reject Action", use_container_width=True):
                log_decision(
                    query_id=inv["query_id"],
                    question=inv["question"],
                    investigation_type=inv["intent"],
                    finding=finding_text,
                    calculated_metrics={"intent": inv["intent"]},
                    recommendation=ai.get("actionable_playbook", "Standard operational playbook"),
                    decision="REJECTED",
                    reviewer=reviewer_role,
                    notes=reviewer_note,
                    evidence_summary=evidence_summary_for_log
                )
                st.session_state.approval_status = "REJECTED"
                st.session_state.approval_msg = "Decision REJECTED. Recommendation logged into audit_trail.json as aborted."

        if st.session_state.approval_msg:
            if st.session_state.approval_status == "APPROVED":
                st.success(st.session_state.approval_msg)
            else:
                st.error(st.session_state.approval_msg)


# ==============================================================================
# TAB 2: DEDICATED DECISION HISTORY (AUDIT TRAIL)
# ==============================================================================
with tab_history:
    st.markdown("### 📜 Enterprise Decision History & Audit Trail")
    st.caption("Immutable record of all human approvals, rejections, findings, and reviewer justifications.")

    trail = get_audit_trail()

    if not trail:
        st.info("No decision records found in `audit_trail.json`. Execute an investigation and click Approve or Reject.")
    else:
        st.write(f"Total Logged Decisions: **{len(trail)}**")

        for idx, entry in enumerate(trail):
            status = entry.get("decision", "PENDING").upper()
            status_badge = "🟢 APPROVED" if status == "APPROVED" else "🔴 REJECTED"
            border_color = "#28a745" if status == "APPROVED" else "#dc3545"

            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #ddd; border-left: 6px solid {border_color}; border-radius: 8px; padding: 14px; margin-bottom: 14px; background-color: #fafafa;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.1rem; font-weight: bold;">{status_badge}</span>
                        <span style="font-family: monospace; color: #666;">ID: {entry.get('audit_id')}</span>
                    </div>
                    <div style="margin-top: 8px;">
                        <strong>Question:</strong> {entry.get('question')}
                    </div>
                    <div style="margin-top: 4px;">
                        <strong>Finding:</strong> {entry.get('finding', 'Operational finding recorded')}
                    </div>
                    <div style="margin-top: 4px;">
                        <strong>Reviewer:</strong> {entry.get('reviewer')} &nbsp;|&nbsp; <strong>Date:</strong> {entry.get('timestamp_utc')}
                    </div>
                    <div style="margin-top: 4px; color: #444; font-style: italic;">
                        <strong>Reviewer Note:</strong> "{entry.get('reviewer_notes')}"
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander(f"🔍 View Full Recommendation & Evidence Details for {entry.get('audit_id')}"):
                    st.markdown("**Action Recommended by AI Layer:**")
                    st.code(entry.get("recommendation", "N/A"), language="text")
                    if entry.get("evidence_summary"):
                        st.markdown("**Evidence Summary:**")
                        st.json(entry.get("evidence_summary"))


# ==============================================================================
# TAB 3: MONTHLY REVENUE BASELINE
# ==============================================================================
with tab_baseline:
    st.markdown("### 📊 Operational & Revenue Baseline (Jan – Sep 2026)")
    st.caption("Deterministic monthly metrics aggregated across orders, refunds, and delivery streams.")

    monthly_df = get_monthly_metrics()
    display_cols = [
        "year_month", "month_label", "order_volume", "billed_revenue",
        "aov", "refund_amount", "delivery_failure_value", "high_discount_value", "net_realized_revenue"
    ]
    renamed_df = monthly_df[display_cols].rename(columns={
        "year_month": "Period",
        "month_label": "Month",
        "order_volume": "Orders",
        "billed_revenue": "Billed Sales (₹)",
        "aov": "AOV (₹)",
        "refund_amount": "Refunds (₹)",
        "delivery_failure_value": "Delivery Loss (₹)",
        "high_discount_value": "High Discounts (₹)",
        "net_realized_revenue": "Net Realized Revenue (₹)"
    })
    st.dataframe(renamed_df, use_container_width=True)

    st.markdown("#### Monthly Net Revenue Trend")
    st.line_chart(monthly_df.set_index("month_label")[["net_realized_revenue"]])