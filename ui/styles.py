THEME_CSS = r'''
:root{
  --bg:#0B1020;
  --card:rgba(255,255,255,0.03);
  --muted:#9AA4BD;
  --text:#E6EEF8;
  --accent:#7C5CFF;
  --accent-2:#00E5A8;
  --glass-border: rgba(255,255,255,0.06);
  --radius: 12px;
}
html, body, [class*="st-"] {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
}
.stApp {
  padding-top: 16px;
}
.card {
  background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
  border: 1px solid var(--glass-border);
  border-radius: var(--radius);
  padding: 18px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.6);
}
.sidebar .block-container {
  background: transparent !important;
}
.logo {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  margin-bottom: 8px;
}
.chat-user {
  background: rgba(255,255,255,0.03);
  color: var(--text);
  padding: 12px 16px;
  border-radius: 14px;
  display: inline-block;
  max-width: 78%;
  margin: 8px 0;
}
.chat-ai {
  background: linear-gradient(135deg, var(--accent), #4D68FF);
  color: white;
  padding: 12px 16px;
  border-radius: 14px;
  display: inline-block;
  max-width: 78%;
  margin: 8px 0;
}
.muted { color: var(--muted); }
.kpi-card { padding:12px; border-radius:10px; background: rgba(255,255,255,0.02); }
.tool-step { padding:10px; border-radius:10px; margin-top:8px; background: rgba(255,255,255,0.02); display:flex; align-items:center; gap:10px; }
.tool-step .label { flex:1 }
.tool-step .status { min-width:72px; text-align:right }
.typing { font-style: italic; opacity:0.95 }

/* typing dots */
.typing-dots { display:inline-block; vertical-align:middle }
.typing-dots span { display:inline-block; width:6px; height:6px; margin:0 2px; background:#fff; border-radius:50%; opacity:0.35; animation: typing 1s infinite; }
.typing-dots span:nth-child(2) { animation-delay: 0.15s }
.typing-dots span:nth-child(3) { animation-delay: 0.3s }
@keyframes typing { 0% { transform: translateY(0); opacity:0.35 } 50% { transform: translateY(-6px); opacity:1 } 100% { transform: translateY(0); opacity:0.35 } }

/* spinner */
.spinner { border: 3px solid rgba(255,255,255,0.08); border-top:3px solid rgba(255,255,255,0.35); border-radius:50%; width:18px; height:18px; animation: spin 1s linear infinite }
@keyframes spin { to { transform: rotate(360deg) } }

/* layout utils */
.row { display:flex; gap:12px; align-items:center }
.col { flex:1 }

/* small responsive tweaks */
@media (max-width: 800px) {
  .chat-user, .chat-ai { max-width: 92%; }
}
'''
