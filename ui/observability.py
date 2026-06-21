import streamlit as st
import json


def render_observability():
    st.markdown("<div class='card'><h2>Agent Observability</h2></div>", unsafe_allow_html=True)

    if "agent_log" not in st.session_state:
        st.session_state.agent_log = []

    st.markdown("**Current Goal**")
    st.write(st.session_state.get("current_goal", "No active goal"))

    st.markdown("**Execution History**")
    for idx, evt in enumerate(st.session_state.agent_log[-50:][::-1]):
        with st.expander(f"Step {idx} - {evt.get('event','')}"):
            st.json(evt)
