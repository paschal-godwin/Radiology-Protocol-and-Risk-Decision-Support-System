import os
import sys
import json
from unittest import result
import pandas as pd
from typing import Any
from pathlib import Path



import streamlit as st
from dotenv import load_dotenv

# Ensure project root is importable
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv()

from app.schemas.input import (  # noqa: E402
    RadiologyCaseInput,
    Sex,
    PregnancyStatus,
    PriorContrastReaction,
    UrgencyLevel,
    MetforminUse,
    ThyroidStatus,
)
from app.services.assessment_service import run_assessment  # noqa: E402
from app.services.case_logger import log_case_run


st.set_page_config(
    page_title="CT Contrast Assistant V1",
    page_icon="🩻",
    layout="wide",
)

LOG_PATH = Path("logs/case_runs.jsonl")

def humanize_confidence_limiter(capped_by):
    mapping = {
        "rule_confidence": "The deterministic rule decision was the main limiting factor.",
        "retrieval_confidence": "Retrieved evidence strength was the main limiting factor.",
        "citation_alignment_confidence": "Citation-to-claim alignment was the main limiting factor.",
        "completeness_confidence": "Missing or incomplete case information was the main limiting factor.",
    }

    return mapping.get(
        capped_by,
        "No single limiting factor was identified."
    )


def load_case_logs(log_path=LOG_PATH):
    if not log_path.exists():
        return []

    logs = []

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                logs.append(json.loads(line))

    return logs

