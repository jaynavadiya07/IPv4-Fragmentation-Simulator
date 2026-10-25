"""
╔══════════════════════════════════════════════════════════════════╗
║  NetVista 3D — IPv4 Fragmentation Simulator                     ║
║  Interactive Browser-Based Simulator (Streamlit)                ║
║  Student ID: 25CS052 | Advanced Learner Group                   ║
║  Course: ITUC201 – Fundamentals of Computer Networks 2026-27    ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
import json

from fragmentation_engine import (
    FragmentationEngine, FragmentationResult, ValidationResult,
    ReassemblySimulationResult, ReassemblyEvent,
    IPV4_HEADER_SIZE, OFFSET_UNIT, MIN_MTU, MAX_PAYLOAD
)

# ─── Page Configuration ──────────────────────────────────────────
st.set_page_config(
    page_title="NetVista 3D — IPv4 Fragmentation Simulator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS for Professional Light Theme ─────────────────────
st.markdown("""
<style>
    /* ── Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    /* ── Global Styles ── */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    .stApp {
        background: linear-gradient(180deg, #FAFBFF 0%, #F0F4FF 100%) !important;
    }

    /* ── Hide Deploy Button & Clean Toolbar ── */
    .stDeployButton,
    [data-testid="stDeployButton"],
    .stAppDeployButton,
    button[title="Deploy this app"],
    [data-testid="stToolbarActions"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%) !important;
        border-right: 1px solid #334155 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #F8FAFC !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    section[data-testid="stSidebar"] label {
        color: #94A3B8 !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    section[data-testid="stSidebar"] .stNumberInput input,
    section[data-testid="stSidebar"] .stTextInput input {
        background: #1E293B !important;
        border: 1px solid #475569 !important;
        color: #F1F5F9 !important;
        border-radius: 8px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.95rem !important;
    }
    section[data-testid="stSidebar"] .stCheckbox label span {
        color: #CBD5E1 !important;
    }

    /* ── Headers ── */
    h1 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 800 !important;
        color: #0F172A !important;
        letter-spacing: -0.02em !important;
    }
    h2 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        color: #1E293B !important;
        letter-spacing: -0.01em !important;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 0.3em;
    }
    h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        color: #334155 !important;
    }

    /* ── Metric Cards ── */
    div[data-testid="stMetric"] {
        background: white !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 1rem 1.2rem !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06) !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stMetric"]:hover {
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1) !important;
        border-color: #93C5FD !important;
    }
    div[data-testid="stMetric"] label {
        color: #64748B !important;
        font-weight: 600 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #1E293B !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0.6rem 1.5rem !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3) !important;
        letter-spacing: 0.01em !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
        box-shadow: 0 4px 16px rgba(37, 99, 235, 0.4) !important;
    }

    /* ── DataFrames / Tables ── */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
    }
    
    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px !important;
        background: #F1F5F9 !important;
        border-radius: 12px !important;
        padding: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.9rem !important;
    }
    .stTabs [aria-selected="true"] {
        background: white !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        color: #2563EB !important;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        color: #334155 !important;
        background: #F8FAFC !important;
        border-radius: 8px !important;
    }

    /* ── Hero Container Card ── */
    .hero-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(246, 249, 255, 0.92) 100%);
        border: 1px solid #DBEAFE;
        border-radius: 20px;
        padding: 1.75rem 2rem 1.4rem 2rem;
        margin: 0.4rem 0 1.25rem 0;
        box-shadow: 0 10px 30px -5px rgba(37, 99, 235, 0.08), 0 4px 6px -2px rgba(15, 23, 42, 0.02);
        position: relative;
        overflow: hidden;
    }
    .hero-card::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; height: 4px;
        background: linear-gradient(90deg, #2563EB, #7C3AED, #38BDF8, #2563EB);
        background-size: 200% auto;
        animation: shimmer 5s linear infinite;
    }
    .hero-pill-status {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        color: #1D4ED8;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 0.28rem 0.85rem;
        border-radius: 30px;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 3px rgba(37, 99, 235, 0.08);
    }
    .status-pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #10B981;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 0 rgba(16, 185, 129, 0.6);
        animation: pulse-dot 2s infinite;
    }
    @keyframes pulse-dot {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { box-shadow: 0 0 0 7px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    .hero-title-main {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.75rem;
        font-weight: 800;
        background: linear-gradient(135deg, #0F172A 0%, #1E40AF 45%, #7C3AED 90%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.03em;
        line-height: 1.15;
        margin: 0;
    }
    .hero-simulator-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.85rem;
        font-weight: 700;
        color: #2563EB;
        letter-spacing: -0.02em;
        margin: 0.25rem 0 0.35rem 0;
    }
    .hero-subtitle-main {
        font-family: 'Inter', sans-serif;
        font-size: 1.05rem;
        color: #64748B;
        font-weight: 500;
        margin: 0.2rem 0 1.25rem 0;
        letter-spacing: -0.01em;
    }
    /* Feature Spec Pills Grid */
    .hero-features-grid {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 0.65rem;
        margin-bottom: 1.1rem;
    }
    .spec-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 0.4rem 0.85rem;
        font-family: 'Inter', sans-serif;
        font-size: 0.82rem;
        color: #334155;
        font-weight: 600;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        transition: all 0.25s ease;
    }
    .spec-pill:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.12);
        border-color: #93C5FD;
        background: #F8FAFC;
    }
    .spec-pill-icon {
        font-size: 1.05rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .spec-pill-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #2563EB;
        background: #EFF6FF;
        border: 1px solid #DBEAFE;
        padding: 0.12rem 0.45rem;
        border-radius: 6px;
        font-weight: 600;
    }
    /* Productivity Flow Steps Bar */
    .pipeline-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 0.65rem 1.1rem;
        margin-top: 0.6rem;
        gap: 0.5rem;
        overflow-x: auto;
    }
    .pipeline-step {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.79rem;
        font-family: 'Inter', sans-serif;
        color: #475569;
        font-weight: 600;
        white-space: nowrap;
    }
    .pipeline-num {
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: linear-gradient(135deg, #2563EB, #1D4ED8);
        color: white;
        font-size: 0.72rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.25);
    }
    .pipeline-arrow {
        color: #94A3B8;
        font-size: 0.85rem;
        font-weight: 700;
    }

    /* ── Destination Reassembly Styles ── */
    .reassembly-banner-success {
        background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
        border: 2px solid #86EFAC;
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 14px rgba(22, 163, 74, 0.08);
    }
    .reassembly-banner-failure {
        background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
        border: 2px solid #FCA5A5;
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 14px rgba(220, 38, 38, 0.08);
    }
    .icmp-packet-card {
        background: #0F172A;
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 1.4rem;
        color: #F8FAFC;
        margin: 1rem 0;
        font-family: 'Inter', sans-serif;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.15);
    }
    .icmp-field-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 0.75rem;
        margin: 1rem 0;
    }
    .icmp-field-box {
        background: #1E293B;
        border: 1px solid #475569;
        border-radius: 10px;
        padding: 0.75rem;
        text-align: center;
    }
    .icmp-field-label {
        font-size: 0.72rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 600;
    }
    .icmp-field-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.05rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-top: 0.2rem;
    }
    .hole-tag {
        display: inline-block;
        background: #FEE2E2;
        border: 1px solid #FCA5A5;
        color: #B91C1C;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 0.2rem 0.55rem;
        border-radius: 6px;
        margin: 0.2rem;
    }

    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1E293B 0%, #2563EB 50%, #7C3AED 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.2rem;
        letter-spacing: -0.03em;
        line-height: 1.1;
    }
    .hero-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.05rem;
        color: #64748B;
        font-weight: 400;
        margin-top: 0;
        letter-spacing: -0.01em;
    }
    .info-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 0.5rem;
        font-family: 'Inter', sans-serif;
        letter-spacing: 0.02em;
    }
    .badge-blue {
        background: #EFF6FF;
        color: #2563EB;
        border: 1px solid #BFDBFE;
    }
    .badge-green {
        background: #F0FDF4;
        color: #16A34A;
        border: 1px solid #BBF7D0;
    }
    .badge-purple {
        background: #FAF5FF;
        color: #7C3AED;
        border: 1px solid #DDD6FE;
    }
    .badge-amber {
        background: #FFFBEB;
        color: #D97706;
        border: 1px solid #FDE68A;
    }
    .badge-red {
        background: #FEF2F2;
        color: #DC2626;
        border: 1px solid #FECACA;
    }
    .section-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 0.75rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .validation-pass {
        background: #F0FDF4;
        border-left: 4px solid #22C55E;
        padding: 0.75rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.4rem 0;
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: #166534;
    }
    .validation-fail {
        background: #FEF2F2;
        border-left: 4px solid #EF4444;
        padding: 0.75rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.4rem 0;
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: #991B1B;
    }
    .packet-box {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border: 2px solid #93C5FD;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        color: #1E40AF;
        margin: 0.5rem 0;
    }
    .divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #CBD5E1, transparent);
        margin: 1.5rem 0;
        border: none;
    }
    .footer {
        text-align: center;
        padding: 2rem 0 1rem 0;
        color: #94A3B8;
        font-size: 0.85rem;
        font-family: 'Inter', sans-serif;
        border-top: 1px solid #E2E8F0;
        margin-top: 3rem;
    }
    .stDownloadButton > button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        box-shadow: 0 2px 8px rgba(5, 150, 105, 0.3) !important;
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #047857 0%, #065F46 100%) !important;
        box-shadow: 0 4px 16px rgba(5, 150, 105, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)


