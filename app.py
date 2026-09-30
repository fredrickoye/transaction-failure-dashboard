"""
Transaction Failure Root-Cause Dashboard
Streamlit interactive dashboard
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="Transaction Failure Dashboard",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Data ----------
@st.cache_data
def load_data():
    path = Path(__file__).parent / "data" / "transaction_failures.csv"
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df["hour"] = df["timestamp"].dt.hour
    df["date"] = df["timestamp"].dt.date
    df["is_failed"] = (df["status"] == "failed").astype(int)
    return df

df = load_data()

# ---------- Sidebar ----------
st.sidebar.title("Filters")
providers = st.sidebar.multiselect(
    "Payment Provider",
    options=sorted(df["payment_provider"].unique()),
    default=sorted(df["payment_provider"].unique())
)
channels = st.sidebar.multiselect(
    "Channel",
    options=sorted(df["channel"].unique()),
    default=sorted(df["channel"].unique())
)

filtered = df[
    (df["payment_provider"].isin(providers)) &
    (df["channel"].isin(channels))
]

# ---------- Header ----------
st.title("💳 Transaction Failure Root-Cause Dashboard")
st.markdown("""
**Problem:** Every failed payment is a lost conversion and a support ticket.  
This dashboard surfaces *why* transactions fail across providers, channels and time of day — so operations can act on patterns instead of individual tickets.

*Synthetic data only. Figures illustrate methodology — they do **not** represent real-world performance of any payment provider. Provider names are fictional (A / B / C).*
""")

# ---------- KPIs ----------
total = len(filtered)
failed = filtered["is_failed"].sum()
fail_rate = failed / total * 100 if total else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Transactions", f"{total:,}")
col2.metric("Failed Transactions", f"{failed:,}")
col3.metric("Failure Rate", f"{fail_rate:.1f}%")
col4.metric("Date Range", f"{filtered['timestamp'].min().date()} → {filtered['timestamp'].max().date()}")

st.divider()

# ---------- Charts ----------
left, right = st.columns(2)

with left:
    st.subheader("Failure Rate by Provider")
    by_prov = filtered.groupby("payment_provider")["is_failed"].mean().reset_index()
    by_prov["failure_rate_pct"] = by_prov["is_failed"] * 100
    fig = px.bar(
        by_prov.sort_values("failure_rate_pct", ascending=False),
        x="payment_provider", y="failure_rate_pct",
        text=by_prov.sort_values("failure_rate_pct", ascending=False)["failure_rate_pct"].round(1).astype(str) + "%",
        color="failure_rate_pct", color_continuous_scale="Reds",
        labels={"payment_provider": "Provider", "failure_rate_pct": "Failure Rate (%)"}
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, height=380, margin=dict(t=30))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Failure Rate by Channel")
    by_chan = filtered.groupby("channel")["is_failed"].mean().reset_index()
    by_chan["failure_rate_pct"] = by_chan["is_failed"] * 100
    fig = px.bar(
        by_chan.sort_values("failure_rate_pct", ascending=False),
        x="channel", y="failure_rate_pct",
        text=by_chan.sort_values("failure_rate_pct", ascending=False)["failure_rate_pct"].round(1).astype(str) + "%",
        color="failure_rate_pct", color_continuous_scale="Oranges",
        labels={"channel": "Channel", "failure_rate_pct": "Failure Rate (%)"}
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, height=380, margin=dict(t=30))
    st.plotly_chart(fig, use_container_width=True)

left2, right2 = st.columns(2)

with left2:
    st.subheader("Top Failure Reasons")
    reasons = filtered[filtered["status"] == "failed"]["failure_reason"].value_counts().reset_index()
    reasons.columns = ["reason", "count"]
    fig = px.pie(reasons, names="reason", values="count", hole=0.4)
    fig.update_layout(height=380, margin=dict(t=30))
    st.plotly_chart(fig, use_container_width=True)

with right2:
    st.subheader("Failure Rate by Hour of Day")
    hourly = filtered.groupby("hour")["is_failed"].mean().reset_index()
    hourly["failure_rate_pct"] = hourly["is_failed"] * 100
    fig = px.line(
        hourly, x="hour", y="failure_rate_pct",
        markers=True,
        labels={"hour": "Hour of Day", "failure_rate_pct": "Failure Rate (%)"}
    )
    fig.update_layout(height=380, margin=dict(t=30), xaxis=dict(dtick=2))
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Transaction Amount Distribution by Status")
fig = px.box(
    filtered, x="status", y="amount",
    color="status",
    labels={"status": "Status", "amount": "Amount (NGN)"},
    points=False
)
fig.update_layout(height=360, showlegend=False, margin=dict(t=20))
st.plotly_chart(fig, use_container_width=True)

# ---------- Insights ----------
st.divider()
st.subheader("Key Insights & Recommendations")
st.markdown("""
- **Provider B** shows the highest failure rate → investigate timeouts/webhooks and consider routing rules.
- **USSD** is the weakest channel → review session handling and timeout settings.
- Failures spike in the **early morning (00:00–05:00)** → adjust monitoring coverage.
- High-value transactions fail slightly more often → add extra confirmation or alternative routing for large amounts.
""")

st.caption("Built by [Omololu Oyewumi](https://www.linkedin.com/in/omololu-oyewumi-4aa682331) · Synthetic data only")
