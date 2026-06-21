import streamlit as st
import pandas as pd
import altair as alt


def render_analytics():
    st.markdown("<div class='card'><h2>Analytics</h2></div>", unsafe_allow_html=True)

    # demo KPIs
    total = 42
    applied = 20
    shortlisted = 8
    interview = 9
    offers = 2
    rejected = 3

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total", total)
    c2.metric("Applied", applied)
    c3.metric("Shortlisted", shortlisted)
    c4.metric("Interview", interview)
    c5.metric("Offers", offers)
    c6.metric("Rejected", rejected)

    # sample bar chart
    data = pd.DataFrame({
        "month": ["Jan", "Feb", "Mar", "Apr", "May"],
        "applications": [5, 8, 12, 9, 15]
    })
    chart = alt.Chart(data).mark_bar().encode(x="month", y="applications", color=alt.value("#7C5CFF"))
    st.altair_chart(chart, use_container_width=True)

    # pie-like distribution (donut simulated)
    dist = pd.DataFrame({"status": ["Applied", "Interview", "Offer", "Rejected"], "count": [20, 9, 2, 3]})
    pie = alt.Chart(dist).mark_arc(innerRadius=50).encode(theta=alt.Theta(field="count", type="quantitative"), color=alt.Color(field="status", type="nominal", scale=alt.Scale(range=["#7C5CFF", "#00E5A8", "#3CE27A", "#FF6B6B"])))
    st.altair_chart(pie, use_container_width=True)
