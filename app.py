import numpy as np
import plotly.graph_objects as go
import streamlit as st

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Telecom Network Intelligence Platform | MCP Agent Flow",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Detect active Streamlit theme
theme_type = st.context.theme.type

if theme_type == "dark":
    noc_theme = """
    <style>
    :root {
        --noc-card-bg: #151d30;
        --noc-border: #2a3857;
        --noc-text: #f1f5f9;
        --noc-muted: #94a3b8;
        --noc-accent: #38bdf8;
        --noc-header-start: #0f172a;
        --noc-header-end: #1e293b;

        --noc-success: #34d399;
        --noc-success-bg: rgba(16,185,129,0.15);

        --noc-error: #f87171;
        --noc-error-bg: rgba(239,68,68,0.15);

        --noc-warning: #fbbf24;
        --noc-warning-bg: rgba(245,158,11,0.15);
    }

    .noc-header,
    .noc-card {
        color: var(--noc-text);
    }

    /* Header */
    .noc-header {
        background: linear-gradient(
            90deg,
            var(--noc-header-start),
            var(--noc-header-end)
        );
        border: 1.5px solid var(--noc-border);
        border-radius: 12px;
        padding: 20px 28px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }

    /* Cards */
    .noc-card {
        background-color: var(--noc-card-bg);
        border: 1px solid var(--noc-border);
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 16px;
    }

    .noc-card-title {
        font-size: 11px;
        font-weight: 700;
        color: var(--noc-muted);
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 6px;
    }

    .noc-card-value {
        font-size: 20px;
        font-weight: 800;
        color: var(--noc-accent);
    }

    /* Status badges */
    .badge-valid {
        background: var(--noc-success-bg);
        color: var(--noc-success);
        border: 1px solid var(--noc-success);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
    }

    .badge-incomplete {
        background: var(--noc-error-bg);
        color: var(--noc-error);
        border: 1px solid var(--noc-error);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
    }

    .badge-ghost {
        background: var(--noc-warning-bg);
        color: var(--noc-warning);
        border: 1px solid var(--noc-warning);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: var(--noc-card-bg);
        padding: 6px;
        border-radius: 8px;
        border: 1px solid var(--noc-border);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        color: var(--noc-text);
    }

    .stTabs [aria-selected="true"] {
        font-weight: 700;
    }
    </style>
    """
else:
    noc_theme = """
    <style>
    :root {
        --noc-card-bg: #ffffff;
        --noc-border: #cbd5e1;
        --noc-text: #1e293b;
        --noc-muted: #475569;
        --noc-accent: #0284c7;
        --noc-header-start: #f1f5f9;
        --noc-header-end: #e2e8f0;

        --noc-success: #047857;
        --noc-success-bg: #d1fae5;

        --noc-error: #b91c1c;
        --noc-error-bg: #fee2e2;

        --noc-warning: #b45309;
        --noc-warning-bg: #fef3c7;
    }

    .noc-header,
    .noc-card {
        color: var(--noc-text);
    }

    /* Header */
    .noc-header {
        background: linear-gradient(
            90deg,
            var(--noc-header-start),
            var(--noc-header-end)
        );
        border: 1.5px solid var(--noc-border);
        border-radius: 12px;
        padding: 20px 28px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }

    /* Cards */
    .noc-card {
        background-color: var(--noc-card-bg);
        border: 1px solid var(--noc-border);
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 16px;
    }

    .noc-card-title {
        font-size: 11px;
        font-weight: 700;
        color: var(--noc-muted);
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 6px;
    }

    .noc-card-value {
        font-size: 20px;
        font-weight: 800;
        color: var(--noc-accent);
    }

    /* Status badges */
    .badge-valid {
        background: var(--noc-success-bg);
        color: var(--noc-success);
        border: 1px solid var(--noc-success);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
    }

    .badge-incomplete {
        background: var(--noc-error-bg);
        color: var(--noc-error);
        border: 1px solid var(--noc-error);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
    }

    .badge-ghost {
        background: var(--noc-warning-bg);
        color: var(--noc-warning);
        border: 1px solid var(--noc-warning);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: var(--noc-card-bg);
        padding: 6px;
        border-radius: 8px;
        border: 1px solid var(--noc-border);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        color: var(--noc-text);
    }

    .stTabs [aria-selected="true"] {
        font-weight: 700;
    }
    </style>
    """

