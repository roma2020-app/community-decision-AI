import streamlit as st
import requests
import os
import pandas as pd
import plotly.express as px
from config import BACKEND_API_URL  # type: ignore

st.set_page_config(
    page_title="Risk Analysis & Insights - CDIP",
    page_icon="💡",
    layout="wide"
)

# Load CSS stylesheet
css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "styles.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Page header
st.markdown("<h1>💡 AI Risk & Insights Engine</h1>", unsafe_allow_html=True)
st.markdown("### Emerging trends, neighborhood vulnerability prioritization, and resource allocation actions")

# Helper block for fetching insights
def fetch_insights():
    try:
        response = requests.get(f"{BACKEND_API_URL}/insights")
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

# Action row: Generate button
col_act1, col_act2 = st.columns([1, 4])
with col_act1:
    if st.button("🔄 Generate AI Insights", type="primary"):
        with st.spinner("Analyzing data and generating insights..."):
            try:
                response = requests.post(f"{BACKEND_API_URL}/insights/generate")
                if response.status_code == 201:
                    st.success("Successfully generated new insights!")
                    st.rerun()
                else:
                    detail = response.json().get("detail", "Error occurred.")
                    st.error(f"Generation failed: {detail}")
            except Exception as e:
                st.error(f"Failed to connect to API: {str(e)}")

# Get current insights
insights = fetch_insights()

if not insights:
    st.info("💡 No insights available. Click **'Generate AI Insights'** above to trigger analysis on your AlloyDB records.")
else:
    # Separate City-wide Summary from localized neighborhood insights
    city_wide = [item for item in insights if item["area"].lower() == "city-wide summary"]
    local_insights = [item for item in insights if item["area"].lower() != "city-wide summary"]

    # 1. Display City-Wide Macro card if exists
    if city_wide:
        cw = city_wide[0]
        st.markdown(
            f"""
            <div class="glass-card" style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(30, 41, 59, 0.8) 100%); border-left: 6px solid #6366F1;">
                <h4 style="margin:0px 0px 8px 0px; color:#A5B4FC;">🏙️ {cw['area']}</h4>
                <p style="font-size: 15px; line-height: 1.6; margin-bottom: 12px;"><b>Analysis</b>: {cw['insight']}</p>
                <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px;">
                    <p style="font-size: 14px; margin:0px; color:#E0E7FF;"><b>Action Plan & Sustainability</b>: {cw['recommendation']}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 2. Grid layout: Chart on left, individual cards on right
    col_chart, col_cards = st.columns([2, 3])

    with col_chart:
        st.markdown("### 📊 Priority Ranking Index")
        if local_insights:
            # Prepare dataframe for Plotly
            chart_df = pd.DataFrame(local_insights)
            chart_df = chart_df.sort_values(by="priority_score", ascending=True)

            fig = px.bar(
                chart_df,
                x="priority_score",
                y="area",
                orientation="h",
                title="Neighborhood Priority Score (Higher = Urgent Attention)",
                color="priority_score",
                color_continuous_scale="Viridis",
                labels={"priority_score": "Priority Index (0-10)", "area": "Neighborhood"},
                height=450
            )
            # Style Plotly figure to fit dark theme
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#F3F4F6",
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(showgrid=False),
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No localized records available for chart rendering.")

    with col_cards:
        st.markdown("### 🚨 Neighborhood Risk Profiles")
        
        # Display localized risk cards
        for idx, item in enumerate(local_insights):
            score = item["priority_score"]
            # Color coding for severity badges
            if score >= 7.0:
                badge_class = "danger"
                border_color = "#EF4444"
            elif score >= 4.0:
                badge_class = "warning"
                border_color = "#F59E0B"
            else:
                badge_class = "success"
                border_color = "#10B981"

            st.markdown(
                f"""
                <div class="glass-card" style="border-left: 5px solid {border_color}; padding: 18px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <h5 style="margin:0px; font-weight:700; color:#FFF;">📍 {item['area']}</h5>
                        <span class="status-badge {badge_class}">Priority: {score:.1f}</span>
                    </div>
                    <p style="font-size: 13px; color: #D1D5DB; margin-bottom: 8px;"><b>AI Insight</b>: {item['insight']}</p>
                    <p style="font-size: 13px; color: #A5B4FC; margin:0px;">💡 <b>Recommendations</b>: {item['recommendation']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
