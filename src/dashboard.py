"""
Streamlit dashboard for focus session analytics.

Run with: .venv/bin/python -m streamlit run src/dashboard.py
"""

import altair as alt
import pandas as pd
import streamlit as st

from src.session_logger import CSV_HEADERS, ensure_sessions_csv, get_csv_path


DATA_FILE = get_csv_path()
CHART_HEIGHT = 280

# Clip any internal chart overflow without blocking page scroll.
CHART_CONTAINER_CSS = """
<style>
div[data-testid="stVegaLiteChart"],
div[data-testid="stVegaLiteChart"] .vega-embed {
    overflow: hidden !important;
}
</style>
"""


def _finalize_chart(chart: alt.Chart) -> alt.Chart:
    """Lock chart size and disable built-in pan/zoom interactions."""
    return (
        chart
        .properties(
            width="container",
            height=CHART_HEIGHT,
            padding={"left": 10, "top": 10, "right": 10, "bottom": 10},
            usermeta={"embedOptions": {"actions": False}},
        )
        .configure_view(strokeWidth=0)
        .configure_axis(labelFontSize=12, titleFontSize=12)
    )


def session_line_chart(
    data: pd.DataFrame,
    y: str,
    y_title: str,
    color: str,
    y_domain: tuple[float, float] | None = None,
) -> alt.Chart:
    """Line chart with readable axis labels and horizontal session ticks."""
    y_enc = alt.Y(y, title=y_title)
    if y_domain is not None:
        y_enc = alt.Y(y, title=y_title, scale=alt.Scale(domain=list(y_domain)))

    return _finalize_chart(
        alt.Chart(data)
        .mark_line(color=color, point=True)
        .encode(
            x=alt.X("Session:O", title="Session", axis=alt.Axis(labelAngle=0)),
            y=y_enc,
        )
    )


def session_bar_chart(
    data: pd.DataFrame,
    y: str,
    y_title: str,
    color: str,
) -> alt.Chart:
    """Bar chart with readable axis labels and horizontal session ticks."""
    return _finalize_chart(
        alt.Chart(data)
        .mark_bar(color=color)
        .encode(
            x=alt.X("Session:O", title="Session", axis=alt.Axis(labelAngle=0)),
            y=alt.Y(y, title=y_title),
        )
    )


def category_bar_chart(
    data: pd.DataFrame,
    x: str,
    y: str,
    x_title: str,
    y_title: str,
    color: str,
) -> alt.Chart:
    """Categorical bar chart with horizontal x-axis labels."""
    return _finalize_chart(
        alt.Chart(data)
        .mark_bar(color=color)
        .encode(
            x=alt.X(f"{x}:N", title=x_title, axis=alt.Axis(labelAngle=0)),
            y=alt.Y(f"{y}:Q", title=y_title),
        )
    )