# ─── Helper Functions ────────────────────────────────────────────

def get_color_palette():
    """Return a consistent professional color palette."""
    return {
        "primary": "#2563EB",
        "secondary": "#7C3AED",
        "success": "#16A34A",
        "warning": "#D97706",
        "danger": "#DC2626",
        "info": "#0891B2",
        "dark": "#0F172A",
        "light": "#F8FAFC",
        "blue_gradient": ["#DBEAFE", "#93C5FD", "#60A5FA", "#3B82F6", "#2563EB", "#1D4ED8"],
        "fragment_colors": [
            "#3B82F6", "#8B5CF6", "#EC4899", "#F59E0B", "#10B981",
            "#EF4444", "#06B6D4", "#84CC16", "#F97316", "#6366F1",
            "#14B8A6", "#F43F5E", "#A855F7", "#0EA5E9", "#22C55E",
        ],
    }


def create_network_topology(result: FragmentationResult):
    """Create a clear network topology diagram showing the path and fragment counts."""
    if result.error or not result.fragments:
        return None

    num_hops = len(result.mtu_path)
    total_nodes = num_hops + 2  # source + routers + destination

    fig = go.Figure()

    # X positions for each node, spaced evenly
    node_x = list(range(total_nodes))

    # ── Draw link lines ──
    for i in range(total_nodes - 1):
        fig.add_trace(go.Scatter(
            x=[node_x[i], node_x[i + 1]],
            y=[0, 0],
            mode='lines',
            line=dict(color='#94A3B8', width=4),
            showlegend=False,
            hoverinfo='skip',
        ))

    # ── Draw nodes ──
    labels = ["Source"]
    colors_list = ["#2563EB"]
    sizes = [50]
    symbols = ["square"]
    hover_texts = [f"<b>Source Host</b><br>Payload: {result.original_payload} B<br>Total: {result.original_payload + IPV4_HEADER_SIZE} B"]

    for i, mtu in enumerate(result.mtu_path):
        labels.append(f"R{i+1}")
        colors_list.append("#7C3AED")
        sizes.append(42)
        symbols.append("diamond")
        # Count fragments existing after this hop
        hop_info = result.hop_details[i] if i < len(result.hop_details) else None
        frags_out = hop_info["fragments_out"] if hop_info else "?"
        fragmented = hop_info["fragmentation_occurred"] if hop_info else False
        hover_texts.append(
            f"<b>Router {i+1}</b><br>"
            f"MTU: {mtu} B<br>"
            f"Fragments out: {frags_out}<br>"
            f"{'⚡ Fragmentation occurred' if fragmented else '✅ No fragmentation'}"
        )

    labels.append("Dest")
    colors_list.append("#16A34A")
    sizes.append(50)
    symbols.append("square")
    hover_texts.append(f"<b>Destination Host</b><br>Receives {result.total_fragments} fragments<br>Reassembles into {result.original_payload} B")

    fig.add_trace(go.Scatter(
        x=node_x,
        y=[0] * total_nodes,
        mode='markers+text',
        marker=dict(size=sizes, color=colors_list, symbol=symbols,
                    line=dict(color='white', width=2)),
        text=labels,
        textposition='top center',
        textfont=dict(size=13, family='Space Grotesk, sans-serif', color='#1E293B'),
        hoverinfo='text',
        hovertext=hover_texts,
        showlegend=False,
    ))

    # ── MTU labels below each router ──
    for i, mtu in enumerate(result.mtu_path):
        hop_info = result.hop_details[i] if i < len(result.hop_details) else None
        fragmented = hop_info["fragmentation_occurred"] if hop_info else False
        badge_color = "#DC2626" if fragmented else "#16A34A"
        badge_text = f"MTU {mtu}B" + (" ⚡" if fragmented else " ✓")
        fig.add_annotation(
            x=i + 1, y=-0.35,
            text=f"<b>{badge_text}</b>",
            showarrow=False,
            font=dict(size=11, family='JetBrains Mono, monospace', color=badge_color),
        )

    # ── Fragment count annotations along links ──
    # Before first router: 1 packet
    fig.add_annotation(
        x=0.5, y=0.25,
        text="<b>1 packet</b>",
        showarrow=False,
        font=dict(size=10, family='Inter, sans-serif', color='#2563EB'),
        bgcolor='#EFF6FF', bordercolor='#BFDBFE', borderwidth=1, borderpad=4,
    )
    # After each router
    for i in range(num_hops):
        hop_info = result.hop_details[i] if i < len(result.hop_details) else None
        frags_out = hop_info["fragments_out"] if hop_info else "?"
        fig.add_annotation(
            x=i + 1.5, y=0.25,
            text=f"<b>{frags_out} frag{'s' if frags_out != 1 else ''}</b>",
            showarrow=False,
            font=dict(size=10, family='Inter, sans-serif', color='#7C3AED'),
            bgcolor='#FAF5FF', bordercolor='#DDD6FE', borderwidth=1, borderpad=4,
        )

    fig.update_layout(
        height=220,
        margin=dict(l=40, r=40, t=20, b=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   range=[-0.5, total_nodes - 0.5]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   range=[-0.8, 0.7]),
        font=dict(family='Inter, sans-serif'),
    )

    return fig


def create_fragment_waterfall(result: FragmentationResult):
    """Create a visual waterfall showing fragment byte coverage."""
    if result.error or not result.fragments:
        return None

    colors = get_color_palette()
    frag_colors = colors["fragment_colors"]

    fig = go.Figure()

    for i, frag in enumerate(result.fragments):
        fc = frag_colors[i % len(frag_colors)]
        fig.add_trace(go.Bar(
            x=[frag.payload_size],
            y=[f"F{frag.fragment_id}"],
            orientation='h',
            base=frag.byte_offset,
            marker=dict(color=fc, opacity=0.85, line=dict(color='white', width=1)),
            text=f"{frag.payload_size}B",
            textposition='inside',
            textfont=dict(color='white', size=11, family='JetBrains Mono, monospace'),
            hovertemplate=(
                f"<b>Fragment {frag.fragment_id}</b><br>"
                f"Payload: {frag.payload_size} B<br>"
                f"Offset: {frag.byte_offset} B (÷8 = {frag.offset_in_units})<br>"
                f"Range: {frag.payload_range[0]}–{frag.payload_range[1]}<br>"
                f"MF: {frag.mf_flag} | Hop: {frag.hop}"
                f"<extra></extra>"
            ),
            showlegend=False,
        ))

    fig.update_layout(
        title=dict(text="Fragment Byte Coverage Map",
                   font=dict(size=16, family='Space Grotesk, sans-serif', color='#1E293B')),
        xaxis=dict(
            title=dict(text="Byte Offset",
                       font=dict(family='Inter, sans-serif', color='#475569')),
            gridcolor='#F1F5F9',
        ),
        yaxis=dict(
            title=dict(text=""),
            autorange="reversed",
        ),
        height=max(220, len(result.fragments) * 32 + 100),
        margin=dict(l=50, r=20, t=50, b=50),
        plot_bgcolor='white',
        paper_bgcolor='rgba(0,0,0,0)',
        barmode='stack',
        font=dict(family='Inter, sans-serif', color='#334155'),
    )

    return fig


def create_experiment_charts(measurements):
    """Create experiment dashboard charts."""
    if not measurements:
        return None, None

    df = pd.DataFrame(measurements)
    colors = get_color_palette()

    # ── Chart 1: Fragment Count + Header Overhead vs MTU ──
    fig1 = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Fragment Count vs MTU", "Header Overhead vs MTU"),
        horizontal_spacing=0.12,
    )

    fig1.add_trace(go.Scatter(
        x=df["MTU (bytes)"], y=df["Fragment Count"],
        mode='lines+markers', name='Fragment Count',
        line=dict(color=colors["primary"], width=3),
        marker=dict(size=5, color=colors["primary"]),
        fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.08)',
        hovertemplate="MTU: %{x}B<br>Fragments: %{y}<extra></extra>",
    ), row=1, col=1)

    fig1.add_trace(go.Scatter(
        x=df["MTU (bytes)"], y=df["Total Header Overhead (bytes)"],
        mode='lines+markers', name='Header Overhead',
        line=dict(color=colors["danger"], width=3),
        marker=dict(size=5, color=colors["danger"]),
        fill='tozeroy', fillcolor='rgba(220, 38, 38, 0.08)',
        hovertemplate="MTU: %{x}B<br>Overhead: %{y}B<extra></extra>",
    ), row=1, col=2)

    fig1.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=50, b=50),
        plot_bgcolor='white',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#334155', size=12),
        showlegend=False,
    )
    fig1.update_xaxes(title_text="MTU (bytes)", gridcolor='#F1F5F9')
    fig1.update_yaxes(gridcolor='#F1F5F9')
    fig1.update_yaxes(title_text="Fragment Count", row=1, col=1)
    fig1.update_yaxes(title_text="Overhead (bytes)", row=1, col=2)

    # ── Chart 2: Efficiency + Overhead % vs MTU ──
    fig2 = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Transmission Efficiency vs MTU", "Overhead Percentage vs MTU"),
        horizontal_spacing=0.12,
    )

    fig2.add_trace(go.Scatter(
        x=df["MTU (bytes)"], y=df["Efficiency %"],
        mode='lines+markers', name='Efficiency',
        line=dict(color=colors["success"], width=3),
        marker=dict(size=5, color=colors["success"]),
        fill='tozeroy', fillcolor='rgba(22, 163, 74, 0.08)',
        hovertemplate="MTU: %{x}B<br>Efficiency: %{y}%<extra></extra>",
    ), row=1, col=1)

    fig2.add_trace(go.Scatter(
        x=df["MTU (bytes)"], y=df["Overhead %"],
        mode='lines+markers', name='Overhead %',
        line=dict(color=colors["warning"], width=3),
        marker=dict(size=5, color=colors["warning"]),
        fill='tozeroy', fillcolor='rgba(217, 119, 6, 0.08)',
        hovertemplate="MTU: %{x}B<br>Overhead: %{y}%<extra></extra>",
    ), row=1, col=2)

    fig2.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=50, b=50),
        plot_bgcolor='white',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#334155', size=12),
        showlegend=False,
    )
    fig2.update_xaxes(title_text="MTU (bytes)", gridcolor='#F1F5F9')
    fig2.update_yaxes(gridcolor='#F1F5F9')
    fig2.update_yaxes(title_text="Efficiency (%)", row=1, col=1)
    fig2.update_yaxes(title_text="Overhead (%)", row=1, col=2)

    return fig1, fig2


