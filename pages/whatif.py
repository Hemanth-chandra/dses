import pandas as pd
import streamlit as st
from common import run_case, default_case

st.title("🔁 What-if Simulator")
st.caption("Change the road conditions or a hospital's status and see how the decision changes, compared with the last case.")

if "last_out" not in st.session_state:
    st.session_state.last_case = default_case()
    st.session_state.last_out = run_case(st.session_state.last_case)
base_case, base_out = st.session_state.last_case, st.session_state.last_out

c1, c2, c3 = st.columns(3)
with c1:
    traffic = st.select_slider("Traffic", ["Low", "Medium", "Heavy"], value=base_case["traffic"])
    rain = st.toggle("Raining", value=base_case["rain"])
with c2:
    hour = st.slider("Hour of call", 0, 23, base_case["hour"])
    area = st.selectbox("Incident area", list(st.session_state.areas.index),
                        index=list(st.session_state.areas.index).index(base_case["area"]))
with c3:
    hdf = st.session_state.hospitals.copy()
    target = st.selectbox("Change a hospital", hdf["name"])
    i = hdf.index[hdf["name"] == target][0]
    hdf.loc[i, "icu_beds"] = st.number_input("ICU beds free", 0, 20, int(hdf.loc[i, "icu_beds"]))
    hdf.loc[i, "on_diversion"] = st.checkbox("On diversion (overloaded)", value=bool(hdf.loc[i, "on_diversion"]))

new_case = dict(base_case, traffic=traffic, rain=rain, hour=hour, area=area)
new_out = run_case(new_case, hospitals_df=hdf)

def summary(out):
    b = out["best"]
    return (b["name"], f"{b['total_min']} min") if b else ("Dispatcher to decide", "-")

st.divider()
l, r = st.columns(2)
bn, bt = summary(base_out)
nn, nt = summary(new_out)
with l:
    st.markdown("#### Original case")
    st.info(f"**{bn}**  \nTime to care: **{bt}**")
with r:
    st.markdown("#### What-if case")
    (st.warning if nn != bn else st.success)(f"**{nn}**  \nTime to care: **{nt}**" + ("  \n⚠️ Decision changed" if nn != bn else "  \nSame decision"))

for a in new_out["alerts"]:
    getattr(st, a["level"])(f"{a['message']}  (rule {a['rule']})")

rows = []
old = {x["id"]: x for x in base_out["results"]}
for x in new_out["results"]:
    o = old[x["id"]]
    rows.append({"Hospital": x["name"], "Original": f"{'✓' if o['accepted'] else '✗'} {o['total_min']} min",
                 "What-if": f"{'✓' if x['accepted'] else '✗'} {x['total_min']} min",
                 "Reason (what-if)": "; ".join(x["reasons"]) or "-"})
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
