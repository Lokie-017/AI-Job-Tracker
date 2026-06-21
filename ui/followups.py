import streamlit as st


def render_followups():
    st.markdown("<div class='card'><h2>Follow Ups</h2></div>", unsafe_allow_html=True)

    items = [
        {"company": "OpenAI", "type": "Follow-up", "due": "2026-06-25", "urgent": True},
        {"company": "Vercel", "type": "Interview", "due": "2026-06-29", "urgent": False},
        {"company": "Notion", "type": "Follow-up", "due": "2026-07-02", "urgent": False},
    ]

    for it in items:
        badge = "🔴" if it["urgent"] else "🟡"
        st.markdown(f"**{badge} {it['company']}** — {it['type']} — due {it['due']}")

    st.markdown("---")
    st.write("Highlight urgent items and allow quick actions (snooze/done).")
