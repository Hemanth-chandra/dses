import streamlit as st

st.title("🚑 Golden-Hour: Emergency Hospital Dispatch Advisor")
st.markdown("A decision support expert system that helps a 108 ambulance dispatcher in Gwalior choose "
            "**the right hospital**, not just the nearest one.")

c1, c2, c3 = st.columns(3)
c1.metric("Hospitals in knowledge base", len(st.session_state.hospitals))
c2.metric("Rules in knowledge base", len(st.session_state.rules))
c3.metric("City areas covered", len(st.session_state.areas))

st.subheader("The problem")
st.write("When an accident call comes in, the patient is usually taken to the closest hospital. If that hospital "
         "has no CT scan, no specialist or no free ICU bed, the patient has to be shifted again and precious time "
         "in the first hour after the injury (the golden hour) is lost. The dispatcher has only a minute or two to "
         "decide and cannot remember which hospital has which facility and how many beds are free right now.")

st.subheader("How the system works")
st.graphviz_chart("""
digraph {
  rankdir=LR; nodesep=0.25; ranksep=0.5; node [shape=box, fontname="Helvetica", fontsize=11];
  {rank=same; call; road; hosp; kb;}
  call [label="Emergency call\\n(type, details, area)"];
  road [label="Road conditions\\n(traffic, rain, time)"];
  hosp [label="Hospital status\\n(facilities, beds, wait)"];
  kb   [label="Knowledge base\\n(IF-THEN rules)"];
  ie   [label="Inference engine\\n(forward chaining)"];
  out  [label="Recommended hospital\\n+ reasons + alerts"];
  disp [label="Dispatcher\\n(accept / override)"];
  call -> ie; road -> ie; hosp -> ie; kb -> ie; ie -> out -> disp;
  disp -> kb [label=" feedback: rules reviewed", style=dashed, constraint=false];
}
""")

col1, col2 = st.columns(2)
with col1:
    st.subheader("System components")
    st.markdown("""
- **Inputs:** emergency type, patient details, incident area, traffic, rain, time of call, hospital status
- **Processor:** forward-chaining inference engine working on the rule base
- **Outputs:** recommended hospital, top options with travel + waiting time, rejected hospitals with reasons, alerts
- **Feedback:** dispatcher overrides with reasons, reviewed to improve the rules
- **Control:** dispatcher has the final say; rule priorities decide which rule fires first
- **Boundary:** the dispatch decision in the control room (driving and treatment are outside)
- **Environment:** hospitals, traffic police, weather, patients' families, the 108 service
- **Interfaces:** call-taking screen, hospital bed status board, map, feedback log
""")
with col2:
    st.subheader("Types of decisions")
    st.markdown("""
- **Structured:** choosing a hospital when the emergency type is clear and a suitable hospital has beds. The rules decide.
- **Semi-structured:** a critical patient whose best hospital is far away. The system suggests stabilising at the nearest ICU first, the dispatcher judges.
- **Unstructured:** no hospital meets all needs, or planning where a new trauma centre is needed. The system only gives information; people decide.
""")
    st.subheader("Course concepts shown")
    st.markdown("""
Knowledge base separate from inference engine · production rules · forward chaining ·
conflict resolution by priority · explanation facility (How / Why) · what-if analysis ·
human-in-the-loop · feedback learning · evaluation against a baseline · ethics and limitations
""")
st.info("Prototype: hospital names and figures are simulated for demonstration. Area locations in Gwalior are approximate.")
