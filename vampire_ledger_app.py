import streamlit as st
import requests
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import uuid
import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="The Vampire's Ledger - Forensic Command Center",
    page_icon="🧛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #E63946;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #8D99AE;
        margin-bottom: 25px;
    }
    .metric-card {
        background-color: #1E1E2E;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #E63946;
    }
    .badge-approve {
        background-color: #2A9D8F;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: bold;
    }
    .badge-challenge {
        background-color: #E9C46A;
        color: black;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: bold;
    }
    .badge-block {
        background-color: #E63946;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar Configuration ---
st.sidebar.title("🧛 Vampire's Ledger")
st.sidebar.markdown("**Real-Time Anti-Mule & AML Engine**")
st.sidebar.divider()

backend_url = st.sidebar.text_input("Backend API Base URL", value="http://localhost:8000")

st.sidebar.subheader("Engine Status")
try:
    health_resp = requests.get(f"{backend_url}/api/audits/recent", timeout=2)
    if health_resp.status_code == 200:
        st.sidebar.success("🟢 API Connected")
    else:
        st.sidebar.warning(f"🟡 API Returned Status {health_resp.status_code}")
except Exception:
    st.sidebar.error("🔴 API Offline / Unreachable")

st.sidebar.divider()
st.sidebar.info("💡 **Hackathon Demo Tip:** Use the *Attack Simulator* tab to trigger real-time circular laundering loops and mule fan-in siphons.")

# --- Header ---
st.markdown("<p class='main-header'>🧛 The Vampire's Ledger</p>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Real-Time Graph-Based Fraud Detection & Forensic Command Center</p>", unsafe_allow_html=True)

# --- Tabs Navigation ---
tab_process, tab_topology, tab_audits, tab_simulator = st.tabs([
    "💳 Process Transaction", 
    "🕸️ Fraud Topology Graph", 
    "📋 Audit Logs", 
    "🚀 Attack Simulator"
])

# ==========================================
# TAB 1: PROCESS TRANSACTION
# ==========================================
with tab_process:
    st.subheader("Evaluate Single Payment")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("##### Input Transaction Details")
        with st.form("tx_form"):
            tx_id = st.text_input("Transaction ID", value=f"TX_{uuid.uuid4().hex[:6].upper()}")
            sender_id = st.text_input("Sender Account ID", value="ACC_VAMP_01")
            receiver_id = st.text_input("Receiver Account ID", value="ACC_VAMP_02")
            amount = st.number_input("Amount ($)", min_value=0.01, value=500.00, step=10.00)
            device_id = st.text_input("Device ID", value="DEV_ST_01")
            
            submit_btn = st.form_submit_button("⚡ Evaluate Transaction Risk")
            
    with col2:
        st.markdown("##### Risk Evaluation Result")
        if submit_btn:
            payload = {
                "tx_id": tx_id,
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "amount": amount,
                "device_id": device_id
            }
            try:
                res = requests.post(f"{backend_url}/api/transactions/process", json=payload, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    decision = data.get("decision")
                    score = data.get("risk_score", 0.0)
                    signals = data.get("trigger_signals", [])
                    
                    # Display Decision Badge
                    if decision == "BLOCK_AND_REPORT":
                        st.error(f"🚨 **DECISION: BLOCK & REPORT** (Score: {score:.2f})")
                    elif decision == "CHALLENGE_STEP_UP":
                        st.warning(f"⚠️ **DECISION: CHALLENGE / STEP-UP 2FA** (Score: {score:.2f})")
                    else:
                        st.success(f"✅ **DECISION: APPROVED** (Score: {score:.2f})")
                    
                    st.progress(float(score))
                    
                    st.markdown("**Triggered Risk Signals:**")
                    if signals:
                        for s in signals:
                            st.markdown(f"- 🚩 `{s}`")
                    else:
                        st.info("No risk rules triggered. Clean baseline transfer.")
                else:
                    st.error(f"Error from API: {res.text}")
            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")
        else:
            st.info("Fill out the transaction form and click 'Evaluate Transaction Risk' to see real-time analysis.")

# ==========================================
# TAB 2: FRAUD TOPOLOGY GRAPH
# ==========================================
with tab_topology:
    st.subheader("Real-Time Network Topology")
    st.caption("Visualizes directional payment edges. Suspicious transfers flagged by the engine are highlighted in red.")
    
    if st.button("🔄 Refresh Graph Network"):
        st.rerun()
        
    try:
        graph_resp = requests.get(f"{backend_url}/api/graph/topology", timeout=5)
        if graph_resp.status_code == 200:
            graph_data = graph_resp.json()
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])
            
            if nodes and edges:
                G = nx.DiGraph()
                for node in nodes:
                    G.add_node(node["id"], label=node["label"])
                
                suspicious_edges = []
                normal_edges = []
                
                for edge in edges:
                    u, v = edge["source"], edge["target"]
                    amt = edge["amount"]
                    is_susp = edge["is_suspicious"]
                    G.add_edge(u, v, amount=amt, suspicious=is_susp)
                    if is_susp:
                        suspicious_edges.append((u, v))
                    else:
                        normal_edges.append((u, v))
                
                fig, ax = plt.subplots(figsize=(10, 6))
                fig.patch.set_facecolor('#0E1117')
                ax.set_facecolor('#0E1117')
                
                pos = nx.spring_layout(G, seed=42, k=0.8)
                
                # Draw nodes
                nx.draw_networkx_nodes(G, pos, node_size=1200, node_color="#457B9D", ax=ax)
                nx.draw_networkx_labels(G, pos, font_color="white", font_size=9, font_weight="bold", ax=ax)
                
                # Draw normal edges
                nx.draw_networkx_edges(G, pos, edgelist=normal_edges, edge_color="#2A9D8F", width=1.8, arrows=True, arrowsize=15, ax=ax)
                
                # Draw suspicious edges
                nx.draw_networkx_edges(G, pos, edgelist=suspicious_edges, edge_color="#E63946", width=2.8, style="dashed", arrows=True, arrowsize=20, ax=ax)
                
                ax.axis('off')
                st.pyplot(fig)
                plt.close(fig)
                
                # Metrics summary
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Active Entities (Nodes)", len(nodes))
                col_m2.metric("Total Transactions (Edges)", len(edges))
                col_m3.metric("Suspicious Edges Flagged", len(suspicious_edges))
            else:
                st.warning("No network data found in database yet. Process some transactions first!")
        else:
            st.error("Failed to fetch topology graph from API.")
    except Exception as e:
        st.error(f"Error loading topology graph: {e}")

