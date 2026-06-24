import streamlit as st

import requests
import os
import pandas as pd
import plotly.express as px
from config import BACKEND_API_URL  # type: ignore

st.set_page_config(
    page_title="AI Policy Recommendations - CDIP",
    page_icon="📋",
    layout="wide"
)

# Load CSS stylesheet
css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "styles.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Page header
st.markdown("<h1>📋 AI Decision Recommendations Engine</h1>", unsafe_allow_html=True)
st.markdown("### Ranked neighborhood priority recommendations, specific policy actions, and municipal resource mapping")

# Session state status tracker
if "rec_status" not in st.session_state:
    st.session_state.rec_status = {}

# Fetch prioritized recommendations from the backend API
def fetch_prioritized_recommendations():
    try:
        response = requests.get(f"{BACKEND_API_URL}/recommendations")
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

recommendations = fetch_prioritized_recommendations()

if not recommendations:
    st.info("💡 No community metrics are currently indexed. Please navigate to the **Data Upload** page in the sidebar and upload a dataset first.")
else:
    # 1. Overview banner explaining formula
    st.markdown(
        """
        <div class="glass-card">
            <h4>🛡️ Solution Architect Risk Model</h4>
            <p>
                Wards are sorted by a multi-indicator priority risk index computed as:<br>
                <code style="background: rgba(255,255,255,0.08); padding: 4px 8px; border-radius: 4px; color:#A5B4FC;">
                    Risk Score = 0.4 * Complaints + 0.3 * Traffic Score + 0.3 * AQI
                </code>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. Columns layout: Risk Score Chart on left, policy details on right
    col_chart, col_policy = st.columns([2, 3])

    with col_chart:
        st.markdown("### 📊 Calculated Risk Index by Ward")
        
        # Prepare dataframe for Plotly rendering
        df_recs = pd.DataFrame(recommendations)
        df_chart = df_recs.sort_values(by="risk_score", ascending=True)
        
        fig = px.bar(
            df_chart,
            x="risk_score",
            y="area",
            orientation="h",
            color="risk_score",
            color_continuous_scale="Turbo",
            labels={"risk_score": "Risk Index Score", "area": "Ward Neighborhood"},
            title="Vulnerability Ranking (Higher Score = Priority Dispatch)"
        )
        
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#F3F4F6",
            xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(showgrid=False),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Display small index guidelines table
        st.markdown("##### 📝 Metric Reference Details")
        ref_df = df_recs[["rank", "area", "risk_score", "complaints", "traffic", "aqi"]].copy()
        ref_df.columns = ["Rank", "Neighborhood", "Risk Score", "Complaints", "Traffic Level", "AQI"]
        st.dataframe(ref_df, use_container_width=True, hide_index=True)

    with col_policy:
        st.markdown("### 📋 AI Directives & Resource Allocation")
        
        for item in recommendations:
            area = item["area"]
            score = item["risk_score"]
            rank = item["rank"]
            traffic = item["traffic"]
            complaints = item["complaints"]
            aqi = item["aqi"]
            rec_actions = item["recommended_actions"]
            res_alloc = item["resource_allocation"]
            
            rec_id = f"rec_eng_{area.lower().replace(' ', '_')}"
            
            # Initialize status if not present
            if rec_id not in st.session_state.rec_status:
                st.session_state.rec_status[rec_id] = "Pending Review"

            status = st.session_state.rec_status[rec_id]
            
            # Select color based on risk score severity
            if score >= 80:
                score_color = "#EF4444"  # Critical Risk Red
                score_badge = '<span class="status-badge danger">CRITICAL RISK</span>'
            elif score >= 50:
                score_color = "#F59E0B"  # Moderate Risk Orange
                score_badge = '<span class="status-badge warning">MEDIUM RISK</span>'
            else:
                score_color = "#10B981"  # Low Risk Green
                score_badge = '<span class="status-badge success">LOW RISK</span>'
                
            # Status Badge indicator
            if status == "Approved":
                status_html = '<span class="status-badge success">✅ APPROVED</span>'
                card_border = "#10B981"
            elif status == "Deferred / Flagged":
                status_html = '<span class="status-badge warning">⚠️ DEFERRED</span>'
                card_border = "#F59E0B"
            else:
                status_html = '<span class="status-badge info">⏳ PENDING</span>'
                card_border = "rgba(255, 255, 255, 0.08)"

            # Display card details
            st.markdown(
                f"""
                <div class="glass-card" style="border-left: 6px solid {score_color}; border-top: 1px solid {card_border}; padding: 20px; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <h4 style="margin: 0px; color: #FFF;">Rank #{rank} - {area}</h4>
                        <div style="display: flex; gap: 8px;">
                            {score_badge}
                            {status_html}
                        </div>
                    </div>
                    <div style="display: flex; gap: 24px; margin-bottom: 14px; background: rgba(0,0,0,0.2); padding: 8px 12px; border-radius: 6px;">
                        <span style="font-size:12.5px; color:#9CA3AF;"><b>Risk Score:</b> <span style="color:#FFF;">{score:.1f}</span></span>
                        <span style="font-size:12.5px; color:#9CA3AF;"><b>Complaints:</b> <span style="color:#FFF;">{complaints}</span></span>
                        <span style="font-size:12.5px; color:#9CA3AF;"><b>Traffic:</b> <span style="color:#FFF;">{traffic}</span></span>
                        <span style="font-size:12.5px; color:#9CA3AF;"><b>AQI:</b> <span style="color:#FFF;">{aqi}</span></span>
                    </div>
                    <div style="margin-bottom: 12px;">
                        <p style="font-size:13.5px; color:#E5E7EB; margin-bottom: 4px;">🎯 <b>Recommended Actions:</b></p>
                        <p style="font-size:13.5px; color:#D1D5DB; margin: 0px; line-height: 1.5;">{rec_actions}</p>
                    </div>
                    <div style="background: rgba(99, 102, 241, 0.06); border: 1px solid rgba(99, 102, 241, 0.15); padding: 12px; border-radius: 6px;">
                        <p style="font-size:13.5px; color:#A5B4FC; margin-bottom: 4px;">💰 <b>Resource Allocation Suggestion:</b></p>
                        <p style="font-size:13.5px; color:#E0E7FF; margin: 0px; line-height: 1.5; font-weight: 500;">{res_alloc}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Card Action Toggles
            c_app, c_def, c_res, _ = st.columns([1, 1, 1, 3])
            with c_app:
                if st.button("Approve Plan", key=f"btn_app_{rec_id}"):
                    st.session_state.rec_status[rec_id] = "Approved"
                    st.rerun()
            with c_def:
                if st.button("Defer Plan", key=f"btn_def_{rec_id}"):
                    st.session_state.rec_status[rec_id] = "Deferred / Flagged"
                    st.rerun()
            with c_res:
                if st.button("Reset Plan", key=f"btn_res_{rec_id}"):
                    st.session_state.rec_status[rec_id] = "Pending Review"
                    st.rerun()
                    
            st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 24px 0px;' />", unsafe_allow_html=True)
