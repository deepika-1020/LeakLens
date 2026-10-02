# 🔎 LeakLens — AI Revenue Leakage Investigator & Decision Engine

**Build Fast with AI — AI Build Challenge 2026**  
**Problem Statement:** PS-04 — AI Decision Engine for Business Data  
**Project Track:** AI & Data Analytics  
## 🚀 Live Demo

**Deployed App:** https://deepika-1020-leaklens-app-gaydrs.streamlit.app/

---

## 📌 Executive Overview

In e-commerce and retail operations, businesses bleed 2% to 6% of gross merchandise value through operational slippage: silent delivery cancellations, transit damages, customer returns, and promotional discount leakage. Traditional business dashboards display backward-looking charts but **fail to diagnose the root cause, quantify financial impact, trace evidence, or prescribe actionable operational interventions**.

**LeakLens** is an enterprise AI decision engine built for Revenue Operations and Data Analytics teams. When an executive asks a natural-language business question such as:

> *"Why did revenue decline last month?"*

LeakLens does not generate hallucinated numbers. Instead, it deploys a **Two-Tier Architecture**:
1. **Tier 1 (Deterministic Data Analytics Engine):** Executes rigorous Month-over-Month (MoM) revenue decomposition, isolates adverse variances (delivery failures, refund spikes, discount overrides, volume drops), and slices performance across categories, logistics hubs, and customer segments.
2. **Tier 2 (Grounded AI Reasoning Layer):** Synthesizes verified analytical findings into executive briefings, cross-references transaction-level evidence, and proposes operational playbooks.
3. **Human-in-the-Loop Governance:** Every proposed action requires human approval before logging into an immutable, persistent audit trail (`audit_trail.json`).

---

## 🏗️ Two-Layer System Architecture

```
                                  [ User Query ]
                          "Why did revenue decline last month?"
                                         │
                                         ▼
                     [ Layer 2: Intelligent Query Router ]
                       (Intent Detection & Filter Extraction)
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
       [ Valid Business Domain ]                    [ Out-of-Scope Query ]
                    │                                         │
                    ▼                                         ▼
   [ Layer 1: Deterministic Analytics Engine ]     [ Safe Guardrail Rejection ]
   - Revenue Waterfall & MoM Analyzer              "Insufficient evidence /
   - Delivery Failure & Logistics Risk              Query unsupported"
   - Customer Refund & Quality Leakage
   - Promotional Discount Anomaly Detection
                    │
                    ▼
     [ Multi-Dimensional Root-Cause Engine ]
       (Category x Metro Hub x Segment)
                    │
                    ▼
      [ Dynamic Evidence & Trace Engine ]
     (Source CSVs + Exact Filter + Calculations +
      Order-Level Row Proofs)
                    │
                    ▼
       [ Layer 2: Grounded AI Reasoner ]
     (Gemini API with Offline Deterministic Fallback)
                    │
                    ▼
      [ Human Approval & Audit Logger ]
     (Reviewer Role + Justification Notes ➔ audit_trail.json)
                    │
                    ▼
       [ Enterprise Decision Support UI ]
            (Streamlit Web Application)
```

### Core Architecture Principle: Zero Financial Hallucination
* **The LLM is NEVER permitted to calculate financial numbers.**
* All aggregations, percentage changes, and financial impact figures are computed deterministically in Python/Pandas.
* The AI layer strictly receives pre-calculated structured facts and translates them into executive business prose.

---

## 🔬 Controlled Business Dataset (Seed = 42)

The dataset models an enterprise e-commerce platform with 4 core relational tables:
- **`orders.csv`** (2,000 orders): `order_id`, `customer_id`, `order_date`, `category`, `unit_price`, `quantity`, `discount`, `total_amount`, `status`
- **`customers.csv`** (300 profiles): `customer_id`, `customer_segment` (Standard, Premium, Enterprise), `location` (5 metro hubs), `signup_date`
- **`refunds.csv`** (155 return records): `refund_id`, `order_id`, `refund_date`, `refund_amount`, `refund_reason`
- **`deliveries.csv`** (2,000 fulfillment logs): `order_id`, `delivery_date`, `promised_date`, `delivery_status` (`Delivered`, `Late`, `Cancelled`, `Failed`, `Returned`)

### Documented Injected Business Event (September 2026)
To enable meaningful root-cause investigation for *"Why did revenue decline last month?"* (comparing August 2026 vs September 2026):
1. **Logistics Bottleneck in South Hub:** In September 2026, 3PL logistics partner disruptions in Hyderabad and Bangalore caused Electronics delivery failure/cancellation rates to jump to ~45%.
2. **Quality & Transit Handling Surge:** Electronics customer refund requests surged with primary justifications recorded as "Damaged" in transit and "Late Delivery".
3. **Discount Overrides:** Periodic unauthorized discount codes (35%–50%) eroded product gross margins.

