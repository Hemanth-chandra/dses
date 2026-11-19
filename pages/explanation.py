import pandas as pd
import streamlit as st
from common import run_case, default_case, facility_text

st.title("🔍 Explanation: How and Why")
if "last_out" not in st.session_state:
    st.session_state.last_case = default_case()
    st.session_state.last_out = run_case(st.session_state.last_case)
case, out = st.session_state.last_case, st.session_state.last_out
facts = out["facts"]

st.caption(f"Explaining the last case: **{case['emergency_type']}** in **{case['area']}** at {case['hour']}:00, "
           f"traffic {case['traffic'].lower()}{', raining' if case['rain'] else ''}. Change it on the Dispatch Advisor page.")

st.subheader("HOW the conclusion was reached")
st.markdown("**Step 1: Forward chaining on the call facts.** In every cycle the engine collects all rules whose "
            "conditions are true (the conflict set), fires the one with the highest priority, adds the new facts, "
            "and repeats until no rule can fire.")
st.dataframe(pd.DataFrame([{"Cycle": t["cycle"], "Conflict set": ", ".join(t["conflict_set"]), "Rule fired": t["fired"],
                            "Rule meaning": t["description"], "New facts": t["changes"]} for t in out["trace"]]),
             hide_index=True, width="stretch")
st.markdown(f"Result: severity = **{facts['severity']}**, facilities needed = **{facility_text(facts['needs'])}**, "
            f"ambulance speed = **{round(facts['speed_kmph'] * facts['speed_factor'])} km/h**, time limit = **{facts['time_limit']} min**.")

st.markdown("**Step 2: Each hospital checked against the filter rules (F1-F5).**")
st.dataframe(pd.DataFrame([{"Hospital": r["name"], "Result": "Accepted" if r["accepted"] else "Rejected",
                            "Rules fired": ", ".join(r["rules_fired"]) or "-", "Reason": "; ".join(r["reasons"]) or "-",
                            "Travel + wait (min)": f"{r['travel_min']} + {r['wait_min']} = {r['total_min']}"} for r in out["results"]]),
             hide_index=True, width="stretch")

st.markdown("**Step 3: Ranking and decision rules (D1-D4).** Accepted hospitals are sorted by total time "
            "(travel time + expected waiting time). Then the decision rules add alerts for the dispatcher.")
if out["alerts"]:
    for a in out["alerts"]:
        st.markdown(f"- Rule **{a['rule']}**: {a['message']}")
else:
    st.markdown("- No decision rule fired for this case.")

st.subheader("WHY each piece of information is asked")
why = {
    "Emergency type": "decides which facilities are needed (rules A1, A2, A4-A7, A9)",
    "Head injury": "a head injury needs CT scan and neurosurgery (rule A1)",
    "Heavy bleeding": "needs a blood bank and makes the patient critical (rules A3, C2)",
    "Unconscious": "makes the patient critical, which then requires an ICU (rules C1 → C3)",
    "Major burns": "needs a burn unit (rule A6)",
    "Age group": "children need paediatric care (rule A8)",
    "Incident area": "used to work out the distance to each hospital",
    "Traffic and rain": "change the ambulance speed and so the travel time (rules E1-E4)",
    "Time of call": "some hospitals are closed at night (rules E5 → F3)",
}
for k, v in why.items():
    st.markdown(f"- **{k}:** {v}")
