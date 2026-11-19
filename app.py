import streamlit as st
from common import init_state, sidebar_note

st.set_page_config(page_title="Golden-Hour DSS", page_icon="🚑", layout="wide")
init_state()

pages = {
    "Overview": [st.Page("pages/overview.py", title="System Overview", icon="🏠", default=True)],
    "Decision support": [
        st.Page("pages/advisor.py", title="Dispatch Advisor", icon="🚑"),
        st.Page("pages/explanation.py", title="Explanation (How / Why)", icon="🔍"),
        st.Page("pages/whatif.py", title="What-if Simulator", icon="🔁"),
    ],
    "Knowledge and data": [
        st.Page("pages/knowledge_base.py", title="Knowledge Base", icon="📘"),
        st.Page("pages/hospitals.py", title="Hospital Status", icon="🏥"),
    ],
    "Learning and evaluation": [
        st.Page("pages/feedback.py", title="Feedback Log", icon="📝"),
        st.Page("pages/evaluation.py", title="Evaluation", icon="📊"),
    ],
}
nav = st.navigation(pages)
sidebar_note()
nav.run()