---

## 📊 End-to-End Decision Chain (11 Steps)

1. **Natural-Language Understanding:** Identifies intent (`revenue_trend`), temporal scope (`2026-09` vs `2026-08`), and dimensions.
2. **Data Ingestion & Hygiene:** Validates schemas, parses dates, and creates unified order-level analytical representations without import-time side effects.
3. **Revenue Waterfall Calculation:** Computes Gross Revenue, Discounts, Billed Revenue, Refunds, Delivery Failures, and Net Realized Revenue.
4. **Variance Decomposition:** Analyzes:
   $$\Delta \text{Net Revenue} = \Delta \text{Volume} + \Delta \text{AOV} - \Delta \text{Failed Deliveries} - \Delta \text{Refunds} - \Delta \text{Discounts}$$
5. **Driver Ranking:** Ranks adverse drivers strictly descending by calculated rupee impact.
6. **Multi-Dimensional Slice:** Pinpoints the highest concentration Category (Electronics), Metro Location (Hyderabad), and Customer Segment (Standard/Premium).
7. **Evidence Extraction:** Extracts exact SQL/Pandas query recipes, filter conditions, and order-level records.
8. **AI Narrative Synthesis:** Produces a 3-part briefing: Executive Summary, Root-Cause Narrative, and Actionable Playbook.
9. **Guardrail Check:** Disallows automated system execution.
10. **Human Review & Decision:** The operations reviewer inputs notes and clicks `Approve` or `Reject`.
11. **Persistent Audit Trail:** Decision state, reviewer role, query ID, timestamp, and metrics snapshot are appended to `audit_trail.json`.

---

## 📈 Benchmark Evaluation Suite

LeakLens includes an automated evaluation framework (`evaluation/evaluate.py`) running across 24 realistic business queries in `evaluation/questions.csv`:

| Benchmark Metric | Measured Result | Description |
| :--- | :---: | :--- |
| **Natural Intent Classification Accuracy** | **100.0%** | Accurately routes across trends, refunds, deliveries, discounts, products, and full scans. |
| **Out-of-Scope Guardrail Rejection** | **100.0%** | Successfully rejects external/unsupported questions without hallucination. |
| **Partially-Supported Data Scoping Rate** | **100.0%** | Clarifies data boundaries on unrecorded metrics (e.g. Profit/Cost) & provides closest proxy. |
| **Row-Level Evidence Backing Rate** | **100.0%** | 100% of supported queries return verified order-level audit records. |
| **Financial Grounding Integrity** | **100.0%** | All financial metrics are non-zero, deterministic, and non-hallucinated. |
| **Overall Benchmark Pass Rate** | **100.0%** | **24 / 24** test cases passing automated assertions. |

---

## 🚀 Setup & Execution Guide

### Prerequisites
- Python 3.10+
- Virtual environment (recommended)

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/deepika-1020/LeakLens.git
cd LeakLens

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Reproducible Data
```bash
python generate_data.py
```

### 3. Run Benchmark Evaluation Suite
```bash
python evaluation/evaluate.py
```

### 4. Launch Streamlit Decision Support Application
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## ☁️ Deployment Instructions

### Streamlit Community Cloud (1-Click Deployment)
1. Push repository to GitHub.
2. Log into [share.streamlit.io](https://share.streamlit.io).
3. Connect your repository and select `app.py` as the entry point.
4. *(Optional)* Add `GEMINI_API_KEY` in the **Advanced Settings -> Secrets** section if you wish to use Gemini for synthesis. Otherwise, the offline deterministic reasoner runs automatically with zero configuration.

---

## 🛡️ Failure Cases & Analytical Guardrails

1. **Unsupported Domains:**  
   Questions such as *"Predict tomorrow's stock price"* or *"What is employee salary distribution?"* are rejected with an explicit analytical scope notice. LeakLens refuses to generate speculative numbers.
2. **Missing or Incomplete Data:**  
   If a user asks about an empty category or non-existent city, the system reports zero matching records and advises the user of insufficient evidence.
3. **Positive Revenue Trajectory:**  
   If a period experienced revenue growth, the engine explicitly reports `NO_DECLINE` rather than forcing an artificial leakage narrative.

---

## 🤖 AI Tool Disclosure

- **Development & Analytical Design:** Architectural design, statistical decomposition, and test suites developed by the Data Analytics & AI participant.
- **LLM Reasoning Layer:** Google Gemini (1.5 Flash) integration for natural-language executive synthesis (optional, with deterministic template fallback).
- **Core Analytics:** Python 3, Pandas, NumPy, and Streamlit.
