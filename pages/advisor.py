from datetime import datetime
import pandas as pd
import streamlit as st
import altair as alt
from common import case_form, run_case, facility_text

st.title("🚑 Dispatch Advisor")
st.caption("Enter the details from the emergency call. The system suggests a hospital and explains why.")

with st.form("call_form"):
    case = case_form("adv")
    submitted = st.form_submit_button("Recommend hospital", type="primary", width="stretch")

if submitted or "last_out" not in st.session_state:
    st.session_state.last_case = case
    st.session_state.last_out = run_case(case)

case, out = st.session_state.last_case, st.session_state.last_out
facts, best, base = out["facts"], out["best"], out["baseline"]

st.divider()
if best:
    st.success(f"### ✅ Recommended: {best['name']}\n{best['area']} · {best['distance_km']} km · about **{best['total_min']} min** to care "
               f"({best['travel_min']} min travel + {best['wait_min']} min wait)")
else:
    st.error("### No suitable hospital found. Dispatcher must decide.")
m2, m3, m4 = st.columns(3)
m2.metric("Estimated time to care", f"{best['total_min']} min" if best else "-")
m3.metric("Severity", facts["severity"])
m4.metric("Hospitals rejected", sum(not r["accepted"] for r in out["results"]))

st.markdown(f"**Facilities needed:** {facility_text(facts['needs'])}")

for a in out["alerts"]:
    getattr(st, a["level"])(f"{a['message']}  (rule {a['rule']})")

if best and base["id"] != best["id"]:
    base_res = next(r for r in out["results"] if r["id"] == base["id"])
    why = "; ".join(base_res["reasons"]) if base_res["reasons"] else "slower overall"
    st.warning(f"The nearest hospital is **{base['name']}** ({base['distance_km']} km), but it was not chosen: {why}.")

st.subheader("Suitable hospitals (fastest first)")
acc = [r for r in out["results"] if r["accepted"]]
if acc:
    df = pd.DataFrame([{"Rank": i + 1, "Hospital": r["name"], "Area": r["area"], "Distance (km)": r["distance_km"],
                        "Travel (min)": r["travel_min"], "Wait (min)": r["wait_min"], "Total (min)": r["total_min"],
                        "ICU beds free": r["icu_beds"]} for i, r in enumerate(acc[:5])])
    st.dataframe(df, hide_index=True, width="stretch")
else:
    st.error("No hospital meets all the needs.")

left, right = st.columns([1, 1])
with left:
    st.subheader("Rejected hospitals")
    for r in out["results"]:
        if not r["accepted"]:
            st.markdown(f"- **{r['name']}** ({r['distance_km']} km): {'; '.join(r['reasons'])} · rule {', '.join(r['rules_fired'])}")
with right:
    st.subheader("Location view")
    area = st.session_state.areas.loc[case["area"]]
    pts = [{"lat": area["lat"], "lon": area["lon"], "label": f"Incident ({case['area']})", "status": "Incident"}]
    for r in out["results"]:
        status = "Recommended" if best and r["id"] == best["id"] else ("Suitable" if r["accepted"] else "Rejected")
        pts.append({"lat": r["lat"], "lon": r["lon"], "label": r["name"].split(" ")[0] + " " + r["name"].split(" ")[1], "status": status})
    pdf = pd.DataFrame(pts)
    t1, t2 = st.tabs(["Schematic", "Street map"])
    with t1:
        colors = alt.Scale(domain=["Incident", "Recommended", "Suitable", "Rejected"], range=["#d62728", "#1f77b4", "#2ca02c", "#b0b0b0"])
        base_ch = alt.Chart(pdf).encode(x=alt.X("lon:Q", scale=alt.Scale(zero=False), axis=None),
                                        y=alt.Y("lat:Q", scale=alt.Scale(zero=False), axis=None))
        pts_ch = base_ch.mark_circle(size=160, opacity=0.9).encode(color=alt.Color("status:N", scale=colors, legend=alt.Legend(orient="bottom", title=None)), tooltip=["label", "status"])
        txt = base_ch.mark_text(align="left", dx=8, fontSize=11).encode(text="label")
        st.altair_chart((pts_ch + txt).properties(height=330), width="stretch")
    with t2:
        cmap = {"Incident": "#d62728", "Recommended": "#1f77b4", "Suitable": "#2ca02c", "Rejected": "#9e9e9e"}
        pdf["color"] = pdf["status"].map(cmap)
        st.map(pdf, latitude="lat", longitude="lon", color="color", size=90, zoom=11, height=330)

st.divider()
st.subheader("Dispatcher decision")
c1, c2 = st.columns([2, 3])
names = [r["name"] for r in out["results"]]
with c1:
    choice = st.selectbox("Send ambulance to", names, index=names.index(best["name"]) if best else 0)
with c2:
    reason = st.text_input("Reason (required if you override the suggestion)", placeholder="e.g. road blocked near Phool Bagh")
if st.button("Confirm dispatch"):
    overridden = (not best) or choice != best["name"]
    if overridden and not reason.strip():
        st.error("Please give a reason for the override. It is used to review the rules.")
    else:
        st.session_state.feedback.append({
            "time": datetime.now().strftime("%d-%m %H:%M"), "area": case["area"], "emergency": case["emergency_type"],
            "suggested": best["name"] if best else "none", "chosen": choice,
            "override": "Yes" if overridden else "No", "reason": reason.strip() or "-"})
        st.success(f"Dispatch to {choice} recorded" + (" as an override." if overridden else "."))