# ==========================================
# TAB 3: AUDIT LOGS
# ==========================================
with tab_audits:
    st.subheader("Forensic Risk Audits")
    st.caption("Chronological audit log showing risk scores, decisions, and rule signals.")
    
    try:
        audits_resp = requests.get(f"{backend_url}/api/audits/recent", timeout=5)
        if audits_resp.status_code == 200:
            audits_list = audits_resp.json()
            if audits_list:
                df = pd.DataFrame(audits_list)
                
                # Format table
                st.dataframe(
                    df,
                    column_config={
                        "tx_id": "Tx ID",
                        "sender": "Sender ID",
                        "receiver": "Receiver ID",
                        "amount": st.column_config.NumberColumn("Amount ($)", format="$%.2f"),
                        "risk_score": st.column_config.ProgressColumn("Risk Score", min_value=0.0, max_value=1.0, format="%.2f"),
                        "decision": "Decision",
                        "signals": "Trigger Signals",
                        "timestamp": "Timestamp"
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No audit logs available.")
        else:
            st.error("Failed to fetch audit records.")
    except Exception as e:
        st.error(f"Error fetching audit records: {e}")

# ==========================================
# TAB 4: ATTACK SIMULATOR
# ==========================================
with tab_simulator:
    st.subheader("🚀 Live Fraud Attack Simulator")
    st.markdown("Execute automated attack sequences to demonstrate the detection engine in real time during hackathon judging.")
    
    col_sim1, col_sim2 = st.columns(2)
    
    with col_sim1:
        st.markdown("#### Scenario A: Circular Laundering Loop")
        st.caption("Executes `ACC_LOOP_A -> ACC_LOOP_B -> ACC_LOOP_C -> ACC_LOOP_A` to trigger `nx.simple_cycles` (+0.55 penalty).")
        if st.button("🔥 Inject Circular Laundering Ring"):
            seq = [
                ("TX_LOOP_1", "ACC_LOOP_A", "ACC_LOOP_B", 1200.0),
                ("TX_LOOP_2", "ACC_LOOP_B", "ACC_LOOP_C", 1150.0),
                ("TX_LOOP_3", "ACC_LOOP_C", "ACC_LOOP_A", 1100.0)
            ]
            for tx_i, s_i, r_i, amt_i in seq:
                p = {"tx_id": f"{tx_i}_{uuid.uuid4().hex[:4]}", "sender_id": s_i, "receiver_id": r_i, "amount": amt_i, "device_id": "DEV_SIM"}
                requests.post(f"{backend_url}/api/transactions/process", json=p)
            st.success("Inserted 3-step circular laundering loop! Check the Topology Graph & Audit Logs.")
            
    with col_sim2:
        st.markdown("#### Scenario B: Mule Siphon Aggregation Hub")
        st.caption("Sends funds from 3 distinct accounts to `ACC_MULE_HUB` to trigger `in_degree >= 3` (+0.30 penalty).")
        if st.button("🔥 Inject Mule Aggregation Siphon"):
            mule_target = "ACC_MULE_HUB"
            sources = ["ACC_SRC_01", "ACC_SRC_02", "ACC_SRC_03"]
            for idx, src in enumerate(sources):
                p = {"tx_id": f"TX_MULE_{idx}_{uuid.uuid4().hex[:4]}", "sender_id": src, "receiver_id": mule_target, "amount": 800.0, "device_id": "DEV_SIM"}
                requests.post(f"{backend_url}/api/transactions/process", json=p)
            st.success("Injected 3-source fan-in siphon to Mule Hub! Check the Topology Graph & Audit Logs.")
