import pandas as pd
import streamlit as st
from common import BASE

st.title("🏥 Hospital Status Board")
st.caption("In a real system this board would be updated live by the hospitals. Here you can edit beds, waiting "
           "time and diversion status to simulate changes. Facilities are fixed hospital knowledge.")

df = st.session_state.hospitals
names = st.session_state.facility_names
view = df.copy()
view["facilities"] = view["facilities"].str.replace(";", ", ")
edited = st.data_editor(
    view[["id", "name", "area", "facilities", "icu_beds", "general_beds", "avg_wait_min", "open_24x7", "on_diversion", "type"]],
    hide_index=True, width="stretch",
    disabled=["id", "name", "area", "facilities", "type"],
    column_config={
        "icu_beds": st.column_config.NumberColumn("ICU beds free", min_value=0, max_value=50),
        "general_beds": st.column_config.NumberColumn("General beds free", min_value=0, max_value=200),
        "avg_wait_min": st.column_config.NumberColumn("Avg wait (min)", min_value=0, max_value=180),
        "open_24x7": st.column_config.CheckboxColumn("Open 24x7"),
        "on_diversion": st.column_config.CheckboxColumn("On diversion"),
    })
for col in ["icu_beds", "general_beds", "avg_wait_min", "open_24x7", "on_diversion"]:
    st.session_state.hospitals[col] = edited[col].values

c1, c2, c3 = st.columns(3)
c1.metric("Total free ICU beds", int(edited["icu_beds"].sum()))
c2.metric("Hospitals on diversion", int(edited["on_diversion"].sum()))
c3.metric("Open 24x7", f"{int(edited['open_24x7'].sum())} / {len(edited)}")

if st.button("Reset to original data"):
    st.session_state.hospitals = pd.read_csv(BASE / "data" / "hospitals.csv")
    st.rerun()

with st.expander("Facility codes"):
    for k, v in names.items():
        st.markdown(f"- **{k}**: {v}")