def create_fragment_size_chart(result: FragmentationResult):
    """Create a per-fragment stacked bar chart (payload + header)."""
    if result.error or not result.fragments:
        return None

    colors = get_color_palette()

    frag_ids = [f"F{f.fragment_id}" for f in result.fragments]
    payloads = [f.payload_size for f in result.fragments]
    headers = [f.header_size for f in result.fragments]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=frag_ids, y=payloads,
        name='Payload',
        marker=dict(color=colors["primary"]),
        hovertemplate="Fragment %{x}<br>Payload: %{y}B<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=frag_ids, y=headers,
        name='IPv4 Header (20B)',
        marker=dict(color=colors["danger"], opacity=0.7),
        hovertemplate="Fragment %{x}<br>Header: %{y}B<extra></extra>",
    ))

    fig.update_layout(
        barmode='stack',
        title=dict(text="Fragment Size Breakdown (Payload + Header)",
                   font=dict(size=16, family='Space Grotesk, sans-serif', color='#1E293B')),
        xaxis=dict(
            title=dict(text="Fragment",
                       font=dict(family='Inter, sans-serif', color='#475569')),
            gridcolor='#F1F5F9',
        ),
        yaxis=dict(
            title=dict(text="Size (bytes)",
                       font=dict(family='Inter, sans-serif', color='#475569')),
            gridcolor='#F1F5F9',
        ),
        height=350,
        margin=dict(l=20, r=20, t=50, b=50),
        plot_bgcolor='white',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#334155'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                    font=dict(size=12)),
    )

    return fig


def create_reassembly_memory_chart(result: FragmentationResult, reassembly: ReassemblySimulationResult, step_index=None):
    """Create an interactive visual memory buffer chart showing received fragments and missing holes."""
    if not result.fragments or result.error:
        return None
    
    colors = get_color_palette()
    frag_colors = colors["fragment_colors"]
    
    fig = go.Figure()
    
    # If step_index is provided, only include fragments received up to that step
    if step_index is not None and 1 <= step_index <= len(reassembly.events):
        active_event = reassembly.events[step_index - 1]
        arrived_fids = set()
        for ev in reassembly.events[:step_index]:
            if ev.fragment_id not in [f.fragment_id for f in reassembly.dropped_fragments]:
                arrived_fids.add(ev.fragment_id)
        current_holes = active_event.holes_after
    else:
        arrived_fids = {f.fragment_id for f in reassembly.fragments_received}
        current_holes = reassembly.final_holes
    
    # Draw received fragment chunks
    for i, frag in enumerate(result.fragments):
        if frag.fragment_id in arrived_fids:
            fc = frag_colors[i % len(frag_colors)]
            fig.add_trace(go.Bar(
                x=[frag.payload_size],
                y=["Destination Buffer"],
                orientation='h',
                base=frag.byte_offset,
                name=f"Fragment {frag.fragment_id}",
                marker=dict(color=fc, line=dict(color='white', width=1.5)),
                text=f"F{frag.fragment_id} ({frag.payload_size}B)",
                textposition='inside',
                textfont=dict(color='white', size=11, family='JetBrains Mono, monospace'),
                hovertemplate=(
                    f"<b>Fragment #{frag.fragment_id} (Received)</b><br>"
                    f"Payload: {frag.payload_size} Bytes<br>"
                    f"Range: Bytes {frag.payload_range[0]}–{frag.payload_range[1]}<br>"
                    f"Offset: {frag.byte_offset} (÷8 = {frag.offset_in_units})<br>"
                    f"MF: {frag.mf_flag}<br>"
                    f"<extra></extra>"
                ),
                showlegend=False,
            ))
    
    # Draw missing holes
    for hi, hole in enumerate(current_holes):
        hole_size = hole[1] - hole[0] + 1
        fig.add_trace(go.Bar(
            x=[hole_size],
            y=["Destination Buffer"],
            orientation='h',
            base=hole[0],
            name=f"Hole {hi+1}",
            marker=dict(
                color='#EF4444',
                pattern=dict(shape="/", fillmode="replace", bgcolor="#FEE2E2", fgcolor="#DC2626"),
                line=dict(color='#DC2626', width=2),
            ),
            text=f"⚠️ HOLE: {hole[0]}–{hole[1]} ({hole_size}B)",
            textposition='inside',
            textfont=dict(color='#991B1B', size=11, family='JetBrains Mono, monospace'),
            hovertemplate=(
                f"<b>⚠️ Missing Byte Hole #{hi+1}</b><br>"
                f"Missing Range: Bytes {hole[0]}–{hole[1]}<br>"
                f"Missing Size: {hole_size} Bytes<br>"
                f"Status: Waiting for fragment / Reassembly blocked<extra></extra>"
            ),
            showlegend=False,
        ))
    
    fig.update_layout(
        title=dict(
            text="Destination Host Reassembly Memory Map (RFC 791)",
            font=dict(size=15, family='Space Grotesk, sans-serif', color='#1E293B'),
        ),
        xaxis=dict(
            title=dict(text="Byte Offset (0 to Original Payload Size)", font=dict(family='Inter, sans-serif', color='#475569')),
            range=[-20, result.original_payload + 40],
            gridcolor='#F1F5F9',
        ),
        yaxis=dict(
            title=dict(text=""),
            showticklabels=False,
        ),
        height=190,
        margin=dict(l=20, r=20, t=45, b=40),
        plot_bgcolor='white',
        paper_bgcolor='rgba(0,0,0,0)',
        barmode='stack',
        font=dict(family='Inter, sans-serif', color='#334155'),
    )
    
    return fig