# -----------------------------
# Session-state init
# -----------------------------
def initialize_state():
    defaults = {
        "age": 60,
        "sex": "male",
        "exam": "CT",
        "contrast": True,
        "urgency": "routine",
        "allergy": "false",
        "asthma": "false",
        "egfr": "20",
        "pregnancy_status": "not_applicable",
        "reaction": "none",
        "loaded_demo_name": "None",
        "metformin_use": "no",
        "thyroid_status": "unknown",
        "last_result": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# -----------------------------
# State handlers
# -----------------------------
def handle_sex_change():
    sex = st.session_state["sex"]
    if sex == "male":
        st.session_state["pregnancy_status"] = "not_applicable"
    else:
        if st.session_state.get("pregnancy_status") == "not_applicable":
            st.session_state["pregnancy_status"] = "unknown"


def load_demo_into_state(case_name: str):
    if case_name == "None":
        return

    demo = load_demo_case(case_name)
    st.session_state["age"] = demo["age"]
    st.session_state["sex"] = demo["sex"]
    st.session_state["exam"] = demo["exam_requested"]
    st.session_state["contrast"] = demo["contrast_requested"]
    st.session_state["metformin"] = demo["metformin_use"]
    st.session_state["thyroid"] = demo["thyroid_status"]
    st.session_state["urgency"] = demo["urgency_level"]
    st.session_state["allergy"] = (
        "unknown"
        if demo["allergy_history"] is None
        else ("true" if demo["allergy_history"] else "false")
    )
    st.session_state["asthma"] = (
        "unknown"
        if demo.get("asthma_history") is None
        else ("true" if demo.get("asthma_history") else "false")
    )
    st.session_state["egfr"] = "" if demo["egfr"] is None else str(demo["egfr"])
    st.session_state["pregnancy_status"] = demo["pregnancy_status"]
    st.session_state["reaction"] = demo["prior_contrast_reaction"]
    st.session_state["loaded_demo_name"] = case_name


# -----------------------------
# Helpers
# -----------------------------
def safe_get(obj: Any, key: str, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def get_risk_style(risk_level: str) -> dict:
    risk_level = (risk_level or "").lower()

    styles = {
        "high": {
            "background": "rgba(220, 38, 38, 0.14)",
            "border": "rgba(239, 68, 68, 0.55)",
            "text_color": "#FCA5A5",
        },
        "moderate": {
            "background": "rgba(245, 158, 11, 0.14)",
            "border": "rgba(245, 158, 11, 0.50)",
            "text_color": "#FCD34D",
        },
        "low": {
            "background": "rgba(34, 197, 94, 0.14)",
            "border": "rgba(34, 197, 94, 0.50)",
            "text_color": "#86EFAC",
        },
        "insufficient_information": {
            "background": "rgba(107, 114, 128, 0.18)",
            "border": "rgba(156, 163, 175, 0.45)",
            "text_color": "#D1D5DB",
        },
    }

    return styles.get(
        risk_level,
        {
            "background": "rgba(255,255,255,0.03)",
            "border": "rgba(128,128,128,0.25)",
            "text_color": "#FFFFFF",
        },
    )

PRIOR_CONTRAST_REACTION_LABELS = {
    "none": "None — no previous contrast reaction",
    "mild": (
        "Mild — limited hives/itching, limited swelling, scratchy throat, "
        "nasal congestion/sneezing, mild nausea/warmth"
    ),
    "moderate": (
        "Moderate — diffuse hives/itching, facial swelling without breathing difficulty, "
        "throat tightness/hoarseness without breathing difficulty, mild wheeze/no low oxygen"
    ),
    "severe": (
        "Severe — breathing difficulty/low oxygen, throat swelling with stridor, "
        "low blood pressure/shock, or collapse"
    ),
    "unknown": "Unknown — previous reaction reported, but details/severity are unclear",
}


def get_action_style(action: str) -> dict:
    action = (action or "").lower()

    if action in {"hold_and_review", "hold_and_clarify"}:
        return {
            "background": "rgba(220, 38, 38, 0.12)",
            "border": "rgba(239, 68, 68, 0.45)",
            "text_color": "#FCA5A5",
        }

    if action in {"proceed_with_caution", "proceed_with_caution_or_review"}:
        return {
            "background": "rgba(245, 158, 11, 0.12)",
            "border": "rgba(245, 158, 11, 0.45)",
            "text_color": "#FCD34D",
        }
    if action == "urgent_radiologist_review":
        return {
            "background": "#4a1f1f",
            "border": "#f97316",
            "text_color": "#fed7aa",
        }

    if action == "proceed":
        return {
            "background": "rgba(34, 197, 94, 0.12)",
            "border": "rgba(34, 197, 94, 0.45)",
            "text_color": "#86EFAC",
        }

    return {
        "background": "rgba(255,255,255,0.03)",
        "border": "rgba(128,128,128,0.25)",
        "text_color": "#FFFFFF",
    }


def render_badge(
    label: str,
    value: str,
    background: str = "rgba(255,255,255,0.02)",
    border: str = "rgba(128,128,128,0.25)",
    text_color: str = "#FFFFFF",
):
    st.markdown(
        f"""
        <div style="
            padding: 0.85rem 1rem;
            border-radius: 0.9rem;
            border: 1px solid {border};
            background: {background};
            margin-bottom: 0.5rem;
            min-height: 112px;
        ">
            <div style="font-size: 0.85rem; opacity: 0.78; color: {text_color};">{label}</div>
            <div style="font-size: 1.15rem; font-weight: 700; color: {text_color}; word-break: break-word;">
                {value}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_medication_precautions(precautions: list):
    if not precautions:
        return

    st.markdown("#### ⚠️ Contrast-Related Clinical Precautions")

    for item in precautions:
        medication = safe_get(item, "medication", "Medication")
        flag = safe_get(item, "flag", "")
        message = safe_get(item, "message", "")
        post_scan_instructions = safe_get(item, "post_scan_instructions", "")

        st.warning(
            f"""
**{medication}**

{message}

**Post-scan instruction:** {post_scan_instructions}

`{flag}`
            """
        )

def render_safety_precautions(precautions: list):
    if not precautions:
        return

    st.markdown("#### ⚠️ Contrast Safety Precautions")

    for item in precautions:
        category = safe_get(item, "category", "Safety Precaution")
        flag = safe_get(item, "flag", "")
        message = safe_get(item, "message", "")
        pre_scan_instruction = safe_get(item, "pre_scan_instruction", "")
        post_scan_instruction = safe_get(item, "post_scan_instruction", None)

        precaution_text = f"""
**{category}**

{message}

**Pre-scan instruction:** {pre_scan_instruction}

`{flag}`
        """

        if post_scan_instruction:
            precaution_text += f"\n\n**Post-scan instruction:** {post_scan_instruction}"

        st.warning(precaution_text)

def format_confidence_label(score: float, label: str) -> str:
    return f"{label.title()} ({score:.2f})"


def prettify_protocol(protocol: str) -> str:
    if not protocol:
        return "n/a"
    return protocol.replace("_", " ").strip().title()

def humanize_action(action):
    mapping = {
        "proceed": "Proceed",
        "hold_and_review": "Hold and Review",
        "hold_and_clarify": "Hold and Clarify Missing Information",
        "proceed_with_caution": "Proceed With Caution / Review",
        "urgent_radiologist_review": "Urgent Radiologist Review",
    }

    return mapping.get(action, action)



SOURCE_URLS = {
    "ACR-Manual-on-Contrast-Media": "https://github.com/paschal-godwin/Radiology-Protocol-and-Risk-Decision-Support-System/blob/main/data/guidelines/ACR-Manual-on-Contrast-Media.pdf",
    "CT imaging_guidelines": "https://github.com/paschal-godwin/Radiology-Protocol-and-Risk-Decision-Support-System/blob/main/data/guidelines/CT%20imaging_guidelines.pdf",
}


def build_source_link(source_title, page_number=None):
    base_url = SOURCE_URLS.get(source_title)

    if not base_url:
        return None

    if page_number is not None:
        return f"{base_url}#page={page_number}"

    return base_url


def render_citation_card(citation: Any):
    claim = safe_get(citation, "claim", "unknown_claim")
    topic = safe_get(citation, "topic", "unknown_topic")
    source_title = safe_get(citation, "source_title", "Unknown Source")
    page_number = safe_get(citation, "page_number", None)
    snippet = safe_get(citation, "snippet", "")

    page_text = f"p. {page_number}" if page_number is not None else "page n/a"
    source_link = build_source_link(source_title, page_number)
    
    st.markdown(
        f"""
        <div style="
            padding: 1rem;
            border-radius: 0.8rem;
            border: 1px solid rgba(128,128,128,0.25);
            margin-bottom: 0.75rem;
        ">
            <div style="font-size: 0.9rem; opacity: 0.75; margin-bottom: 0.35rem;">
                Claim: <b>{claim}</b> &nbsp;|&nbsp; Topic: <b>{topic}</b>
            </div>
            <div style="font-size: 1rem; font-weight: 600; margin-bottom: 0.35rem;">
                {source_title} ({page_text})
            </div>
            <div style="font-size: 0.96rem; line-height: 1.5;">
            {f'<a href="{source_link}" target="_blank">🔗 Open source document ({page_text})</a><br><br>' if source_link else ''}
            {snippet}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    

# -----------------------------
# Input area
# -----------------------------
def build_case_input_from_form() -> RadiologyCaseInput | None:
    st.subheader("Patient Case Input")

    col1, col2, col3 = st.columns(3)


    with col1:
        age = st.number_input(
            "Age",
            min_value=0,
            max_value=120,
            step=1,
            key="age",
        )

        sex = st.selectbox(
            "Sex",
            options=[member.value for member in Sex],
            key="sex",
            on_change=handle_sex_change,
        )

        exam_requested = st.text_input(
            "Exam Requested",
            key="exam",
        )

    with col2:
        contrast_requested = st.checkbox(
            "Contrast Requested",
            key="contrast",
        )

        urgency_level = st.selectbox(
            "Urgency Level",
            options=[member.value for member in UrgencyLevel],
            key="urgency",
        )

        allergy_history = st.selectbox(
            "Allergy History",
            options=["false", "true", "unknown"],
            key="allergy",
        )

        asthma_history = st.selectbox(
            "Asthma History",
            options=["false", "true", "unknown"],
            key="asthma",
            help=(
                "Select true if the patient has a known history of asthma. "
                "This is separate from unrelated allergy history and prior contrast reaction."
            ),
        )

        metformin_use = st.selectbox(
            "Metformin Use",
            options=[member.value for member in MetforminUse],
            key="metformin",
        )
        thyroid_status = st.selectbox(
            "Thyroid Status",
            options=[member.value for member in ThyroidStatus],
            key="thyroid",
        )

    with col3:
        egfr_input = st.text_input(
            "eGFR (leave blank if unknown)",
            key="egfr",
        )

        if st.session_state["sex"] == "male":
            pregnancy_options = ["not_applicable"]
            pregnancy_help = "Pregnancy status is not applicable for male patients."
            disabled = True
        else:
            pregnancy_options = [
                PregnancyStatus.not_pregnant.value,
                PregnancyStatus.pregnant.value,
                PregnancyStatus.unknown.value,
            ]
            pregnancy_help = "For female patients, choose not_pregnant, pregnant, or unknown."
            disabled = False

        # make sure current value stays valid when options change
        if st.session_state.get("pregnancy_status") not in pregnancy_options:
            st.session_state["pregnancy_status"] = pregnancy_options[0]

        pregnancy_status = st.selectbox(
            "Pregnancy Status",
            options=pregnancy_options,
            key="pregnancy_status",
            disabled=disabled,
            help=pregnancy_help,
        )

        prior_contrast_reaction = st.selectbox(
            "Prior Contrast Reaction",
            options=[member.value for member in PriorContrastReaction],
            key="reaction",
            format_func=lambda value: PRIOR_CONTRAST_REACTION_LABELS.get(value, value),
            help=(
                "Choose the closest severity based on the previous reaction. "
                "If the details are unclear, choose unknown."
            ),
        )

        with st.expander("How to classify prior contrast reaction"):
            st.markdown(
                """
        **Mild:** limited hives/itching, limited swelling, scratchy throat, nasal congestion, sneezing, mild nausea/warmth.

        **Moderate:** diffuse hives/itching, facial swelling without breathing difficulty, throat tightness/hoarseness without breathing difficulty, mild wheeze without low oxygen.

        **Severe:** breathing difficulty, low oxygen, throat swelling with noisy breathing/stridor, low blood pressure, shock, collapse, or cardiac arrest.

        If the patient only says “I reacted before” but the symptoms are unclear, choose **Unknown**.
                """
            )

    egfr_value = None
    if egfr_input.strip():
        try:
            egfr_value = float(egfr_input.strip())
        except ValueError:
            st.error("eGFR must be a valid number or blank.")
            return None

    if allergy_history == "unknown":
        allergy_history_value = None
    else:
        allergy_history_value = allergy_history == "true"

    if asthma_history == "unknown":
        asthma_history_value = None
    else:
        asthma_history_value = asthma_history == "true"

    return RadiologyCaseInput(
        age=int(age),
        sex=Sex(sex),
        pregnancy_status=PregnancyStatus(pregnancy_status),
        exam_requested=exam_requested.strip() or "CT",
        contrast_requested=contrast_requested,
        urgency_level=UrgencyLevel(urgency_level),
        egfr=egfr_value,
        allergy_history=allergy_history_value,
        asthma_history=asthma_history_value,
        prior_contrast_reaction=PriorContrastReaction(prior_contrast_reaction),
        metformin_use=MetforminUse(metformin_use),
        thyroid_status=ThyroidStatus(thyroid_status),
        
    )


# -----------------------------
# Assessment output
# -----------------------------
def render_assessment(result: dict):
    overall = result["overall_decision"]
    protocol = result["protocol_recommendation"]
    explanation = result["explanation"]
    confidence = result.get("confidence")
    debug_trace = result.get("debug_trace", {})
    missing_info = result.get("missing_information", [])
    missing_info_severity = safe_get(
        overall,
        "missing_information_severity",
        "none",
    )

    st.subheader("Assessment Summary")

    overall_risk = safe_get(overall, "overall_risk_level", "n/a")
    recommended_action_raw = safe_get(overall, "recommended_action", "n/a")
    recommended_action = humanize_action(recommended_action_raw)
    can_proceed = str(safe_get(overall, "can_proceed", "n/a"))
    suggested_protocol = prettify_protocol(safe_get(protocol, "suggested_protocol", "n/a"))

    risk_style = get_risk_style(overall_risk)
    action_style = get_action_style(recommended_action_raw)

    top1, top2, top3, top4 = st.columns(4)

    with top1:
        render_badge(
            "Overall Risk",
            overall_risk,
            background=risk_style["background"],
            border=risk_style["border"],
            text_color=risk_style["text_color"],
        )

    with top2:
        render_badge(
            "Recommended Action",
            recommended_action,
            background=action_style["background"],
            border=action_style["border"],
            text_color=action_style["text_color"],
        )

    with top3:
        render_badge("Can Proceed", can_proceed)

    with top4:
        render_badge("Suggested Protocol", suggested_protocol)
        if recommended_action_raw == "urgent_radiologist_review":
            st.warning(
                "Emergency context detected: this does not remove the risk. "
                "It changes the workflow to urgent radiologist review and risk-benefit assessment."
            )
    multi_risk_escalation = safe_get(
        overall,
        "multi_risk_escalation",
        False,
    )

    if multi_risk_escalation:
        st.error(
            "Multiple concurrent contrast-related risks detected. "
            "Senior radiologist review is strongly recommended before proceeding."
        )
        
    if missing_info_severity == "high":
        st.error(
            "High-severity missing information detected. "
            "Critical information must be clarified before proceeding."
        )

    elif missing_info_severity == "moderate":
        st.warning(
            "Moderate-severity missing information detected. "
            "Clarification is recommended before proceeding."
        )
        
    st.markdown("---")

    left, right = st.columns([1.4, 1])

    with left:
        st.subheader("Why the System Made This Decision")
        st.write(safe_get(explanation, "reasoning_summary", ""))

        contrast_medication_precautions = result.get("contrast_medication_precautions", [])
        contrast_safety_precautions = result.get("contrast_safety_precautions", [])

        render_medication_precautions(contrast_medication_precautions)
        render_safety_precautions(contrast_safety_precautions)

        rule_based_factors = safe_get(explanation, "rule_based_factors", [])
        if rule_based_factors:
            st.markdown("**Rule-Based Factors**")
            for factor in rule_based_factors:
                st.write(f"- {factor}")

        if missing_info:
            st.markdown("**Missing Information**")
            for item in missing_info:
                st.write(f"- {item}")
    

        next_steps = safe_get(protocol, "next_steps", [])
        if next_steps:
            st.markdown("**Recommended Next Steps**")
            for step in next_steps:
                st.write(f"- {step}")

    with right:
        st.subheader("Confidence")
        if confidence:
            final_confidence = safe_get(confidence, "final_confidence", 0.0)
            confidence_label = safe_get(confidence, "confidence_label", "unknown")
            capped_by = safe_get(confidence, "capped_by", "unknown")
            human_limiter = humanize_confidence_limiter(capped_by)
            st.info(f"Primary limiting factor: {human_limiter}")

            st.metric(
                "Final Confidence",
                format_confidence_label(final_confidence, confidence_label),
            )
            st.write(f"**Confidence capped by:** `{capped_by}`")

            with st.expander("Confidence Breakdown", expanded=True):
                for field_name, title in [
                    ("rule_confidence", "Rule Confidence"),
                    ("retrieval_confidence", "Retrieval Confidence"),
                    ("citation_alignment_confidence", "Citation Alignment Confidence"),
                    ("completeness_confidence", "Completeness Confidence"),
                ]:
                    component = safe_get(confidence, field_name)
                    if component:
                        comp_score = safe_get(component, "score", 0.0)
                        comp_reasons = safe_get(component, "reasons", [])
                        st.write(f"**{title}:** {comp_score:.2f}")
                        for reason in comp_reasons:
                            st.write(f"- {reason}")
        else:
            st.info("No confidence data available.")

    st.markdown("---")

    st.subheader("Evidence-Backed Citations")
    citations = safe_get(explanation, "citations", [])
    if citations:
        for citation in citations:
            render_citation_card(citation)
    else:
        st.info("No citations were emitted for this case.")

    st.markdown("---")

    with st.expander("Technical Debug View"):
        st.markdown("### Rule Trace")
        st.json(safe_get(debug_trace, "rule_trace", {}))

        st.markdown("### Retrieval Queries")
        st.json(safe_get(debug_trace, "retrieval_queries", []))

        st.markdown("### Selected Evidence")
        st.json(safe_get(debug_trace, "selected_evidence", []))

        st.markdown("### Retrieval Topic Traces")
        st.json(safe_get(debug_trace, "retrieval_topics", []))


# -----------------------------
# Demo cases
# -----------------------------
def load_demo_case(case_name: str) -> dict:
    demos = {
        "High Renal + Severe Reaction": {
            "age": 60,
            "sex": "male",
            "pregnancy_status": "not_applicable",
            "exam_requested": "CT",
            "contrast_requested": True,
            "urgency_level": "routine",
            "egfr": 20.0,
            "allergy_history": True,
            "asthma_history": False,
            "prior_contrast_reaction": "severe",
            "thyroid_status": "normal",
            "metformin_use": "no",
        },
        "Pregnancy Review Case": {
            "age": 31,
            "sex": "female",
            "pregnancy_status": "pregnant",
            "exam_requested": "CT",
            "contrast_requested": True,
            "urgency_level": "routine",
            "egfr": 90.0,
            "allergy_history": False,
            "asthma_history": False,
            "prior_contrast_reaction": "none",
            "thyroid_status": "normal",
            "metformin_use": "no",
        },
        "Low Risk Proceed Case": {
            "age": 39,
            "sex": "female",
            "pregnancy_status": "not_pregnant",
            "exam_requested": "CT",
            "contrast_requested": True,
            "urgency_level": "routine",
            "egfr": 88.0,
            "allergy_history": False,
            "asthma_history": False,
            "prior_contrast_reaction": "none",
            "thyroid_status": "normal",
            "metformin_use": "no",
        },
    }
    return demos[case_name]


def render_sidebar():
    st.sidebar.title("CT Contrast Assistant V1")
    st.sidebar.write(
        "A deterministic radiology decision-support prototype for CT contrast risk assessment."
    )

    st.sidebar.markdown("### Demo Cases")
    selected_demo = st.sidebar.selectbox(
        "Load a demo scenario",
        options=[
            "None",
            "High Renal + Severe Reaction",
            "Pregnancy Review Case",
            "Low Risk Proceed Case",
        ],
        index=[
            "None",
            "High Renal + Severe Reaction",
            "Pregnancy Review Case",
            "Low Risk Proceed Case",
        ].index(st.session_state.get("loaded_demo_name", "None")),
    )

    if selected_demo != st.session_state.get("loaded_demo_name", "None"):
        load_demo_into_state(selected_demo)

    st.sidebar.markdown("### What this app shows")
    st.sidebar.write("- Rule-based risk assessment")
    st.sidebar.write("- Evidence-backed explanation")
    st.sidebar.write("- Confidence breakdown")
    st.sidebar.write("- Retrieval/debug observability")

    return selected_demo



# -----------------------------
# Main
# -----------------------------
def main():
    initialize_state()

    st.title("🩻 Radiology Protocol & Risk Decision Support System")
    st.caption("CT Contrast Assistant V1")

    selected_demo = render_sidebar()

    st.markdown(
        """
        This prototype combines:
        **deterministic clinical risk rules**, **topic-aware retrieval**,
        **claim-aware evidence selection**, and **confidence-aware explanations**.
        """
    )

    st.markdown("---")

    if selected_demo != "None":
        demo = load_demo_case(selected_demo)
        st.info(f"Loaded demo scenario: {selected_demo}")
        st.json(demo)

    case = build_case_input_from_form()

    st.markdown("---")
    run_clicked = st.button("Run Assessment", use_container_width=True)
    
    

    if run_clicked:
        if case is None:
            st.error("Please fix the input issues before running the assessment.")
            return

        try:
            with st.spinner("Running deterministic assessment..."):
                result = run_assessment(case)
                log_case_run(case, result)
            st.session_state["last_result"] = result
        except Exception as exc:
            st.error(f"Assessment failed: {exc}")
    
    if st.session_state.get("last_result") is not None:
        render_assessment(st.session_state["last_result"])

    st.link_button(
        "Leave Feedback",
        "https://forms.gle/kLsXhVtdE3wbZaZw5",
    )
    

    



if __name__ == "__main__":
    main()