# Golden-Hour: Emergency Hospital Dispatch Advisor

A rule-based **Decision Support Expert System** that helps a 108 ambulance dispatcher in Gwalior choose the right hospital for a patient, not just the nearest one.

Course project for *Decision Support and Expert Systems*, M.S. AI & Data Science, ABV-IIITM Gwalior.
Author: S. Hemanth Chandra (2025MS_020).

## What it does
- Works out what the patient needs (CT scan, cath lab, burn unit, ICU...) from the call details using **IF-THEN production rules**
- Uses a **forward-chaining inference engine** with conflict resolution (priority + refraction)
- Rejects hospitals that lack a facility, have no free bed, are closed at night or on diversion
- Ranks the rest by expected time to care = travel time + waiting time
- Explains every decision (**How / Why**), supports **what-if analysis**, and logs dispatcher **overrides** as feedback

## Pages
System Overview · Dispatch Advisor · Explanation · What-if Simulator · Knowledge Base · Hospital Status · Feedback Log · Evaluation

## Project structure
```
app.py                     navigation
common.py                  shared state, input form
engine.py                  inference engine (no domain knowledge inside)
knowledge_base/rules.json  26 production rules
knowledge_base/facilities.json
data/hospitals.csv         10 simulated hospitals
data/areas.csv             12 Gwalior areas (approximate locations)
data/scenarios.csv         20 test calls for evaluation
pages/                     one file per page
```

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Push this folder to a public GitHub repository.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **Create app**, choose the repository, branch `main` and main file `app.py`, then **Deploy**.

## Note
Hospital names, facilities and figures are simulated for demonstration. This prototype does not diagnose or treat patients; the final decision always rests with the dispatcher.
