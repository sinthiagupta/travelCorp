import streamlit as st
import pandas as pd
from database import get_all_invoices, get_all_logs
from agent_graph import run_automated_agent
import time

# 1. Page Config
st.set_page_config(page_title="TravelCorp Finance Agent", page_icon="💰", layout="wide", initial_sidebar_state="expanded")

# 2. Premium Styling (TravelCorp Theme)
st.markdown("""
    <style>
    /* Main Background */
    .main { background-color: #0e1117; }
    
    /* Metric Card Styling */
    [data-testid="stMetricValue"] {
        font-size: 32px;
        color: #00d4ff;
    }
    .stMetric {
        background-color: #1a1c24;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        border: 1px solid #30333d;
    }
    
    /* Table Styling */
    .stDataFrame {
        border: 1px solid #30333d;
        border-radius: 8px;
    }
    
    /* Header Hide */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 3. Sidebar Header
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/airplane-take-off.png") # Travel Icon
    st.title("TravelCorp")
    st.markdown("---")
    if st.button("🚀 Run Automation Now", use_container_width=True):
        with st.spinner("AI is processing..."):
            run_automated_agent()
            st.success("Work Complete!")
            time.sleep(1)
            st.rerun()

# 4. Header Section
st.title("💰 Finance Credit Follow-up Agent")
st.markdown("##### Real-time Invoice Management & AI Auditing System")

# Fetch data
invoices = get_all_invoices()
logs = get_all_logs()

# 5. Metrics Section
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Pending Invoices", len(invoices))
with m2:
    st.metric("Total Follow-ups", len(logs))
with m3:
    escalated = sum(1 for l in logs if l.status == "ESCALATED")
    st.metric("Legal Escalations", escalated)
with m4:
    st.metric("System Health", "Active 🟢")

st.markdown("---")

# 6. Data Layout
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("📋 Pending Invoices")
    df_inv = pd.DataFrame([{
        "ID": i.invoice_id, 
        "Client": i.client_name, 
        "Amount": f"${i.amount:,.2f}",
        "Due": i.due_date
    } for i in invoices])
    st.dataframe(df_inv, use_container_width=True, hide_index=True)

with right_col:
    st.subheader("📜 Recent Audit Logs")
    df_logs = pd.DataFrame([{
        "Time": l.timestamp, 
        "Inv": l.invoice_id, 
        "Tone": l.tone_used, 
        "Status": l.status
    } for l in logs])
    st.dataframe(df_logs, use_container_width=True, hide_index=True)

# 7. Interactive Email Viewer
st.markdown("---")
st.subheader("✉️ AI Communication Archive")

if logs:
    log_options = {f"{l.timestamp} - {l.invoice_id} ({l.tone_used})": l for l in logs}
    choice = st.selectbox("Select a sent follow-up to review:", list(log_options.keys()))
    
    selected_log = log_options[choice]
    
    if selected_log.email_content:
        with st.container():
            st.markdown(f"**Tone Analysis:** `{selected_log.tone_used}` | **Status:** `{selected_log.status}`")
            st.text_area("Final Draft Sent to Client:", selected_log.email_content, height=500)
    else:
        st.warning("⚠️ No email content generated. This invoice was escalated directly to the Legal Department.")
else:
    st.info("No audit logs found. Run the agent to generate data.")
