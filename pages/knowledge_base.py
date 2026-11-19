import json
import pandas as pd
import streamlit as st
from engine import describe_rule
from common import EMERGENCY_TYPES

st.title("📘 Knowledge Base")
st.caption("All rules are stored in knowledge_base/rules.json, separate from the inference engine. "
           "A knowledge engineer can switch rules off or add new ones without changing any code.")

stage_names = {"needs": "Stage 1: Needs, severity and road rules (forward chaining)",
               "filter": "Stage 2: Hospital filter rules", "decide": "Stage 3: Decision and alert rules"}
for stage, title in stage_names.items():
    st.subheader(title)
    rows = []
    for r in st.session_state.rules:
        if r["stage"] == stage:
            rows.append({"Active": not r.get("disabled", False), "ID": r["id"], "Priority": r["priority"],
                         "Rule": describe_rule(r), "Meaning": r["description"], "Knowledge source": r["source"]})
    edited = st.data_editor(pd.DataFrame(rows), hide_index=True, width="stretch", key=f"kb_{stage}",
                            disabled=["ID", "Priority", "Rule", "Meaning", "Knowledge source"])
    for _, row in edited.iterrows():
        for r in st.session_state.rules:
            if r["id"] == row["ID"]:
                r["disabled"] = not row["Active"]

st.divider()
st.subheader("Add a new facility rule")
st.caption("Example of knowledge acquisition: a doctor says \"elderly heart patients should also go where there is an ICU\".")
names = st.session_state.facility_names
c1, c2, c3 = st.columns(3)
etype = c1.selectbox("IF emergency type is", EMERGENCY_TYPES)
age = c2.selectbox("AND age group is", ["Any", "Adult", "Child (below 14)", "Elderly (above 60)"])
need = c3.multiselect("THEN also need", list(names), format_func=lambda c: names[c])
desc = st.text_input("Meaning in plain words")
if st.button("Add rule", type="primary", disabled=not need):
    new_id = f"N{sum(r['id'].startswith('N') for r in st.session_state.rules) + 1}"
    cond = [{"fact": "emergency_type", "op": "==", "value": etype}]
    if age != "Any":
        cond.append({"fact": "age_group", "op": "==", "value": age})
    st.session_state.rules.append({"id": new_id, "stage": "needs", "priority": 50, "source": "Added in app",
                                   "description": desc or f"{etype} needs {', '.join(need)}", "if": cond,
                                   "then": [{"action": "add", "fact": "needs", "value": need}]})
    st.success(f"Rule {new_id} added. It is used from the next recommendation.")
    st.rerun()

st.download_button("Download rules.json", json.dumps(st.session_state.rules, indent=2), "rules.json", "application/json")
