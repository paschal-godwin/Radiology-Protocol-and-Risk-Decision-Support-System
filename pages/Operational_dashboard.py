import json
from pathlib import Path

import pandas as pd
import streamlit as st


LOG_PATH = Path("logs/case_runs.jsonl")


def load_case_logs(log_path=LOG_PATH):
    if not log_path.exists():
        return []

    logs = []

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                logs.append(json.loads(line))

    return logs


st.set_page_config(
    page_title="Operational Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("Operational Dashboard")
st.caption("Monitoring view for logged assessment runs, confidence behavior, evidence support, and operational alerts.")

logs = load_case_logs()

if not logs:
    st.info("No operational logs yet. Run an assessment first.")
    st.stop()

logs_df = pd.DataFrame(logs)
logs_df.index = range(1, len(logs_df) + 1)

st.subheader("Recent Operational Logs")

display_columns = [
    "timestamp",
    "overall_risk",
    "recommended_action",
    "confidence",
    "confidence_label",
    "capped_by",
    "active_claims",
    "active_topics",
    "selected_evidence_count",
]

available_columns = [
    col for col in display_columns
    if col in logs_df.columns
]

st.dataframe(
    logs_df[available_columns].tail(10),
    use_container_width=True,
)
risk_counts = logs_df["overall_risk"].value_counts()

st.markdown("#### Risk Distribution")
st.bar_chart(risk_counts)
st.markdown("#### Most Common Active Claims")

all_claims = []

for claims in logs_df["active_claims"]:
    if isinstance(claims, list):
        all_claims.extend(claims)

if all_claims:
    claim_counts = pd.Series(all_claims).value_counts()
    st.bar_chart(claim_counts)
else:
    st.info("No active claims found in logs yet.")
st.markdown("#### Most Common Active Topics")

all_topics = []

for topics in logs_df["active_topics"]:
    if isinstance(topics, list):
        all_topics.extend(topics)

if all_topics:
    topic_counts = pd.Series(all_topics).value_counts()
    st.bar_chart(topic_counts)
else:
    st.info("No active topics found in logs yet.")

st.markdown("#### Confidence Monitoring")

confidence_values = logs_df["confidence"].dropna()

if not confidence_values.empty:
    avg_confidence = confidence_values.mean()

    low_confidence_count = (
        logs_df["confidence"] < 0.70
    ).sum()

    st.metric(
        "Average Final Confidence",
        round(avg_confidence, 3)
    )

    st.metric(
        "Low Confidence Cases (< 0.70)",
        int(low_confidence_count)
    )

    st.markdown("##### Confidence Limiting Factors")

    capped_by_counts = (
        logs_df["capped_by"]
        .dropna()
        .value_counts()
    )

    st.bar_chart(capped_by_counts)

else:
    st.info("No confidence data available yet.")

st.markdown("#### Recommended Action Distribution")

if "recommended_action" in logs_df.columns:
    action_counts = logs_df["recommended_action"].dropna().value_counts()

    if not action_counts.empty:
        st.bar_chart(action_counts)
    else:
        st.info("No recommended action data available yet.")
else:
    st.info("Recommended action field not found in logs.")

st.markdown("#### Risk Level vs Recommended Action")

if "overall_risk" in logs_df.columns and "recommended_action" in logs_df.columns:
    risk_action_table = pd.crosstab(
        logs_df["overall_risk"],
        logs_df["recommended_action"]
    )

    st.dataframe(
        risk_action_table,
        use_container_width=True
    )
st.markdown("#### Evidence Support Monitoring")

if "selected_evidence_count" in logs_df.columns:
    avg_evidence_count = logs_df["selected_evidence_count"].mean()

    zero_evidence_cases = (
        logs_df["selected_evidence_count"] == 0
    ).sum()

    st.metric(
        "Average Selected Evidence Count",
        round(avg_evidence_count, 2)
    )

    st.metric(
        "Cases With No Selected Evidence",
        int(zero_evidence_cases)
    )

    evidence_count_distribution = (
        logs_df["selected_evidence_count"]
        .value_counts()
        .sort_index()
    )

    st.markdown("##### Selected Evidence Count Distribution")
    st.bar_chart(evidence_count_distribution)

else:
    st.info("Selected evidence count field not found in logs.")

st.markdown("#### Operational Alerts")

low_confidence_cases = logs_df[
    logs_df["confidence"] < 0.70
]

if not low_confidence_cases.empty:
    st.warning(
        f"{len(low_confidence_cases)} low-confidence case(s) detected."
    )

    st.dataframe(
        low_confidence_cases[
            [
                "timestamp",
                "overall_risk",
                "recommended_action",
                "confidence",
                "capped_by",
                "active_claims",
            ]
        ].tail(5),
        use_container_width=True,
    )
else:
    st.success("No recent low-confidence cases detected.")

high_risk_cases = logs_df[
    logs_df["overall_risk"] == "high"
]

st.markdown("##### Recent High-Risk Cases")

if not high_risk_cases.empty:
    st.dataframe(
        high_risk_cases[
            [
                "timestamp",
                "recommended_action",
                "confidence",
                "active_claims",
                "active_topics",
            ]
        ].tail(5),
        use_container_width=True,
    )
else:
    st.info("No high-risk cases logged yet.")

display_columns = [
    "timestamp",
    "overall_risk",
    "recommended_action",
    "confidence",
    "confidence_label",
    "capped_by",
    "active_claims",
    "active_topics",
    "selected_evidence_count",
]

available_columns = [
    col for col in display_columns
    if col in logs_df.columns
]
logs_df.index = range(1, len(logs_df) + 1)
st.dataframe(
    logs_df[available_columns].tail(10),
    use_container_width=True,
)

with st.expander("View raw operational logs"):
    st.json(logs[-10:])