st.markdown(noc_theme, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# INITIALIZE STATE
# -----------------------------------------------------------------------------
if "approved" not in st.session_state:
    st.session_state.approved = False

# Detect Streamlit theme background for Plotly chart sync
is_dark = st.get_option("theme.base") == "dark"
plotly_text_color = "#f8fafc" if is_dark else "#1e293b"
plotly_grid_color = "#334155" if is_dark else "#cbd5e1"

# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS & GOVERNANCE
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/isometric-line/100/38bdf8/network.png", width=64)
    st.title("Control & Scope")
    st.caption("Role-Based Access & Simulation Control")

    st.markdown("---")

    # Customer Context
    customer = st.selectbox(
        "🏢 Customer Scope (Tenant)",
        [
            "cust_alpha (Customer Alpha)",
            "cust_beta (Customer Beta)",
            "cust_gamma (Customer Gamma)",
        ],
        index=0,
    )
    tenant_id = customer.split()[0]

    # Agent Role Selection
    agent_role = st.selectbox(
        "👤 Active Agent Role",
        ["Alarm Management", "Performance Analysis", "Change Planning"],
        index=0,
    )

    st.markdown("---")
    st.subheader("⚙️ Incident Simulation")

    selected_alarm = st.selectbox(
        "Select Trigger Alarm",
        [
            "ALT-9042: Cell Availability Degradation (10:05 UTC)",
            "ALT-8812: Transport Interface Down (09:45 UTC)",
            "ALT-7719: High Retransmission Rate (08:30 UTC)",
        ],
    )

    topology_depth = st.slider("Topology Hop Depth", min_value=1, max_value=3, value=2)

    # Bitemporal Time Slider
    time_offset = st.select_slider(
        "Effective Query Time Window",
        options=[
            "09:30 UTC",
            "09:45 UTC",
            "10:00 UTC",
            "10:05 UTC (Incident)",
            "10:15 UTC",
            "11:00 UTC (Batch Sync)",
        ],
        value="10:05 UTC (Incident)",
        help="Simulates Bitemporal Time Travel: queries how the network was connected at that exact moment versus when data arrived in the database.",
    )

    st.markdown("---")
    st.info(
        f"**RBAC Enforcement:**\nRole `{agent_role}` bound to JWT claims for tenant `{tenant_id}`."
    )

# -----------------------------------------------------------------------------
# TOP HEADER
# -----------------------------------------------------------------------------
st.markdown(
    f"""
<div class="noc-header" style="background-color: white;">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h1 style="margin:0; font-size:24px; font-weight:800; letter-spacing:-0.5px;">
                Telecom Network Intelligence Platform
            </h1>
            <p style="margin:4px 0 0 0; font-size:13px; color:var(--card-text-muted);">
                Autonomous Multi-Tenant Telemetry, Bitemporal Topology & Role-Based MCP Agent Operations
            </p>
        </div>
        <div style="text-align:right;">
            <span class="badge-valid">SYSTEM ONLINE</span>
            <p style="margin:6px 0 0 0; font-size:11px; font-family:monospace; color:var(--card-text-muted);">SLA: &lt;2s (p95 Graph) | Tenant: {tenant_id}</p>
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# TRIGGER & BITEMPORAL CONTEXT CARDS
# -----------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        """
    <div class="noc-card">
        <div class="noc-card-title">Triggering Alarm</div>
        <div class="noc-card-value" style="color:#ef4444;">ALT-9042</div>
        <div style="font-size:12px; color:var(--card-text-muted); margin-top:4px;">Cell Availability Fault</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
    <div class="noc-card">
        <div class="noc-card-title">Effective Time (Event)</div>
        <div class="noc-card-value">{time_offset.split()[0]}</div>
        <div style="font-size:12px; color:var(--card-text-muted); margin-top:4px;">Incident Timestamp</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
    <div class="noc-card">
        <div class="noc-card-title">Ingestion Time (DB)</div>
        <div class="noc-card-value" style="color:#d97706;">11:00:00 UTC</div>
        <div style="font-size:12px; color:var(--card-text-muted); margin-top:4px;">Hourly Batch Dump Sync</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        """
    <div class="noc-card">
        <div class="noc-card-title">Topology State</div>
        <div class="noc-card-value" style="color:#059669;">Bitemporal Snapshot</div>
        <div style="font-size:12px; color:var(--card-text-muted); margin-top:4px;">Ghost Entity Handled</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# EXECUTION TABS
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🌐 Step 1: Bounded Topology Graph",
        "📊 Step 2: KPI Evidence Window",
        "🛠️ Step 3: MCP Tool Call Log",
        "🤖 Step 4: AI Agent Reasoning & Action",
    ]
)

# -----------------------------------------------------------------------------
# TAB 1: BOUNDED TOPOLOGY GRAPH
# -----------------------------------------------------------------------------
with tab1:
    st.subheader("Bounded 2-Hop Dependency Topology")
    st.caption(
        f"Historical network state reconstructed at Effective Time: {time_offset}. Displays target cells, shared transport, and stubbed un-indexed nodes."
    )

    edge_x = []
    edge_y = []

    nodes = {
        "Cell_A": {
            "pos": (0, 2),
            "type": "Cell",
            "status": "Degraded",
            "color": "#ef4444",
            "size": 32,
        },
        "Cell_B": {
            "pos": (1, 2),
            "type": "Cell",
            "status": "Degraded",
            "color": "#ef4444",
            "size": 32,
        },
        "Cell_C": {
            "pos": (2, 2),
            "type": "Cell",
            "status": "Normal",
            "color": "#10b981",
            "size": 28,
        },
        "Site_Router_R101": {
            "pos": (1, 1),
            "type": "Transport Router",
            "status": "Warning",
            "color": "#f59e0b",
            "size": 38,
        },
        "Backhaul_Fiber_L1": {
            "pos": (1, 0),
            "type": "Fiber Link",
            "status": "Normal",
            "color": "#0284c7",
            "size": 26,
        },
        "Ghost_Node_X": {
            "pos": (2.5, 0.8),
            "type": "Unresolved Stub",
            "status": "Ghost Node",
            "color": "#64748b",
            "size": 22,
        },
    }

    edges = [
        ("Cell_A", "Site_Router_R101"),
        ("Cell_B", "Site_Router_R101"),
        ("Cell_C", "Site_Router_R101"),
        ("Site_Router_R101", "Backhaul_Fiber_L1"),
        ("Site_Router_R101", "Ghost_Node_X"),
    ]

    for edge in edges:
        x0, y0 = nodes[edge[0]]["pos"]
        x1, y1 = nodes[edge[1]]["pos"]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line={"width": 2, "color": plotly_grid_color},
        hoverinfo="none",
        mode="lines",
    )

    node_trace = go.Scatter(
        x=[nodes[n]["pos"][0] for n in nodes],
        y=[nodes[n]["pos"][1] for n in nodes],
        mode="markers+text",
        hoverinfo="text",
        text=[n for n in nodes],
        textposition="top center",
        textfont={"color": plotly_text_color, "size": 11},
        hovertext=[
            f"<b>{n}</b><br>Type: {nodes[n]['type']}<br>Status: {nodes[n]['status']}"
            for n in nodes
        ],
        marker={
            "color": [nodes[n]["color"] for n in nodes],
            "size": [nodes[n]["size"] for n in nodes],
            "line": {"width": 2, "color": plotly_grid_color},
        },
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode="closest",
            margin={"b": 20, "l": 20, "r": 20, "t": 20},
            xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
            yaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=360,
        ),
    )

    col_graph, col_info = st.columns([2, 1])
    with col_graph:
        st.plotly_chart(fig, width="stretch")

    with col_info:
        st.markdown("#### Entity Dependency Insights")
        st.markdown("""
        * **Affected Entities:** `Cell_A`, `Cell_B`
        * **Shared Infrastructure:** Both degraded cells map directly to `Site_Router_R101`.
        * **Unresolved Ghost Nodes:** `Ghost_Node_X` flagged (`unresolved=true`). Inventory dump arrived late at 11:00 UTC.
        * **Graph Traversal SLA:** Executed in **1.42s** (p95 SLA &lt; 2.0s target).
        """)
        st.markdown(
            '<span class="badge-ghost">UNRESOLVED ENTITY ISOLATED</span>',
            unsafe_allow_html=True,
        )

# -----------------------------------------------------------------------------
# TAB 2: KPI EVIDENCE WINDOW
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("15-Minute Tumbling Window KPI Counters")
    st.caption("Inspecting performance indicators before and during incident window.")

    timestamps = ["09:00", "09:15", "09:30", "09:45", "10:00", "10:05 (Event)", "10:15"]
    cell_a_availability = [99.9, 99.8, 99.9, 99.7, 98.2, 42.1, 40.5]
    cell_b_availability = [99.8, 99.9, 99.7, 99.8, 97.9, 45.0, 41.2]
    transport_kpi = [99.9, 99.9, 99.8, 99.9, np.nan, np.nan, np.nan]

    kpi_fig = go.Figure()
    kpi_fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=cell_a_availability,
            mode="lines+markers",
            name="Cell_A Availability (%)",
            line={"color": "#ef4444", "width": 3},
        )
    )
    kpi_fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=cell_b_availability,
            mode="lines+markers",
            name="Cell_B Availability (%)",
            line={"color": "#d97706", "width": 3},
        )
    )
    kpi_fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=transport_kpi,
            mode="lines+markers",
            name="Site_Router_R101 Telemetry",
            line={"color": "#64748b", "width": 2, "dash": "dash"},
        )
    )

    kpi_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": plotly_text_color},
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        xaxis={"gridcolor": plotly_grid_color},
        yaxis={"gridcolor": plotly_grid_color, "title": "Availability / Throughput %"},
        height=320,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    )

    st.plotly_chart(kpi_fig, width="stretch")

    col_q1, col_q2, col_q3 = st.columns(3)
    with col_q1:
        st.markdown(
            """
        <div class="noc-card">
            <div class="noc-card-title">Completeness Score</div>
            <div class="noc-card-value" style="color:#ef4444;">0.66 / 1.0</div>
            <div style="font-size:12px; color:var(--card-text-muted); margin-top:4px;">Transport Telemetry Missing</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col_q2:
        st.markdown(
            """
        <div class="noc-card">
            <div class="noc-card-title">KPI Data Status</div>
            <div style="margin-top:6px;"><span class="badge-incomplete">INCOMPLETE EVIDENCE</span></div>
            <div style="font-size:12px; color:var(--card-text-muted); margin-top:8px;">2 Counter Buckets Missing</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col_q3:
        st.markdown(
            """
        <div class="noc-card">
            <div class="noc-card-title">Late Data Reprocessing</div>
            <div class="noc-card-value" style="color:#0284c7; font-size:18px;">Micro-Batch Active</div>
            <div style="font-size:12px; color:var(--card-text-muted); margin-top:4px;">Window 10:00-10:15 Pending</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

# -----------------------------------------------------------------------------
# TAB 3: MCP TOOL CALL LOG
# -----------------------------------------------------------------------------
with tab3:
    st.subheader("Model Context Protocol (MCP) Tool Contract")
    st.caption(
        "Standardized JSON-RPC payload exchanged between LLM Agent and Domain Engine."
    )

    mcp_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "get_node_topology",
            "arguments": {
                "customer_id": tenant_id,
                "node_id": "cell_A",
                "depth": topology_depth,
                "timestamp": f"2026-11-10T{time_offset.split()[0][:5]}:00Z",
            },
        },
        "id": "req_091a_telco",
    }

    mcp_response = {
        "jsonrpc": "2.0",
        "result": {
            "identity": {
                "entity_id": "cell_A",
                "type": "cell",
                "customer_id": tenant_id,
            },
            "provenance": {
                "source": "connection_factory_inventory_sync",
                "retrieved_at": "2026-11-10T10:05:02Z",
                "topology_version_id": "topo_v20261110_1000",
            },
            "completeness": {
                "status": "INCOMPLETE",
                "completeness_score": 0.66,
                "missing_dependencies": ["Site_Router_R101:counter_stream"],
            },
            "data": {"nodes": list(nodes.keys()), "relationships": edges},
            "errors": [],
        },
        "id": "req_091a_telco",
    }

    col_req, col_res = st.columns(2)
    with col_req:
        st.markdown("**MCP Request Payload**")
        st.json(mcp_request)

    with col_res:
        st.markdown("**MCP Response Payload (with Evidence Metadata)**")
        st.json(mcp_response)

# -----------------------------------------------------------------------------
# TAB 4: AI AGENT REASONING & ACTION
# -----------------------------------------------------------------------------
with tab4:
    st.subheader("Explainable Agent Reasoning & Governance")
    st.caption(
        "Decomposed confidence scoring prevents hallucinated root causes when evidence is incomplete."
    )

    col_reasoning, col_action = st.columns([1.8, 1.2])

    with col_reasoning:
        st.markdown("#### Evidence Score Decomposition")

        scores = {
            "KPI Completeness": 0.30 * 0.66,
            "Topology Freshness": 0.25 * 1.0,
            "Temporal Alignment": 0.20 * 1.0,
            "Source Reliability": 0.15 * 0.90,
            "Independent Corroboration": 0.10 * 0.50,
        }
        total_score = sum(scores.values())

        for k, v in scores.items():
            st.write(f"**{k}**")
            st.progress(float(v))

        st.markdown(f"### Aggregate Evidence Score: `{total_score:.2f} / 1.0`")

        if total_score < 0.85:
            st.warning(
                "⚠️ **ADVISORY REVIEW TRIGGERED:** Confidence score is below target threshold (0.85). Critical transport telemetry counter is missing. Agent will NOT execute automated resolution."
            )
        else:
            st.success(
                "✅ Confidence threshold satisfied. High certainty root-cause established."
            )

    with col_action:
        st.markdown("#### Human-in-the-Loop Gate")
        st.markdown(f"**Current Role:** `{agent_role}`")

        if agent_role == "Alarm Management":
            st.info("Role Permission: **Propose Incident Ticket Update**")
            st.markdown("""
            **Proposed Recommendation:**
            > "Cells A & B degradation correlates to Site Router R101. Transport telemetry is delayed (completeness 0.66). Recommend dispatching field tech for R101 ping test; hold automated cell reset."
            """)

            if not st.session_state.approved:
                if st.button("🚀 Authorize & Dispatch Ticket Action", type="primary"):
                    st.session_state.approved = True
                    st.rerun()
            else:
                st.success(
                    "🎉 **Action Authorized by Human Operator!** Ticket #INC-9042 updated with audit trail."
                )
                if st.button("Reset Simulation"):
                    st.session_state.approved = False
                    st.rerun()

        elif agent_role == "Performance Analysis":
            st.info("Role Permission: **Query Long-Term KPI Trends**")
            st.caption(
                "🚫 Direct ticket creation or production change initiation is restricted for this role."
            )

        elif agent_role == "Change Planning":
            st.info("Role Permission: **Simulate Impact & Propose Change Spec**")
            st.caption(
                "🔒 Production write actions strictly require Human Authorization."
            )

# -----------------------------------------------------------------------------
# FOOTER
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:var(--card-text-muted); font-size:12px;'>"
    "Telecom Network Intelligence Platform Architecture Reference Implementation | Powered by Google Cloud & Model Context Protocol (MCP)"
    "</div>",
    unsafe_allow_html=True,
)
