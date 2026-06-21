import streamlit as st

from ui.sidebar import render_sidebar
from ui.chat_panel import render_chat
from ui.applications import render_applications
from ui.analytics import render_analytics
from ui.followups import render_followups
from ui.observability import render_observability
from ui.styles import THEME_CSS


st.set_page_config(page_title="AI Job Tracker Agent", layout="wide")

st.markdown(f"<style>{THEME_CSS}</style>", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "AI Assistant"


def main():
    with st.sidebar:
        render_sidebar()

    # Main layout: two columns (chat or dashboard content)
    st.header("")
    page = st.session_state.page

    if page == "AI Assistant":
        render_chat()
    elif page == "Applications":
        render_applications()
    elif page == "Analytics":
        render_analytics()
    elif page == "Follow Ups":
        render_followups()
    elif page == "Observability":
        render_observability()
    else:
        st.write("Page not implemented yet")


if __name__ == "__main__":
    main()
