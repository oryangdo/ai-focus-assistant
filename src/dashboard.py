"""
Streamlit dashboard for focus session analytics.

Run with: .venv/bin/python -m streamlit run src/dashboard.py
"""

import pandas as pd
import streamlit as st
from pathlib import Path


DATA_FILE = Path(__file__).parent.parent / "data" / "sessions.csv"


def load_data() -> pd.DataFrame | None:
    """Load sessions from CSV file."""
    if not DATA_FILE.exists():
        return None
    
    try:
        df = pd.read_csv(DATA_FILE)
        if df.empty:
            return None
        return df
    except Exception:
        return None


def format_duration(seconds: float) -> str:
    """Format seconds as H:MM or M:SS."""
    if seconds >= 3600:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        mins, secs = divmod(int(seconds), 60)
        return f"{mins}:{secs:02d}"


def main():
    # Page config
    st.set_page_config(
        page_title="Focus Dashboard",
        page_icon="🎯",
        layout="wide",
    )
    
    # Title
    st.title("🎯 Focus Session Dashboard")
    
    # Load data
    df = load_data()
    
    if df is None:
        st.warning("No session data found.")
        st.info(f"Run some focus sessions first. Data will be saved to `{DATA_FILE}`")
        return
    
    # Check if risk columns exist (for backwards compatibility)
    has_risk_data = "peak_risk_score" in df.columns and "avg_risk_score" in df.columns
    
    # Calculate metrics
    total_sessions = len(df)
    total_focus_time = df["duration_seconds"].sum()
    avg_score = df["focus_score"].mean()
    avg_distractions = df["distractions"].mean()
    total_phone_time = df["phone_visible_seconds"].sum()
    
    # Risk metrics (if available)
    if has_risk_data:
        avg_peak_risk = df["peak_risk_score"].mean()
        avg_risk = df["avg_risk_score"].mean()
    
    # Metrics row
    st.subheader("Overview")
    if has_risk_data:
        col1, col2, col3, col4, col5, col6 = st.columns(6)
    else:
        col1, col2, col3, col4, col5 = st.columns(5)
        col6 = None
    
    with col1:
        st.metric("Total Sessions", total_sessions)
    with col2:
        st.metric("Total Focus Time", format_duration(total_focus_time))
    with col3:
        st.metric("Avg Focus Score", f"{avg_score:.1f}")
    with col4:
        st.metric("Avg Distractions", f"{avg_distractions:.1f}")
    with col5:
        st.metric("Total Phone Time", format_duration(total_phone_time))
    if col6 and has_risk_data:
        with col6:
            st.metric("Avg Peak Risk", f"{avg_peak_risk:.0f}")
    
    st.divider()
    
    # Charts
    st.subheader("Focus Score Over Sessions")
    
    chart_df = df.copy()
    chart_df["Session"] = range(1, len(df) + 1)
    
    st.line_chart(
        chart_df,
        x="Session",
        y="focus_score",
        color="#4CAF50",
    )
    
    # Two columns for phone time and distractions
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Phone Time per Session")
        st.bar_chart(
            chart_df,
            x="Session",
            y="phone_visible_seconds",
            color="#2196F3",
        )
    
    with col_right:
        st.subheader("Distractions per Session")
        st.bar_chart(
            chart_df,
            x="Session",
            y="distractions",
            color="#FF9800",
        )
    
    # Risk charts (if data available)
    if has_risk_data:
        st.divider()
        st.subheader("Risk Analysis")
        
        col_risk1, col_risk2 = st.columns(2)
        
        with col_risk1:
            st.write("**Peak Risk Score per Session**")
            st.bar_chart(
                chart_df,
                x="Session",
                y="peak_risk_score",
                color="#F44336",
            )
        
        with col_risk2:
            st.write("**Average Risk Score per Session**")
            st.line_chart(
                chart_df,
                x="Session",
                y="avg_risk_score",
                color="#FF5722",
            )
        
        # Risk level distribution
        def categorize_risk(score):
            if score <= 33:
                return "LOW"
            elif score <= 66:
                return "MEDIUM"
            else:
                return "HIGH"
        
        risk_dist = df["peak_risk_score"].apply(categorize_risk).value_counts()
        
        col_dist, col_info = st.columns([1, 2])
        with col_dist:
            st.write("**Peak Risk Distribution**")
            st.bar_chart(risk_dist)
        
        with col_info:
            st.write("**Risk Level Guide**")
            st.markdown("""
            - 🟢 **LOW (0-33)**: Focused and unlikely to be distracted
            - 🟡 **MEDIUM (34-66)**: Some risk factors present
            - 🔴 **HIGH (67-100)**: High likelihood of distraction
            """)
    
    st.divider()
    
    # Raw data table
    st.subheader("Session History")
    
    display_df = df.copy()
    display_df["duration"] = display_df["duration_seconds"].apply(format_duration)
    display_df["phone_time"] = display_df["phone_visible_seconds"].apply(format_duration)
    
    # Build column list based on available data
    display_cols = ["timestamp", "duration", "distractions", "phone_time", "focus_score"]
    column_config = {
        "timestamp": "Timestamp",
        "duration": "Duration",
        "distractions": "Distractions",
        "phone_time": "Phone Time",
        "focus_score": st.column_config.ProgressColumn(
            "Focus Score",
            min_value=0,
            max_value=100,
            format="%d",
        ),
    }
    
    if has_risk_data:
        display_cols.extend(["peak_risk_score", "avg_risk_score"])
        column_config["peak_risk_score"] = st.column_config.ProgressColumn(
            "Peak Risk",
            min_value=0,
            max_value=100,
            format="%d",
        )
        column_config["avg_risk_score"] = st.column_config.ProgressColumn(
            "Avg Risk",
            min_value=0,
            max_value=100,
            format="%d",
        )
    
    st.dataframe(
        display_df[display_cols],
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
    )


if __name__ == "__main__":
    main()
