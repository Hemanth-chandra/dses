"""Shared helpers for all pages: data loading, session state and the input form."""
from pathlib import Path
import pandas as pd
import streamlit as st
import engine

BASE = Path(__file__).parent

EMERGENCY_TYPES = ["Road accident", "Heart attack signs", "Stroke signs", "Burns",
                   "Pregnancy complication", "Snake bite / poisoning", "Other / general"]
AGE_GROUPS = ["Adult", "Child (below 14)", "Elderly (above 60)"]


def init_state():
    if "hospitals" not in st.session_state:
        st.session_state.hospitals = pd.read_csv(BASE / "data" / "hospitals.csv")
    if "areas" not in st.session_state:
        st.session_state.areas = pd.read_csv(BASE / "data" / "areas.csv").set_index("area")
    if "rules" not in st.session_state:
        st.session_state.rules = engine.load_rules()
    if "feedback" not in st.session_state:
        st.session_state.feedback = []
    if "facility_names" not in st.session_state:
        st.session_state.facility_names = engine.load_facility_names()


def active_rules():
    return [r for r in st.session_state.rules if not r.get("disabled")]


def run_case(case, hospitals_df=None, rules=None):
    hospitals_df = st.session_state.hospitals if hospitals_df is None else hospitals_df
    rules = active_rules() if rules is None else rules
    area = st.session_state.areas.loc[case["area"]]
    facts_in = {k: v for k, v in case.items() if k != "area"}
    return engine.run(facts_in, hospitals_df.to_dict("records"), rules, area["lat"], area["lon"])


def default_case():
    return {"area": "Morar", "emergency_type": "Road accident", "head_injury": True,
            "heavy_bleeding": False, "conscious": True, "major_burns": False,
            "age_group": "Adult", "traffic": "Heavy", "rain": False, "hour": 18}


def case_form(key="main", case=None):
    """Input form used on the advisor page. Returns the case dict."""
    case = case or st.session_state.get("last_case", default_case())
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Call details**")
        etype = st.selectbox("Emergency type", EMERGENCY_TYPES, index=EMERGENCY_TYPES.index(case["emergency_type"]), key=f"{key}_type")
        age = st.selectbox("Age group", AGE_GROUPS, index=AGE_GROUPS.index(case["age_group"]), key=f"{key}_age")
        head = st.checkbox("Head injury", value=case["head_injury"], key=f"{key}_head")
        bleed = st.checkbox("Heavy bleeding", value=case["heavy_bleeding"], key=f"{key}_bleed")
        unconscious = st.checkbox("Patient is unconscious", value=not case["conscious"], key=f"{key}_unc")
        burns = st.checkbox("Major burns (large area)", value=case["major_burns"], key=f"{key}_burn")
    with c2:
        st.markdown("**Location and road conditions**")
        areas = list(st.session_state.areas.index)
        area = st.selectbox("Incident area (Gwalior)", areas, index=areas.index(case["area"]), key=f"{key}_area")
        hour = st.slider("Time of call (hour, 24h)", 0, 23, case["hour"], key=f"{key}_hour")
        traffic = st.radio("Traffic level", ["Low", "Medium", "Heavy"], index=["Low", "Medium", "Heavy"].index(case["traffic"]), horizontal=True, key=f"{key}_traffic")
        rain = st.toggle("Raining", value=case["rain"], key=f"{key}_rain")
    return {"area": area, "emergency_type": etype, "head_injury": head, "heavy_bleeding": bleed,
            "conscious": not unconscious, "major_burns": burns, "age_group": age,
            "traffic": traffic, "rain": rain, "hour": hour}


def facility_text(codes):
    names = st.session_state.facility_names
    return ", ".join(names.get(c, c) for c in sorted(codes))


def sidebar_note():
    st.sidebar.markdown("---")
    st.sidebar.caption("Golden-Hour DSS · Decision Support & Expert Systems course project · "
                       "S. Hemanth Chandra (2025MS_020), IIITM Gwalior")
    st.sidebar.caption("Prototype with simulated hospital data. Final decision always rests with the dispatcher.")
