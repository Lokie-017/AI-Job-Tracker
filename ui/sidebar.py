
import streamlit as st
from pathlib import Path


def render_sidebar():
  logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.svg"
  col1, col2 = st.columns([1, 6])
  with col1:
    if logo_path.exists():
      st.image(str(logo_path), width=48, use_column_width=False)
    else:
      st.markdown("<div class='logo' style='background:linear-gradient(135deg,#7C5CFF,#4D68FF)'></div>", unsafe_allow_html=True)
  with col2:
    st.markdown("<div style='margin-top:6px'> <strong>AI Job Tracker Agent</strong><div class='muted' style='font-size:12px'>Assistant for job applications</div></div>", unsafe_allow_html=True)

  st.markdown("<hr style='border-color:rgba(255,255,255,0.04)' />", unsafe_allow_html=True)

  nav_items = ["AI Assistant", "Applications", "Analytics", "Follow Ups", "Observability", "Settings"]
  current = st.session_state.get("page", "AI Assistant")
  for item in nav_items:
    is_active = item == current
    if is_active:
      # render active item as styled markdown (non-clickable)
      st.markdown(f"<div style='padding:8px;border-radius:8px;margin-bottom:6px;background:rgba(124,92,255,0.08)'><strong>{item}</strong></div>", unsafe_allow_html=True)
    else:
      # render inactive items as buttons (plain text)
      if st.button(item, key=f"nav_{item}"):
        st.session_state.page = item

  st.markdown("<div class='muted' style='margin-top:12px;font-size:12px'>Tip: Use the assistant to run MCP tools or manage applications.</div>", unsafe_allow_html=True)
