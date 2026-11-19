import pandas as pd
import streamlit as st

st.title("📝 Feedback Log")
st.caption("Every dispatch is recorded. Overrides and their reasons are reviewed by the knowledge engineer "
           "to correct or add rules. This is the feedback loop of the system.")

log = st.session_state.feedback
if st.button("Load sample entries (for demo)"):
    st.session_state.feedback += [
        {"time": "18-11 09:12", "area": "Lashkar", "emergency": "Road accident", "suggested": "Gwalior Trauma & Ortho Centre", "chosen": "Gwalior Trauma & Ortho Centre", "override": "No", "reason": "-"},
        {"time": "18-11 11:40", "area": "Morar", "emergency": "Heart attack signs", "suggested": "Heartline Cardiac Institute", "chosen": "Heartline Cardiac Institute", "override": "No", "reason": "-"},
        {"time": "18-11 14:05", "area": "Hazira", "emergency": "Burns", "suggested": "Chambal Burns & Plastic Surgery Centre", "chosen": "Chambal Burns & Plastic Surgery Centre", "override": "No", "reason": "-"},
        {"time": "18-11 17:55", "area": "City Centre", "emergency": "Road accident", "suggested": "Sanjeevani Multispeciality Hospital", "chosen": "District General Hospital", "override": "Yes", "reason": "Patient has government health card, family requested"},
        {"time": "18-11 19:20", "area": "Thatipur", "emergency": "Stroke signs", "suggested": "Nova Neuro & Stroke Centre", "chosen": "Sanjeevani Multispeciality Hospital", "override": "Yes", "reason": "Road blocked near Gole Ka Mandir due to procession"},
        {"time": "18-11 22:10", "area": "Kampoo", "emergency": "Pregnancy complication", "suggested": "Shishu Mata Hospital", "chosen": "Shishu Mata Hospital", "override": "No", "reason": "-"},
    ]
    st.rerun()

if not log:
    st.info("No dispatches yet. Confirm a dispatch on the Dispatch Advisor page, or load sample entries.")
else:
    df = pd.DataFrame(log)
    c1, c2, c3 = st.columns(3)
    c1.metric("Dispatches", len(df))
    c2.metric("Overrides", int((df["override"] == "Yes").sum()))
    c3.metric("Override rate", f"{(df['override'] == 'Yes').mean() * 100:.0f}%")
    st.dataframe(df, hide_index=True, width="stretch")
    ov = df[df["override"] == "Yes"]
    if len(ov):
        st.subheader("Points for rule review")
        for _, r in ov.iterrows():
            st.markdown(f"- {r['emergency']} in {r['area']}: suggested *{r['suggested']}*, dispatcher chose "
                        f"*{r['chosen']}* because \"{r['reason']}\".")
        st.caption("Repeated reasons (for example road blocks or patient insurance) show missing inputs or rules "
                   "that should be added in the next version.")
    st.download_button("Download log (CSV)", df.to_csv(index=False), "feedback_log.csv", "text/csv")
