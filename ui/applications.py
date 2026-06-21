import streamlit as st
import pandas as pd
from datetime import datetime


def _seed_data():
    return [
        {"ID": 1, "Company": "OpenAI", "Role": "Research Engineer", "Status": "Applied", "Applied Date": "2026-05-01", "Notes": "Referred"},
        {"ID": 2, "Company": "Vercel", "Role": "Frontend Engineer", "Status": "Interview", "Applied Date": "2026-05-10", "Notes": "Screening"},
        {"ID": 3, "Company": "Notion", "Role": "Product Designer", "Status": "Shortlisted", "Applied Date": "2026-04-21", "Notes": "Portfolio review"},
    ]


def render_applications():
    if "applications" not in st.session_state:
        st.session_state.applications = _seed_data()

    st.markdown("<div class='card'><h2>Applications</h2></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([4, 2, 1])
    with col1:
        q = st.text_input("Search", key="app_search")
    with col2:
        status = st.selectbox("Filter by status", options=["All", "Applied", "Shortlisted", "Interview", "Offer", "Rejected"], index=0)
    with col3:
        if st.button("Add"):
            # simple add demo
            apps = st.session_state.applications
            new_id = max([a["ID"] for a in apps]) + 1
            apps.append({"ID": new_id, "Company": "NewCo", "Role": "Role", "Status": "Applied", "Applied Date": datetime.utcnow().date().isoformat(), "Notes": ""})
            st.session_state.applications = apps

    df = pd.DataFrame(st.session_state.applications)
    if q:
        df = df[df["Company"].str.contains(q, case=False) | df["Role"].str.contains(q, case=False) | df["Notes"].str.contains(q, case=False)]
    if status != "All":
        df = df[df["Status"] == status]

    st.dataframe(df.sort_values(by="Applied Date", ascending=False))

    st.markdown("---")
    st.write("Select an application to edit or delete")
    ids = df["ID"].tolist()
    if ids:
        sel = st.selectbox("Application", options=ids)
        app = next((a for a in st.session_state.applications if a["ID"] == sel), None)
        if app:
            with st.form("edit_app"):
                company = st.text_input("Company", value=app["Company"])
                role = st.text_input("Role", value=app["Role"])
                status_val = st.selectbox("Status", options=["Applied", "Shortlisted", "Interview", "Offer", "Rejected"], index=["Applied", "Shortlisted", "Interview", "Offer", "Rejected"].index(app["Status"]) if app["Status"] in ["Applied", "Shortlisted", "Interview", "Offer", "Rejected"] else 0)
                notes = st.text_area("Notes", value=app.get("Notes", ""))
                submitted = st.form_submit_button("Save")
                if submitted:
                    app.update({"Company": company, "Role": role, "Status": status_val, "Notes": notes})
                    st.session_state.applications = st.session_state.applications
                    st.success("Saved")
            if st.button("Delete"):
                st.session_state.applications = [a for a in st.session_state.applications if a["ID"] != sel]
                st.success("Deleted")
