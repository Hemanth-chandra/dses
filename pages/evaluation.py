import pandas as pd
import streamlit as st
from common import run_case, BASE

st.title("📊 Evaluation")
st.caption("20 test calls are run through the system and through the usual method (send to the nearest hospital). "
           "A choice is counted as appropriate if the hospital has every facility the patient needs and a free bed.")

sc = pd.read_csv(BASE / "data" / "scenarios.csv")
rows = []
for _, s in sc.iterrows():
    case = {"area": s["area"], "emergency_type": s["emergency_type"], "head_injury": bool(s["head_injury"]),
            "heavy_bleeding": bool(s["heavy_bleeding"]), "conscious": bool(s["conscious"]),
            "major_burns": bool(s["major_burns"]), "age_group": s["age_group"], "traffic": s["traffic"],
            "rain": bool(s["rain"]), "hour": int(s["hour"])}
    out = run_case(case)
    best, base = out["best"], out["baseline"]
    base_res = next(r for r in out["results"] if r["id"] == base["id"])
    rows.append({"#": s["id"], "Call": f"{s['emergency_type']}, {s['area']}",
                 "System choice": best["name"] if best else "Dispatcher decides",
                 "System OK": best is not None, "System time (min)": best["total_min"] if best else None,
                 "Nearest hospital": base["name"], "Nearest OK": base_res["accepted"],
                 "Nearest time (min)": base_res["total_min"],
                 "Nearest problem": "; ".join(base_res["reasons"]) or "-"})
df = pd.DataFrame(rows)

sys_ok, near_ok = df["System OK"].mean() * 100, df["Nearest OK"].mean() * 100
c1, c2, c3 = st.columns(3)
c1.metric("Appropriate hospital: system", f"{sys_ok:.0f}%")
c2.metric("Appropriate hospital: nearest", f"{near_ok:.0f}%", delta=f"{near_ok - sys_ok:.0f} pts", delta_color="normal")
c3.metric("Second transfers avoided", int((df["System OK"] & ~df["Nearest OK"]).sum()), help="Calls where the nearest hospital was unsuitable but the system found a suitable one")

chart = pd.DataFrame({"Method": ["Golden-Hour system", "Nearest hospital"], "Appropriate choices (%)": [sys_ok, near_ok]})
import altair as alt
bars = alt.Chart(chart).mark_bar(size=34).encode(x=alt.X("Appropriate choices (%):Q", scale=alt.Scale(domain=[0, 100])),
                                                 y=alt.Y("Method:N", title=None, sort=None),
                                                 color=alt.Color("Method:N", scale=alt.Scale(range=["#C62828", "#9e9e9e"]), legend=None))
labels = bars.mark_text(align="left", dx=5).encode(text=alt.Text("Appropriate choices (%):Q", format=".0f"))
st.altair_chart((bars + labels).properties(height=140), width="stretch")

st.markdown("**Trade-off:** the system sometimes chooses a hospital a few minutes further away, but the nearest "
            "hospital in those cases could not treat the patient and a second transfer would cost much more time.")
both = df[df["System OK"] & df["Nearest OK"]]
st.markdown(f"When both methods are appropriate, average time is **{both['System time (min)'].mean():.0f} min** "
            f"(system) vs **{both['Nearest time (min)'].mean():.0f} min** (nearest).")

st.subheader("Test case details")
st.dataframe(df, hide_index=True, width="stretch")
st.caption("Limitation: test calls and hospital data are simulated; a real evaluation would use past 108 dispatch records.")