def build_animated_fragmentation_html(result: FragmentationResult) -> str:
    """Build an HTML/CSS animation of packets being fragmented at each hop."""
    if result.error or not result.fragments:
        return ""

    colors = get_color_palette()
    frag_colors = colors["fragment_colors"]
    num_hops = len(result.mtu_path)

    # Build hop stages: what fragments exist after each hop
    stages = []

    # Stage 0: original packet
    stages.append([{
        "id": 0,
        "size": result.original_payload,
        "offset": 0,
        "label": f"{result.original_payload}B",
    }])

    # Simulate stages by tracking fragments at each hop
    engine = FragmentationEngine()
    current_frags = [{"payload_size": result.original_payload, "byte_offset": 0, "more_fragments": False}]

    for hop_idx, mtu in enumerate(result.mtu_path):
        max_payload_per_frag = mtu - IPV4_HEADER_SIZE
        max_payload_aligned = (max_payload_per_frag // OFFSET_UNIT) * OFFSET_UNIT

        new_frags = []
        for frag in current_frags:
            frag_total = frag["payload_size"] + IPV4_HEADER_SIZE
            if frag_total <= mtu:
                new_frags.append(frag)
                continue

            remaining = frag["payload_size"]
            current_offset = frag["byte_offset"]
            original_mf = frag["more_fragments"]

            while remaining > 0:
                if remaining + IPV4_HEADER_SIZE <= mtu:
                    chunk = remaining
                    mf = original_mf
                else:
                    chunk = max_payload_aligned
                    mf = True
                new_frags.append({"payload_size": chunk, "byte_offset": current_offset, "more_fragments": mf})
                current_offset += chunk
                remaining -= chunk

        current_frags = new_frags
        stage_items = []
        for i, f in enumerate(current_frags):
            stage_items.append({
                "id": i,
                "size": f["payload_size"],
                "offset": f["byte_offset"],
                "label": f"{f['payload_size']}B",
            })
        stages.append(stage_items)

    # Build HTML
    html_parts = []
    html_parts.append("""
    <style>
        .anim-container { display: flex; flex-direction: column; gap: 1.2rem; }
        .anim-stage { display: flex; align-items: center; gap: 1rem; }
        .anim-label {
            min-width: 120px; text-align: right; font-family: 'Inter', sans-serif;
            font-weight: 600; font-size: 0.85rem; color: #475569;
        }
        .anim-label small { display: block; font-weight: 400; color: #94A3B8; font-size: 0.75rem; }
        .anim-bar-container {
            flex: 1; display: flex; flex-wrap: wrap; gap: 3px;
            align-items: center; min-height: 42px;
        }
        .anim-frag {
            height: 38px; border-radius: 6px; display: inline-flex;
            align-items: center; justify-content: center;
            color: white; font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem; font-weight: 600;
            animation: fadeIn 0.5s ease-out both;
            min-width: 28px; padding: 0 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.15);
        }
        @keyframes fadeIn { from { opacity: 0; transform: scaleX(0.3); } to { opacity: 1; transform: scaleX(1); } }
        .anim-arrow {
            text-align: center; color: #94A3B8; font-size: 1.2rem;
            padding-left: 120px; letter-spacing: 0.3em;
        }
    </style>
    <div class="anim-container">
    """)

    # Stage 0: Original
    html_parts.append(f"""
        <div class="anim-stage">
            <div class="anim-label">🖥️ Source<small>Original Packet</small></div>
            <div class="anim-bar-container">
                <div class="anim-frag" style="background: linear-gradient(135deg, #2563EB, #1D4ED8);
                     width: 100%; max-width: 500px;">
                    📦 {result.original_payload}B payload + {IPV4_HEADER_SIZE}B header = {result.original_payload + IPV4_HEADER_SIZE}B
                </div>
            </div>
        </div>
    """)

    # Each hop stage
    for hop_idx in range(num_hops):
        mtu = result.mtu_path[hop_idx]
        stage = stages[hop_idx + 1]
        hop_info = result.hop_details[hop_idx] if hop_idx < len(result.hop_details) else None
        fragmented = hop_info["fragmentation_occurred"] if hop_info else False

        # Arrow
        arrow_label = "⚡ FRAGMENTED" if fragmented else "✅ PASSED THROUGH"
        arrow_color = "#DC2626" if fragmented else "#16A34A"
        html_parts.append(f"""
            <div class="anim-arrow">
                <span style="color: {arrow_color}; font-size: 0.8rem; font-weight: 600;">▼ {arrow_label}</span>
            </div>
        """)

        # Fragments
        max_size = max(f["size"] for f in stage) if stage else 1
        html_parts.append(f"""
            <div class="anim-stage">
                <div class="anim-label">🔀 Router {hop_idx + 1}<small>MTU: {mtu}B</small></div>
                <div class="anim-bar-container">
        """)
        for i, frag in enumerate(stage):
            fc = frag_colors[i % len(frag_colors)]
            # Width proportional to size relative to original payload
            width_pct = max(8, (frag["size"] / result.original_payload) * 100)
            delay = i * 0.08
            html_parts.append(f"""
                    <div class="anim-frag" style="background: {fc}; flex: 0 0 auto;
                         width: {width_pct}%; max-width: 200px;
                         animation-delay: {delay}s;">
                        {frag['label']}
                    </div>
            """)
        html_parts.append("</div></div>")

    # Destination
    html_parts.append(f"""
        <div class="anim-arrow">
            <span style="color: #16A34A; font-size: 0.8rem; font-weight: 600;">▼ DELIVERED</span>
        </div>
        <div class="anim-stage">
            <div class="anim-label">🖥️ Destination<small>Reassembly</small></div>
            <div class="anim-bar-container">
                <div class="anim-frag" style="background: linear-gradient(135deg, #16A34A, #15803D);
                     width: 100%; max-width: 500px;">
                    📨 {result.total_fragments} fragments → reassembled to {result.original_payload}B
                </div>
            </div>
        </div>
    """)

    html_parts.append("</div>")
    return "".join(html_parts)


# ─── Sidebar Configuration ───────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <style>
        @keyframes pulse-ring {
            0% { box-shadow: 0 0 0 0 rgba(96, 165, 250, 0.4); }
            70% { box-shadow: 0 0 0 12px rgba(96, 165, 250, 0); }
            100% { box-shadow: 0 0 0 0 rgba(96, 165, 250, 0); }
        }
        @keyframes shimmer {
            0% { background-position: -200% center; }
            100% { background-position: 200% center; }
        }
        .sidebar-brand {
            text-align: center;
            padding: 1.5rem 0.5rem 1rem 0.5rem;
        }
        .sidebar-icon-wrap {
            width: 68px; height: 68px; margin: 0 auto 0.75rem auto;
            border-radius: 18px;
            background: linear-gradient(135deg, #1E3A5F 0%, #2563EB 50%, #7C3AED 100%);
            display: flex; align-items: center; justify-content: center;
            animation: pulse-ring 2.5s ease-out infinite;
            box-shadow: 0 4px 20px rgba(37, 99, 235, 0.35);
        }
        .sidebar-icon-wrap span { font-size: 2rem; line-height: 1; }
        .sidebar-title {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.6rem; font-weight: 800;
            background: linear-gradient(90deg, #60A5FA, #A78BFA, #60A5FA);
            background-size: 200% auto;
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: shimmer 4s linear infinite;
            letter-spacing: -0.02em;
            margin-bottom: 0.15rem;
        }
        .sidebar-subtitle {
            font-family: 'Inter', sans-serif;
            font-size: 0.78rem; color: #94A3B8;
            letter-spacing: 0.04em;
        }
        .sidebar-version {
            display: inline-block; margin-top: 0.6rem;
            padding: 0.2rem 0.65rem; border-radius: 20px;
            background: rgba(96, 165, 250, 0.12);
            border: 1px solid rgba(96, 165, 250, 0.25);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.68rem; font-weight: 600;
            color: #93C5FD; letter-spacing: 0.05em;
        }
    </style>
    <div class="sidebar-brand">
        <div class="sidebar-icon-wrap"><span>🌐</span></div>
        <div class="sidebar-title">NetVista 3D</div>
        <div class="sidebar-subtitle">IPv4 Fragmentation Simulator</div>
        <div class="sidebar-version">v1.0 • RFC 791</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    st.markdown("### ⚙️ Packet Configuration")

    payload_size = st.number_input(
        "PAYLOAD SIZE (BYTES)",
        min_value=1,
        max_value=MAX_PAYLOAD,
        value=4000,
        step=100,
        help="Size of the original IP payload (excluding 20-byte header)",
    )

    st.markdown("---")

    if "mtu_text_field" not in st.session_state:
        st.session_state["mtu_text_field"] = "1500, 620, 400"

    mtu_input = st.text_input(
        "MTU VALUES (COMMA-SEPARATED)",
        key="mtu_text_field",
        help="Enter MTU values for each hop, e.g. 1500, 620, 400",
    )

    # Parse MTU values
    try:
        mtu_path = [int(m.strip()) for m in mtu_input.split(",") if m.strip()]
        mtu_valid = all(m >= MIN_MTU for m in mtu_path) and len(mtu_path) > 0
    except ValueError:
        mtu_path = []
        mtu_valid = False

    if not mtu_valid:
        st.error(f"⚠️ Enter valid MTUs ≥ {MIN_MTU}B, comma-separated")

    def set_preset_mtu(val):
        st.session_state["mtu_text_field"] = val

    # Quick MTU presets
    st.markdown("**Quick Presets:**")
    preset_cols = st.columns(2)
    with preset_cols[0]:
        st.button("🌐 Ethernet", use_container_width=True, key="preset1", on_click=set_preset_mtu, args=("1500",))
    with preset_cols[1]:
        st.button("📶 Multi-hop", use_container_width=True, key="preset2", on_click=set_preset_mtu, args=("1500, 620, 400",))

    preset_cols2 = st.columns(2)
    with preset_cols2[0]:
        st.button("🔻 Bottleneck", use_container_width=True, key="preset3", on_click=set_preset_mtu, args=("1500, 200, 1500",))
    with preset_cols2[1]:
        st.button("📡 Internet", use_container_width=True, key="preset4", on_click=set_preset_mtu, args=("1500, 576",))

    st.markdown("---")

    st.markdown("### 🚩 IP Flags")
    df_flag = st.checkbox(
        "Don't Fragment (DF) bit set",
        value=False,
        help="When DF=1, packets are dropped instead of fragmented if too large",
    )

    st.markdown("---")

    # Run simulation button
    run_clicked = st.button(
        "🚀  Run Simulation",
        use_container_width=True,
        type="primary",
    )

    st.markdown("---")

    st.html("""
    <div style="background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(148, 163, 184, 0.3);
                border-radius: 14px; padding: 1.1rem 0.8rem; text-align: center; margin-top: 0.6rem;
                box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);">
        <div style="font-size: 0.82rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; margin-bottom: 0.35rem;">
            Student Candidate
        </div>
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.45rem; font-weight: 800; color: #60A5FA; letter-spacing: 0.03em;">
            25CS052
        </div>
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.2rem; font-weight: 700; color: #FFFFFF; letter-spacing: 0.05em; margin-top: 0.2rem;">
            JAY NAVADIYA
        </div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; color: #CBD5E1; font-weight: 600; margin-top: 0.5rem; letter-spacing: 0.02em;">
            ITUC201 • 2026-27
        </div>
    </div>
    """)


# ─── Main Content Area ────────────────────────────────────────────

# Hero Header - Clean st.html rendering with no raw code leakage
st.html("""
<div class="hero-card">
    <div style="text-align: center;">
        <div class="hero-pill-status">
            <span class="status-pulse-dot"></span> RFC 791 • LIVE PROTOCOL SIMULATOR
        </div>
        <div class="hero-title-main">NetVista 3D</div>
        <div class="hero-simulator-title">IPv4 Fragmentation Simulator</div>
        <div class="hero-subtitle-main">
            Interactive Visual Demonstration & Path MTU Analytical Engine
        </div>
        
        <div class="hero-features-grid">
            <div class="spec-pill">
                <span class="spec-pill-icon">🔬</span>
                <span>RFC 791 Standard</span>
                <span class="spec-pill-sub">Compliant</span>
            </div>
            <div class="spec-pill">
                <span class="spec-pill-icon">📐</span>
                <span>Fixed Header</span>
                <span class="spec-pill-sub">20 Bytes</span>
            </div>
            <div class="spec-pill">
                <span class="spec-pill-icon">⚡</span>
                <span>Offset Granularity</span>
                <span class="spec-pill-sub">8-Byte Blocks</span>
            </div>
            <div class="spec-pill">
                <span class="spec-pill-icon">🔀</span>
                <span>Path Topology</span>
                <span class="spec-pill-sub">Multi-Hop MTUs</span>
            </div>
            <div class="spec-pill">
                <span class="spec-pill-icon">🛡️</span>
                <span>Flags Evaluation</span>
                <span class="spec-pill-sub">DF / MF Bits</span>
            </div>
        </div>

        <div class="pipeline-bar">
            <div class="pipeline-step">
                <span class="pipeline-num">1</span>
                <span>Configure Payload & MTUs</span>
            </div>
            <span class="pipeline-arrow">➔</span>
            <div class="pipeline-step">
                <span class="pipeline-num">2</span>
                <span>Simulate Router Hops</span>
            </div>
            <span class="pipeline-arrow">➔</span>
            <div class="pipeline-step">
                <span class="pipeline-num">3</span>
                <span>Inspect Offsets & Headers</span>
            </div>
            <span class="pipeline-arrow">➔</span>
            <div class="pipeline-step">
                <span class="pipeline-num">4</span>
                <span>Destination Reassembly & RFC Verification</span>
            </div>
        </div>
    </div>
</div>
""")

# ─── Run Simulation ──────────────────────────────────────────────

if run_clicked or "result" not in st.session_state:
    if mtu_valid and mtu_path:
        engine = FragmentationEngine()
        result = engine.fragment_packet(payload_size, mtu_path, df_flag)
        validation = engine.validate_fragments(result)
        st.session_state["result"] = result
        st.session_state["validation"] = validation
    else:
        st.session_state.pop("result", None)
        st.session_state.pop("validation", None)

# Get result from session
result = st.session_state.get("result")
validation = st.session_state.get("validation")

if result is None:
    st.info("👆 Configure your packet parameters in the sidebar and click **Run Simulation**")
    st.stop()

# ─── Error Handling ──────────────────────────────────────────────
if result.error:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
                border: 2px solid #FECACA; border-radius: 16px; padding: 2rem;
                text-align: center; margin: 2rem 0;">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">🚫</div>
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.3rem;
                    font-weight: 700; color: #991B1B; margin-bottom: 0.5rem;">
            Packet Dropped!
        </div>
        <div style="font-family: 'Inter', sans-serif; color: #DC2626; font-size: 1rem;">
            {result.error}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if result.df_flag:
        st.markdown("""
        <div class="section-card">
            <h3 style="margin-top:0;">📚 What Happens with DF Flag?</h3>
            <p>When the <b>Don't Fragment (DF)</b> bit is set in the IPv4 header:</p>
            <ol>
                <li>The router checks if the packet size exceeds the outgoing link MTU</li>
                <li>If it does, the router <b>drops the packet</b> (instead of fragmenting it)</li>
                <li>The router sends an <b>ICMP Destination Unreachable</b> message (Type 3, Code 4 — Fragmentation Needed) back to the source</li>
                <li>This ICMP message includes the MTU of the next hop, enabling <b>Path MTU Discovery (PMTUD)</b></li>
            </ol>
            <p style="color: #64748B; font-size: 0.9rem;">
                PMTUD is used by modern TCP implementations to find the optimal packet size
                that avoids fragmentation across the entire path.
            </p>
        </div>
        """, unsafe_allow_html=True)
    st.stop()


# ─── Summary Metrics ────────────────────────────────────────────

st.markdown("## 📊 Simulation Results")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Original Payload", f"{result.original_payload:,} B")
with col2:
    st.metric("Total Fragments", f"{result.total_fragments}")
with col3:
    st.metric("Header Overhead", f"{result.total_header_overhead} B")
with col4:
    st.metric("Overhead %", f"{result.overhead_percentage:.1f}%")
with col5:
    st.metric("Bytes Transmitted", f"{result.total_bytes_transmitted:,} B")

st.markdown("")

# MTU path display
st.markdown(f"""
<div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px;
            padding: 0.8rem 1.2rem; margin: 0.5rem 0;">
    <span style="font-weight: 600; color: #64748B; font-size: 0.85rem; text-transform: uppercase;
                 letter-spacing: 0.05em;">Network Path:</span>
    <span style="font-family: 'JetBrains Mono', monospace; color: #1E293B; margin-left: 0.5rem;">
        🖥️ Source → {" → ".join([f"🔀 {m}B" for m in result.mtu_path])} → 🖥️ Destination
    </span>
</div>
""", unsafe_allow_html=True)


# ─── Tabbed Interface ────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🎬 Animation",
    "🔍 Fragment Inspector",
    "🧩 Destination Reassembly",
    "📊 Experiment Dashboard",
    "✅ Validation",
    "📐 Theory",
])


# ─── TAB 1: Animated Fragmentation ──────────────────────────────
with tab1:
    st.markdown("### 🎬 Fragmentation Visualization")
    st.markdown("*Watch how the packet is fragmented as it traverses routers with different MTUs*")

    # Network topology diagram (Plotly)
    topo_fig = create_network_topology(result)
    if topo_fig:
        st.plotly_chart(topo_fig, use_container_width=True, key="topo")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Animated hop-by-hop HTML visualization
    st.markdown("#### 📦 Hop-by-Hop Fragmentation Process")
    anim_html = build_animated_fragmentation_html(result)
    if anim_html:
        st.components.v1.html(anim_html, height=max(300, (len(result.mtu_path) + 2) * 100), scrolling=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Fragment coverage map
    st.markdown("#### 🗺️ Fragment Byte Coverage Map")
    waterfall_fig = create_fragment_waterfall(result)
    if waterfall_fig:
        st.plotly_chart(waterfall_fig, use_container_width=True, key="waterfall")

    # Fragment size breakdown chart
    st.markdown("#### 📊 Fragment Size Breakdown")
    size_chart = create_fragment_size_chart(result)
    if size_chart:
        st.plotly_chart(size_chart, use_container_width=True, key="sizes")


# ─── TAB 2: Fragment Inspector ──────────────────────────────────
with tab2:
    st.markdown("### 🔍 Detailed Fragment Inspector")
    st.markdown("*Complete breakdown of every fragment with all IPv4 header fields*")

    # Create DataFrame for display
    frag_data = [f.to_dict() for f in result.fragments]
    df = pd.DataFrame(frag_data)

    st.dataframe(
        df,
        use_container_width=True,
        height=min(450, len(df) * 38 + 50),
        column_config={
            "Fragment #": st.column_config.NumberColumn("Fragment #", help="Sequential fragment number"),
            "Hop": st.column_config.NumberColumn("Hop", help="Router hop where fragmentation occurred"),
            "MTU (bytes)": st.column_config.NumberColumn("MTU (B)", help="MTU at the fragmenting router"),
            "Payload (bytes)": st.column_config.NumberColumn("Payload (B)", help="Fragment payload size"),
            "Header (bytes)": st.column_config.NumberColumn("Header (B)", help="IPv4 header size (always 20B)"),
            "Total Size (bytes)": st.column_config.NumberColumn("Total (B)", help="Payload + Header"),
            "Byte Offset": st.column_config.NumberColumn("Byte Offset", help="Offset in bytes from start"),
            "Offset (÷8)": st.column_config.NumberColumn("Offset ÷8", help="Fragment Offset field value"),
            "MF Flag": st.column_config.NumberColumn("MF", help="More Fragments flag"),
            "Payload Range": st.column_config.TextColumn("Byte Range", help="Payload byte range (inclusive)"),
        },
    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Per-fragment detail cards
    st.markdown("#### 📋 Fragment Details")

    cols_per_row = min(3, len(result.fragments))

    for i in range(0, len(result.fragments), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(result.fragments):
                break
            frag = result.fragments[idx]
            with col:
                frag_color = get_color_palette()['fragment_colors'][idx % len(get_color_palette()['fragment_colors'])]
                mf_badge = '<span class="info-badge badge-amber">MF = 1</span>' if frag.more_fragments else '<span class="info-badge badge-green">MF = 0 (Last)</span>'
                st.markdown(f"""
                <div class="section-card" style="border-top: 3px solid {frag_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-family: 'Space Grotesk', sans-serif; font-weight: 700;
                                     font-size: 1.1rem; color: #1E293B;">
                            Fragment {frag.fragment_id}
                        </span>
                        {mf_badge}
                    </div>
                    <div style="margin-top: 0.75rem; font-family: 'JetBrains Mono', monospace;
                                font-size: 0.85rem; line-height: 1.8;">
                        <div>📦 Payload: <b>{frag.payload_size} bytes</b></div>
                        <div>📋 Header: <b>{frag.header_size} bytes</b></div>
                        <div>📏 Total: <b>{frag.total_size} bytes</b></div>
                        <div>📍 Byte Offset: <b>{frag.byte_offset}</b></div>
                        <div>🔢 Offset ÷8: <b>{frag.offset_in_units}</b></div>
                        <div>🔀 Created at Hop: <b>{frag.hop}</b></div>
                        <div>📐 MTU: <b>{frag.mtu_at_hop} bytes</b></div>
                        <div>📊 Range: <b>{frag.payload_range[0]}–{frag.payload_range[1]}</b></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Download fragment data
    csv_data = FragmentationEngine.export_fragments_csv(result)
    st.download_button(
        "📥  Download Fragment Data (CSV)",
        data=csv_data,
        file_name=f"netvista3d_fragments_{result.original_payload}B_{'_'.join(map(str, result.mtu_path))}.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ─── TAB 3: Destination Reassembly ──────────────────────────────
with tab3:
    st.markdown("### 🧩 Destination Host Datagram Reassembly Simulator")
    st.markdown(
        "*RFC 791 Specification: Intermediate routers only fragment oversized packets; "
        "reassembly occurs exclusively at the destination host before handing data to Layer 4 (Transport Layer).*"
    )

    # ── Interactive Control Bar ──
    re_ctrl_col1, re_ctrl_col2, re_ctrl_col3 = st.columns([1.2, 1.4, 1.0])

    with re_ctrl_col1:
        st.markdown("#### 🔄 1. Arrival Sequence Mode")
        arrival_choice = st.radio(
            "Select fragment arrival order:",
            options=["In-Order (F1 → Fn)", "Reverse-Order (Fn → F1)", "Multi-Path Out-of-Order"],
            index=0,
            key="arrival_mode_choice",
            help="Demonstrates that IPv4 reassembly operates on byte offsets and can absorb out-of-order packets."
        )
        if arrival_choice.startswith("In-Order"):
            arrival_mode = "in_order"
        elif arrival_choice.startswith("Reverse"):
            arrival_mode = "reverse_order"
        else:
            arrival_mode = "scrambled"

    with re_ctrl_col2:
        st.markdown("#### 🚨 2. Simulate Lost Fragment(s)")
        simulate_loss = st.checkbox(
            "Enable Packet Drop / Lost Fragment",
            value=False,
            key="cb_simulate_loss",
            help="Simulates fragment drop due to router buffer congestion, bit errors, or link failure."
        )

        fragment_options = [
            f"Fragment #{f.fragment_id} [Bytes {f.payload_range[0]}–{f.payload_range[1]}]"
            for f in result.fragments
        ]

        if simulate_loss and fragment_options:
            default_drops = [fragment_options[min(1, len(fragment_options)-1)]]
            selected_drop_labels = st.multiselect(
                "Select which fragment(s) are LOST in transit:",
                options=fragment_options,
                default=default_drops,
                key="drop_multiselect"
            )
            dropped_ids = [int(lbl.split("#")[1].split(" ")[0]) for lbl in selected_drop_labels]
        else:
            dropped_ids = []

    with re_ctrl_col3:
        st.markdown("#### ⏱️ 3. RFC 791 Timer")
        timeout_val = st.slider(
            "Reassembly Timeout (seconds)",
            min_value=5.0,
            max_value=60.0,
            value=30.0,
            step=5.0,
            key="re_timeout_slider",
            help="RFC 791 specifies that if the datagram remains incomplete when the timer reaches 0, the partially assembled packet must be discarded."
        )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Run Reassembly Simulation ──
    re_sim = FragmentationEngine.simulate_reassembly(
        result=result,
        arrival_mode=arrival_mode,
        dropped_fragment_ids=dropped_ids,
        timeout_seconds=timeout_val
    )

    # ── Status Banner & Key Metrics ──
    if re_sim.success:
        st.markdown(f"""
        <div class="reassembly-banner-success">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.25rem; font-weight: 800; color: #166534;">
                        🎉 Datagram Reassembled Successfully!
                    </div>
                    <div style="font-size: 0.92rem; color: #15803D; margin-top: 0.35rem; line-height: 1.5;">
                        All <b>{len(re_sim.fragments_received)} / {re_sim.total_fragments_sent} fragments</b> received and verified.
                        Complete original payload of <b>{re_sim.original_payload:,} bytes</b> reconstructed without any missing byte holes.
                        Datagram handed off to <b>Layer 4 (Transport Layer: TCP/UDP)</b>.
                    </div>
                </div>
                <div style="text-align: right; background: white; padding: 0.6rem 1rem; border-radius: 12px; border: 1px solid #BBF7D0; box-shadow: 0 2px 6px rgba(0,0,0,0.04);">
                    <div style="font-size: 0.72rem; color: #64748B; text-transform: uppercase; font-weight: 700;">Reassembly Status</div>
                    <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.15rem; font-weight: 800; color: #16A34A;">COMPLETE ✅</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        holes_fmt = ", ".join([f"Bytes {h[0]}–{h[1]}" for h in re_sim.final_holes])
        st.markdown(f"""
        <div class="reassembly-banner-failure">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.25rem; font-weight: 800; color: #991B1B;">
                        🚨 Reassembly Failed: Missing Hole Timeout!
                    </div>
                    <div style="font-size: 0.92rem; color: #B91C1C; margin-top: 0.35rem; line-height: 1.5;">
                        RFC 791 timer expired after <b>{re_sim.timeout_seconds:.1f} seconds</b>.
                        Unclosed missing byte hole(s): <span class="hole-tag">{holes_fmt}</span> due to lost fragment(s).
                        <b>All {len(re_sim.fragments_received)} buffered fragments were discarded from memory.</b>
                        Transmitted <b>ICMP Time Exceeded (Type 11, Code 1)</b> back to Source Host.
                    </div>
                </div>
                <div style="text-align: right; background: white; padding: 0.6rem 1rem; border-radius: 12px; border: 1px solid #FECACA; box-shadow: 0 2px 6px rgba(0,0,0,0.04);">
                    <div style="font-size: 0.72rem; color: #64748B; text-transform: uppercase; font-weight: 700;">Reassembly Status</div>
                    <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.15rem; font-weight: 800; color: #DC2626;">TIMED OUT ❌</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Summary KPI Metrics ──
    re_m1, re_m2, re_m3, re_m4, re_m5 = st.columns(5)
    with re_m1:
        st.metric("Total Fragments Sent", f"{re_sim.total_fragments_sent}")
    with re_m2:
        st.metric("Fragments Arrived", f"{len(re_sim.fragments_received)}")
    with re_m3:
        st.metric("Lost in Transit", f"{len(re_sim.dropped_fragments)}")
    with re_m4:
        rec_bytes = sum(f.payload_size for f in re_sim.fragments_received)
        pct = (rec_bytes / re_sim.original_payload) * 100 if re_sim.original_payload else 0
        st.metric("Buffer Filled", f"{pct:.1f}%", f"{rec_bytes}/{re_sim.original_payload} B")
    with re_m5:
        st.metric("Unclosed Holes", f"{len(re_sim.final_holes)}")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Step-by-Step Playback Stepper ──
    st.markdown("#### 🕹️ Interactive Step-by-Step Buffer Reassembly Playback")
    st.markdown("*Use the step slider to inspect the destination buffer after each fragment arrives:*")
    
    total_steps = len(re_sim.events)
    step_slider = st.slider(
        "Reassembly Arrival Step:",
        min_value=1,
        max_value=max(1, total_steps),
        value=total_steps,
        key="re_step_slider",
        help="Step through each fragment arrival to observe how memory is mapped and holes are closed."
    )

    # Reassembly Memory Map Chart for the selected step
    re_chart = create_reassembly_memory_chart(result, re_sim, step_index=step_slider)
    if re_chart:
        st.plotly_chart(re_chart, use_container_width=True, key="re_chart_plot")

    # Current step event callout
    if 1 <= step_slider <= len(re_sim.events):
        cur_ev = re_sim.events[step_slider - 1]
        step_badge_color = "#DC2626" if cur_ev.fragment_id in [f.fragment_id for f in re_sim.dropped_fragments] else "#2563EB"
        st.markdown(f"""
        <div style="background: white; border: 1px solid #E2E8F0; border-left: 4px solid {step_badge_color};
                    border-radius: 10px; padding: 0.85rem 1.1rem; margin-top: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 0.95rem; color: #1E293B;">
                    Step {cur_ev.step} of {total_steps}: Fragment #{cur_ev.fragment_id}
                </span>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: #64748B;">
                    Buffer Filled: <b>{cur_ev.buffer_percent}%</b> ({cur_ev.buffered_bytes_after:,} / {re_sim.original_payload:,} B)
                </span>
            </div>
            <div style="font-size: 0.88rem; color: #334155; margin-top: 0.35rem;">
                {cur_ev.description}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── ICMP Error Packet Card (When packet loss simulated) ──
    if re_sim.icmp_generated:
        st.markdown("#### 🚨 Generated ICMP Error Packet (RFC 792 / RFC 1122)")
        st.markdown(
            "*When the reassembly timer expires with open holes, RFC 791 mandates discarding "
            "all buffered fragments and generating an ICMP Time Exceeded message to notify the source host:*"
        )
        
        dropped_name = f"#{re_sim.dropped_fragments[0].fragment_id}" if re_sim.dropped_fragments else "X"
        st.markdown(f"""
        <div class="icmp-packet-card">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 0.6rem;">
                <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 700; color: #F87171;">
                    📡 ICMP Error Datagram Sent to Source Host
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; background: #991B1B; color: #FEE2E2; padding: 0.2rem 0.6rem; border-radius: 6px;">
                    RFC 792 Type 11 Code 1
                </div>
            </div>
            
            <div class="icmp-field-grid">
                <div class="icmp-field-box">
                    <div class="icmp-field-label">ICMP Type</div>
                    <div class="icmp-field-val" style="color: #F87171;">11</div>
                    <div style="font-size: 0.7rem; color: #94A3B8; margin-top: 0.2rem;">Time Exceeded</div>
                </div>
                <div class="icmp-field-box">
                    <div class="icmp-field-label">ICMP Code</div>
                    <div class="icmp-field-val" style="color: #F87171;">1</div>
                    <div style="font-size: 0.7rem; color: #94A3B8; margin-top: 0.2rem;">Reassembly Timeout</div>
                </div>
                <div class="icmp-field-box">
                    <div class="icmp-field-label">Checksum</div>
                    <div class="icmp-field-val">0xA4F2</div>
                    <div style="font-size: 0.7rem; color: #94A3B8; margin-top: 0.2rem;">16-Bit 1's Compl</div>
                </div>
                <div class="icmp-field-box">
                    <div class="icmp-field-label">Unused / Reserved</div>
                    <div class="icmp-field-val">0x00000000</div>
                    <div style="font-size: 0.7rem; color: #94A3B8; margin-top: 0.2rem;">32 Bits Zeroes</div>
                </div>
            </div>
            
            <div style="background: #1E293B; border-radius: 8px; padding: 0.8rem; border: 1px solid #334155; margin-top: 0.5rem; font-size: 0.85rem; line-height: 1.6;">
                <div style="font-weight: 700; color: #93C5FD; margin-bottom: 0.2rem;">📦 Encapsulated Diagnostic Payload:</div>
                <div>• <b>Original IPv4 Header:</b> 20 Bytes (Ident=0x4A1F, Proto=6/TCP, Src=192.168.1.10, Dst=10.0.0.1)</div>
                <div>• <b>First 64 Bits of Datagram:</b> Original TCP ports (Src Port: 54321, Dst Port: 443 HTTPS) for upper-layer demux</div>
                <div style="color: #FCA5A5; margin-top: 0.4rem;">
                    ⚠️ <b>Consequence:</b> IP is a connectionless network layer protocol with <i>no selective fragment acknowledgment</i>.
                    The sender cannot retransmit just Fragment {dropped_name}; 
                    the entire {result.original_payload}-byte TCP segment must be retransmitted from scratch.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── RFC 791 Hole Descriptor Table ──
    st.markdown("#### 📋 RFC 791 Hole Descriptor State Table")
    st.markdown("*Chronological state machine log of the destination host's hole descriptor list:*")
    
    hole_log_data = []
    for ev in re_sim.events:
        holes_repr = ", ".join([f"[{h[0]}–{h[1]}]" for h in ev.holes_after]) if ev.holes_after else "None (Closed)"
        hole_log_data.append({
            "Step": ev.step,
            "Fragment": f"F#{ev.fragment_id}",
            "Payload (Bytes)": f"{ev.payload_size} B",
            "Offset ÷8": ev.offset // OFFSET_UNIT,
            "Byte Range": f"{ev.payload_range[0]}–{ev.payload_range[1]}",
            "MF": ev.mf_flag,
            "Holes Remaining": holes_repr,
            "Buffer Progress": f"{ev.buffer_percent}%"
        })
    st.dataframe(pd.DataFrame(hole_log_data), use_container_width=True, height=280)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Key Viva & Examination Insights ──
    st.markdown("#### 🎓 Viva & Exam Insights: Why Reassembly Matters")
    st.markdown("""
    <div class="section-card">
        <h4 style="margin-top:0; color: #1E293B;">Essential Exam Concepts on IPv4 Reassembly</h4>
        <ol>
            <li><b>Why do intermediate routers NEVER reassemble fragments?</b><br>
                <span style="color: #475569;">In dynamic IP networks, fragments can traverse completely different physical routes (multipath / asymmetric routing). A router along Path A may never see the fragments traveling along Path B! Reassembly at intermediate routers would require massive memory buffering and could cause permanent deadlocks.</span>
            </li>
            <li style="margin-top: 0.5rem;"><b>Why is 1 fragment loss so catastrophic in IPv4?</b><br>
                <span style="color: #475569;">IPv4 is an unreliable best-effort protocol without fragment-level ACKs. If 1 fragment out of 14 is lost, the entire 4,000-byte datagram is discarded by the destination after the 30-second timeout, wasting 100% of the network bandwidth used by the other 13 fragments.</span>
            </li>
            <li style="margin-top: 0.5rem;"><b>How do modern protocols prevent this?</b><br>
                <span style="color: #475569;">Modern networks use <b>Path MTU Discovery (PMTUD)</b> with <code>DF=1</code> to determine the path MTU beforehand and size TCP MSS accordingly. In IPv6, intermediate routers are forbidden from fragmenting altogether!</span>
            </li>
        </ol>
    </div>
    """, unsafe_allow_html=True)


# ─── TAB 4: Experiment Dashboard ────────────────────────────────
with tab4:
    st.markdown("### 📊 Controlled Experiment Dashboard")
    st.markdown("*Fixed payload, varying MTU — measuring fragment count and overhead*")

    exp_col1, exp_col2 = st.columns([1, 1])
    with exp_col1:
        exp_payload = st.number_input(
            "Experiment Payload Size (bytes)",
            min_value=100, max_value=MAX_PAYLOAD, value=4000, step=500,
            key="exp_payload",
        )
    with exp_col2:
        exp_mtu_range = st.slider(
            "MTU Range (bytes)",
            min_value=MIN_MTU, max_value=1500, value=(100, 1500), step=20,
            key="exp_mtu_range",
        )

    if st.button("🧪  Run Experiment", use_container_width=True, key="run_exp"):
        with st.spinner("Running controlled experiment..."):
            mtu_values = list(range(max(MIN_MTU, exp_mtu_range[0]), exp_mtu_range[1] + 1, 20))
            measurements = FragmentationEngine.run_experiment(exp_payload, mtu_values)
            st.session_state["measurements"] = measurements

    measurements = st.session_state.get("measurements")

    if measurements:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        m_df = pd.DataFrame(measurements)

        sum_cols = st.columns(4)
        with sum_cols[0]:
            st.metric("MTU Range", f"{m_df['MTU (bytes)'].min()}–{m_df['MTU (bytes)'].max()} B")
        with sum_cols[1]:
            st.metric("Max Fragments", f"{m_df['Fragment Count'].max()}")
        with sum_cols[2]:
            st.metric("Max Overhead", f"{m_df['Total Header Overhead (bytes)'].max()} B")
        with sum_cols[3]:
            st.metric("Data Points", f"{len(measurements)}")

        st.markdown("")

        fig1, fig2 = create_experiment_charts(measurements)
        if fig1:
            st.plotly_chart(fig1, use_container_width=True, key="exp1")
        if fig2:
            st.plotly_chart(fig2, use_container_width=True, key="exp2")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # Measurement data table
        st.markdown("#### 📋 Measurement Data")
        st.dataframe(m_df, use_container_width=True, height=300)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # Multi-hop experiment
        st.markdown("#### 🔗 Multi-Hop Path Comparison")

        multi_measurements = FragmentationEngine.run_multi_hop_experiment(exp_payload)
        if multi_measurements:
            multi_df = pd.DataFrame(multi_measurements)
            st.dataframe(multi_df, use_container_width=True, height=380)

            fig_multi = go.Figure()
            fig_multi.add_trace(go.Bar(
                x=multi_df["MTU Path"], y=multi_df["Fragment Count"],
                name="Fragment Count",
                marker=dict(color="#3B82F6"),
            ))
            fig_multi.add_trace(go.Bar(
                x=multi_df["MTU Path"], y=multi_df["Overhead %"],
                name="Overhead %",
                marker=dict(color="#F59E0B"),
            ))
            fig_multi.update_layout(
                title=dict(text="Multi-Hop Path Comparison",
                           font=dict(size=16, family='Space Grotesk, sans-serif', color='#1E293B')),
                barmode='group',
                height=400,
                plot_bgcolor='white',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter, sans-serif', color='#334155'),
                xaxis=dict(tickangle=-45, gridcolor='#F1F5F9'),
                yaxis=dict(gridcolor='#F1F5F9'),
                margin=dict(l=20, r=20, t=50, b=120),
            )
            st.plotly_chart(fig_multi, use_container_width=True, key="multi")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # Download buttons
        exp_csv = FragmentationEngine.export_measurements_csv(measurements)
        dcol1, dcol2 = st.columns(2)
        with dcol1:
            st.download_button(
                "📥  Download Measurements (CSV)",
                data=exp_csv,
                file_name=f"netvista3d_experiment_{exp_payload}B.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with dcol2:
            if multi_measurements:
                multi_csv = FragmentationEngine.export_measurements_csv(multi_measurements)
                st.download_button(
                    "📥  Download Multi-Hop Data (CSV)",
                    data=multi_csv,
                    file_name=f"netvista3d_multihop_{exp_payload}B.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
    else:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; color: #94A3B8;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🧪</div>
            <div style="font-size: 1.1rem; font-weight: 500;">
                Click <b>Run Experiment</b> to generate measurements
            </div>
            <div style="font-size: 0.9rem; margin-top: 0.5rem;">
                The experiment keeps payload fixed and varies MTU to observe fragmentation behavior
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─── TAB 5: Validation ──────────────────────────────────────────
with tab5:
    st.markdown("### ✅ Validation & Edge Case Checks")
    st.markdown("*Comprehensive verification of fragment correctness*")

    if validation:
        overall_color = "#16A34A" if validation.is_valid else "#DC2626"
        overall_icon = "✅" if validation.is_valid else "❌"
        overall_text = "ALL CHECKS PASSED" if validation.is_valid else "SOME CHECKS FAILED"

        st.markdown(f"""
        <div style="background: {'#F0FDF4' if validation.is_valid else '#FEF2F2'};
                    border: 2px solid {'#86EFAC' if validation.is_valid else '#FECACA'};
                    border-radius: 16px; padding: 1.5rem; text-align: center; margin-bottom: 1.5rem;">
            <div style="font-size: 2rem;">{overall_icon}</div>
            <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.2rem;
                        font-weight: 700; color: {overall_color};">
                {overall_text}
            </div>
            <div style="font-size: 0.85rem; color: #64748B; margin-top: 0.3rem;">
                {sum(1 for c in validation.checks if c['passed'])}/{len(validation.checks)} checks passed
            </div>
        </div>
        """, unsafe_allow_html=True)

        for check in validation.checks:
            css_class = "validation-pass" if check["passed"] else "validation-fail"
            st.markdown(f"""
            <div class="{css_class}">
                <div style="font-weight: 600; font-size: 0.95rem;">{check['name']}</div>
                <div style="font-size: 0.85rem; margin-top: 0.25rem; opacity: 0.9;">{check['detail']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # DF Flag Test
    st.markdown("#### 🚫 Don't Fragment (DF) Flag Test")

    df_result = FragmentationEngine.fragment_packet(payload_size, mtu_path, df_flag=True)

    if df_result.error:
        st.markdown(f"""
        <div class="validation-fail">
            <div style="font-weight: 600; font-size: 0.95rem;">🚫 DF Flag Result</div>
            <div style="font-size: 0.85rem; margin-top: 0.25rem;">{df_result.error}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="validation-pass">
            <div style="font-weight: 600; font-size: 0.95rem;">✅ DF Flag Result</div>
            <div style="font-size: 0.85rem; margin-top: 0.25rem;">
                Packet ({payload_size + IPV4_HEADER_SIZE}B) fits through all hops without fragmentation.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Edge cases
    st.markdown("#### 🔬 Edge Case Scenarios")

    edge_cases = [
        ("Minimum MTU (68B)", 4000, [68]),
        ("Single fragment (large MTU)", 100, [1500]),
        ("Exact fit (no fragmentation)", 1480, [1500]),
        ("Off-by-one (needs 1 extra fragment)", 1481, [1500]),
        ("Very small MTU (76B)", 4000, [76]),
        ("Progressive reduction", 4000, [1500, 1000, 500, 200]),
        ("Increasing MTU path", 4000, [500, 1500]),
        ("Same MTU all hops", 4000, [620, 620, 620]),
    ]

    edge_data = []
    for name, payload, path in edge_cases:
        r = FragmentationEngine.fragment_packet(payload, path)
        v = FragmentationEngine.validate_fragments(r)
        edge_data.append({
            "Scenario": name,
            "Payload": f"{payload}B",
            "MTU Path": " → ".join(map(str, path)),
            "Fragments": r.total_fragments if not r.error else "Error",
            "Overhead": f"{r.total_header_overhead}B" if not r.error else "—",
            "Valid": "✅" if v.is_valid else "❌",
        })

    edge_df = pd.DataFrame(edge_data)
    st.dataframe(edge_df, use_container_width=True, height=340)


# ─── TAB 6: Theory ──────────────────────────────────────────────
with tab6:
    st.markdown("### 📐 IPv4 Fragmentation Theory")

    st.markdown("""
    <div class="section-card">
        <h3 style="margin-top:0; color: #1E293B;">📦 How IPv4 Fragmentation Works</h3>
        <p>When an IPv4 packet is larger than the <b>Maximum Transmission Unit (MTU)</b> of the outgoing link,
        the router must <b>fragment</b> the packet into smaller pieces that fit within the MTU.</p>

        <h4>Key Rules (RFC 791):</h4>
        <ol>
            <li><b>Header Size:</b> Each fragment gets its own 20-byte IPv4 header (no options assumed)</li>
            <li><b>8-Byte Alignment:</b> All fragment payloads except the last must be a multiple of 8 bytes</li>
            <li><b>Fragment Offset:</b> Measured in 8-byte units (actual_byte_offset ÷ 8)</li>
            <li><b>More Fragments (MF) flag:</b> Set to 1 on all fragments except the last one</li>
            <li><b>Don't Fragment (DF) flag:</b> If set, packet is dropped instead of fragmented</li>
            <li><b>Reassembly:</b> Only the destination host reassembles — intermediate routers don't</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section-card">
        <h3 style="margin-top:0; color: #1E293B;">🔢 Fragmentation Formula</h3>
        <div style="font-family: 'JetBrains Mono', monospace; background: #F8FAFC;
                    padding: 1.5rem; border-radius: 8px; font-size: 0.9rem; line-height: 2;">
            <div><b>max_payload</b> = MTU − 20 (IPv4 header)</div>
            <div><b>aligned_payload</b> = floor(max_payload ÷ 8) × 8</div>
            <div><b>num_fragments</b> = ceil(original_payload ÷ aligned_payload)</div>
            <div><b>fragment_offset</b> = byte_position ÷ 8</div>
            <div><b>total_overhead</b> = num_fragments × 20 bytes</div>
            <div><b>overhead_%</b> = (total_overhead ÷ original_payload) × 100</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section-card">
        <h3 style="margin-top:0; color: #1E293B;">📝 Worked Example</h3>
        <p><b>Given:</b> Payload = 4000 bytes, MTU Path = [1500, 620, 400]</p>

        <h4>Hop 1 — MTU 1500:</h4>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; padding-left: 1rem; line-height: 1.8;">
            Original packet: 4000 + 20 = 4020B (exceeds 1500B MTU)<br>
            max_payload = 1500 − 20 = 1480B<br>
            aligned_payload = floor(1480 ÷ 8) × 8 = 1480B ✓<br>
            Fragment 1: 1480B payload, offset=0, MF=1<br>
            Fragment 2: 1480B payload, offset=185 (1480÷8), MF=1<br>
            Fragment 3: 1040B payload, offset=370 (2960÷8), MF=0<br>
            → 3 fragments after Hop 1
        </div>

        <h4>Hop 2 — MTU 620:</h4>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; padding-left: 1rem; line-height: 1.8;">
            max_payload = 620 − 20 = 600B<br>
            aligned_payload = floor(600 ÷ 8) × 8 = 600B ✓<br>
            Each 1480B fragment → 3 sub-fragments (600 + 600 + 280)<br>
            The 1040B fragment → 2 sub-fragments (600 + 440)<br>
            → 8 fragments after Hop 2
        </div>

        <h4>Hop 3 — MTU 400:</h4>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; padding-left: 1rem; line-height: 1.8;">
            max_payload = 400 − 20 = 380B<br>
            aligned_payload = floor(380 ÷ 8) × 8 = 376B ✓<br>
            Further fragmentation of 600B fragments (376 + 224) and 440B (376 + 64)...<br>
            → 14 fragments after Hop 3
        </div>

        <p style="margin-top: 1rem; color: #64748B;">
            <b>Key insight:</b> As MTU decreases, fragment count increases dramatically,
            and IPv4 header overhead grows proportionally (each new fragment needs its own 20-byte header).
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section-card">
        <h3 style="margin-top:0; color: #1E293B;">📊 Why Fragmentation Matters</h3>
        <ul>
            <li><b>Performance:</b> Each fragment adds 20 bytes of overhead — smaller MTUs = more waste</li>
            <li><b>Reliability:</b> If any fragment is lost, the entire original packet must be retransmitted</li>
            <li><b>Security:</b> Fragment-based attacks (e.g., Teardrop, overlapping fragments) exploit reassembly bugs</li>
            <li><b>Modern approach:</b> Path MTU Discovery (PMTUD) avoids fragmentation by probing for the minimum MTU along the path</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# ─── Footer ──────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    <b>NetVista 3D</b> — IPv4 Fragmentation Simulator<br>
    Jay Navadiya (25CS052) | ITUC201 – Fundamentals of Computer Networks 2026-27<br>
    Built with Python + Streamlit | RFC 791 Compliant
</div>
""", unsafe_allow_html=True)