def load_data() -> pd.DataFrame | None:
    """Load sessions from CSV file."""
    if not DATA_FILE.exists():
        return None

    try:
        ensure_sessions_csv(DATA_FILE)
        df = pd.read_csv(DATA_FILE)
        if df.empty:
            return None

        for column in CSV_HEADERS:
            if column not in df.columns:
                default = 0 if column != "timestamp" else ""
                df[column] = default

        return df[CSV_HEADERS]
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

    st.markdown(CHART_CONTAINER_CSS, unsafe_allow_html=True)
    
    # Title
    st.title("🎯 Focus Session Dashboard")
    
    # Load data
    df = load_data()
    
    if df is None:
        st.warning("No session data found.")
        st.info(f"Run some focus sessions first. Data will be saved to `{DATA_FILE}`")
        return
    
    # Check if optional columns exist (for backwards compatibility)
    has_risk_data = "peak_risk_score" in df.columns and "avg_risk_score" in df.columns
    has_gaze_data = "gaze_distractions" in df.columns and "gaze_away_seconds" in df.columns
    
    # Calculate metrics
    total_sessions = len(df)
    total_focus_time = df["duration_seconds"].sum()
    avg_score = df["focus_score"].mean()
    avg_distractions = df["distractions"].mean()
    total_phone_time = df["phone_visible_seconds"].sum()
    
    if has_gaze_data:
        avg_gaze_away = df["gaze_away_seconds"].mean()
        avg_gaze_events = df["gaze_distractions"].mean()
    
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
        st.metric(
            "Avg Focus Score",
            f"{avg_score:.1f}",
            help="0–100 score from phone time, phone distractions, gaze events, and gaze-away time.",
        )
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
    st.caption(
        "Score starts at 100 and subtracts penalties for phone use (major), "
        "phone distractions (major), gaze-away events (minor), and gaze-away time (minor)."
    )

    chart_df = df.copy()
    chart_df["Session"] = [str(i) for i in range(1, len(df) + 1)]
    chart_df["Focus Score"] = chart_df["focus_score"]
    chart_df["Phone Time (s)"] = chart_df["phone_visible_seconds"]
    chart_df["Distractions"] = chart_df["distractions"]
    chart_df["Peak Risk"] = chart_df["peak_risk_score"]
    chart_df["Avg Risk"] = chart_df["avg_risk_score"]
    chart_df["Gaze Away (s)"] = chart_df["gaze_away_seconds"]
    chart_df["Gaze Events"] = chart_df["gaze_distractions"]
    
    st.altair_chart(
        session_line_chart(chart_df, "Focus Score", "Focus Score", "#4CAF50", y_domain=(0, 100)),
        use_container_width=True,
        height=CHART_HEIGHT,
    )
    
    # Two columns for phone time and distractions
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Phone Time per Session")
        st.altair_chart(
            session_bar_chart(chart_df, "Phone Time (s)", "Seconds", "#2196F3"),
            use_container_width=True,
            height=CHART_HEIGHT,
        )
    
    with col_right:
        st.subheader("Distractions per Session")
        st.altair_chart(
            session_bar_chart(chart_df, "Distractions", "Count", "#FF9800"),
            use_container_width=True,
            height=CHART_HEIGHT,
        )
    
    # Risk charts (if data available)
    if has_risk_data:
        st.divider()
        st.subheader("Risk Analysis")
        
        col_risk1, col_risk2 = st.columns(2)
        
        with col_risk1:
            st.write("**Peak Risk Score per Session**")
            st.altair_chart(
                session_bar_chart(chart_df, "Peak Risk", "Risk Score", "#F44336"),
                use_container_width=True,
            height=CHART_HEIGHT,
            )
        
        with col_risk2:
            st.write("**Average Risk Score per Session**")
            st.altair_chart(
                session_line_chart(chart_df, "Avg Risk", "Risk Score", "#FF5722", y_domain=(0, 100)),
                use_container_width=True,
            height=CHART_HEIGHT,
            )
        
        # Risk level distribution
        def categorize_risk(score):
            if score <= 33:
                return "LOW"
            elif score <= 66:
                return "MEDIUM"
            else:
                return "HIGH"
        
        risk_counts = df["peak_risk_score"].apply(categorize_risk).value_counts()
        risk_dist = pd.DataFrame({
            "Risk Level": ["LOW", "MEDIUM", "HIGH"],
            "Sessions": [int(risk_counts.get(level, 0)) for level in ["LOW", "MEDIUM", "HIGH"]],
        })
        
        col_dist, col_info = st.columns([1, 2])
        with col_dist:
            st.write("**Peak Risk Distribution**")
            st.altair_chart(
                category_bar_chart(
                    risk_dist,
                    x="Risk Level",
                    y="Sessions",
                    x_title="Risk Level",
                    y_title="Sessions",
                    color="#2196F3",
                ),
                use_container_width=True,
            height=CHART_HEIGHT,
            )
        
        with col_info:
            st.write("**Risk Level Guide**")
            st.markdown("""
            - 🟢 **LOW (0-33)**: Focused and unlikely to be distracted
            - 🟡 **MEDIUM (34-66)**: Some risk factors present
            - 🔴 **HIGH (67-100)**: High likelihood of distraction
            """)

        has_recorded_risk = (df["peak_risk_score"] > 0).any() or (df["avg_risk_score"] > 0).any()
        if has_recorded_risk and len(df) >= 2:
            st.write("**Risk trends (last session vs previous)**")
            tcol1, tcol2 = st.columns(2)
            peak_delta = int(df["peak_risk_score"].iloc[-1] - df["peak_risk_score"].iloc[-2])
            avg_delta = int(df["avg_risk_score"].iloc[-1] - df["avg_risk_score"].iloc[-2])
            with tcol1:
                st.metric("Peak risk change", int(df["peak_risk_score"].iloc[-1]), delta=peak_delta)
            with tcol2:
                st.metric("Avg risk change", int(df["avg_risk_score"].iloc[-1]), delta=avg_delta)

    if has_gaze_data and (df["gaze_away_seconds"] > 0).any():
        st.divider()
        st.subheader("Gaze Analysis")

        gcol1, gcol2 = st.columns(2)
        with gcol1:
            st.metric("Avg Gaze Away", format_duration(avg_gaze_away))
        with gcol2:
            st.metric("Avg Gaze Distractions", f"{avg_gaze_events:.1f}")

        gchart1, gchart2 = st.columns(2)
        with gchart1:
            st.write("**Gaze Away Time per Session**")
            st.altair_chart(
                session_bar_chart(chart_df, "Gaze Away (s)", "Seconds", "#9C27B0"),
                use_container_width=True,
            height=CHART_HEIGHT,
            )
        with gchart2:
            st.write("**Gaze Distractions per Session**")
            st.altair_chart(
                session_bar_chart(chart_df, "Gaze Events", "Count", "#673AB7"),
                use_container_width=True,
            height=CHART_HEIGHT,
            )

        if len(df) >= 2:
            gaze_delta = float(df["gaze_away_seconds"].iloc[-1] - df["gaze_away_seconds"].iloc[-2])
            event_delta = int(df["gaze_distractions"].iloc[-1] - df["gaze_distractions"].iloc[-2])
            tcol1, tcol2 = st.columns(2)
            with tcol1:
                st.metric(
                    "Gaze away change",
                    format_duration(df["gaze_away_seconds"].iloc[-1]),
                    delta=f"{gaze_delta:.0f}s",
                )
            with tcol2:
                st.metric(
                    "Gaze events change",
                    int(df["gaze_distractions"].iloc[-1]),
                    delta=event_delta,
                )
    
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
            help="Phone + gaze penalties applied; see chart caption above.",
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

    if has_gaze_data:
        display_cols.extend(["gaze_distractions", "gaze_away_seconds"])
        column_config["gaze_distractions"] = "Gaze Events"
        column_config["gaze_away_seconds"] = st.column_config.NumberColumn(
            "Gaze Away (s)",
            format="%.1f",
        )
    
    st.dataframe(
        display_df[display_cols],
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
    )


if __name__ == "__main__":
    main()
