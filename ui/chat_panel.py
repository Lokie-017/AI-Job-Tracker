
import streamlit as st
import time
from mcp_integration.mcp_client import MCPClient
from mcp_integration.ollama_client import OllamaClient


def _ensure_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "agent_log" not in st.session_state:
        st.session_state.agent_log = []
    if "mcp_client" not in st.session_state:
        st.session_state.mcp_client = MCPClient()
    if "ollama_client" not in st.session_state:
        st.session_state.ollama_client = OllamaClient()


def _render_message(msg):
    role = msg.get("role")
    text = msg.get("text")
    if role == "user":
        col1, col2 = st.columns([1, 7])
        with col2:
            st.markdown(f"<div class='chat-user'>{text}</div>", unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([7, 1])
        with col1:
            st.markdown(f"<div class='chat-ai'>{text}</div>", unsafe_allow_html=True)


def _render_tool_step(step):
    tool = step.get("tool")
    status = step.get("status", "idle")
    args = step.get("args", {})
    icon = "🔄" if status == "running" else ("✅" if status == "done" else "•")
    st.markdown(f"<div class='tool-step'><div class='label'><strong>{icon} {tool}</strong><div class='muted' style='font-size:12px'>{args}</div></div><div class='status'>{status}</div></div>", unsafe_allow_html=True)


def render_chat():
    _ensure_state()
    st.markdown("<div class='card'><h2>AI Assistant</h2></div>", unsafe_allow_html=True)

    # messages
    for msg in st.session_state.messages:
        _render_message(msg)

    # Chat input
    cols = st.columns([1, 6, 1])
    with cols[1]:
        _ = st.text_input("", key="chat_input", placeholder="Ask the agent or type a command...", label_visibility='collapsed')
        send = st.button("Send")

    if send and st.session_state.get("chat_input"):
        user_text = st.session_state.chat_input.strip()
        if not user_text:
            return

        st.session_state.messages.append({"role": "user", "text": user_text})
        # add assistant placeholder
        assistant_idx = len(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "text": "Agent thinking... <span class='typing-dots'><span></span><span></span><span></span></span>", "meta": {"typing": True}})

        st.session_state.agent_log.append({"event": "planning", "detail": f"Planning for: {user_text}", "ts": time.time()})

        # planning
        plan = st.session_state.ollama_client.plan(user_text)
        time.sleep(0.25)

        if not plan:
            # update assistant message
            st.session_state.messages[-1] = {"role": "assistant", "text": "I couldn't plan any tool steps for that request."}
            st.session_state.chat_input = ""
            st.experimental_rerun()

        # execute plan
        tool_steps = []
        for step in plan:
            tool_steps.append({"tool": step.get("tool"), "args": step.get("arguments", {}), "status": "running"})
            st.session_state.agent_log.append({"event": "thought", "thought": step.get("thought", "")})

            # perform call
            try:
                result = st.session_state.mcp_client.call_tool(step.get("tool"), step.get("arguments", {}))
                st.session_state.agent_log.append({"event": "result", "tool": step.get("tool"), "result": result, "ts": time.time()})
                tool_steps[-1]["status"] = "done"
            except Exception as exc:
                st.session_state.agent_log.append({"event": "error", "tool": step.get("tool"), "error": str(exc), "ts": time.time()})
                tool_steps[-1]["status"] = "error"

            # small pause to simulate streaming updates
            time.sleep(0.18)

        # update assistant final message summarizing steps
        summary_lines = []
        for s in tool_steps:
            summary_lines.append(f"{s['tool']}: {s['status']}")
        final_text = "\n".join(summary_lines)
        st.session_state.messages[-1] = {"role": "assistant", "text": f"Plan executed:\n{final_text}"}
        st.session_state.chat_input = ""
        st.experimental_rerun()

    st.markdown("---")
    # Observability quick log
    with st.expander("Agent Observability (quick)"):
        for item in st.session_state.agent_log[-20:][::-1]:
            if item.get("event") == "result":
                st.json(item)
            else:
                st.write(item)
