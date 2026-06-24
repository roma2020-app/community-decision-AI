import streamlit as st
import requests
import os
import pandas as pd
import plotly.express as px
from config import BACKEND_API_URL  # type: ignore

st.set_page_config(
    page_title="Dashboard - CDIP",
    page_icon="📊",
    layout="wide"
)

# Load CSS stylesheet
css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "styles.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Page header
st.markdown("<h1 style='font-size: 2.6rem; font-weight: 800; line-height: 1.2; margin-bottom: 8px; background: linear-gradient(135deg, #FFFFFF 30%, #A5B4FC 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>Community Command Center</h1>", unsafe_allow_html=True)
st.markdown("### Real-time city indicators, environmental indices, and traffic bottlenecks")

# Fetch database records from backend API
def fetch_community_data():
    try:
        response = requests.get(f"{BACKEND_API_URL}/datasets/records")
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

# Fetch decision recommendations from backend API
def fetch_recommendations():
    try:
        response = requests.get(f"{BACKEND_API_URL}/recommendations")
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

records = fetch_community_data()
recommendations = fetch_recommendations()

if not records:
    st.info("💡 AlloyDB database is currently empty. Please navigate to the **Data Upload** page in the sidebar and ingest a CSV dataset.")
else:
    # Convert database response to pandas DataFrame
    df = pd.DataFrame(records)
    
    # 1. KPIs Section
    total_wards = df["area"].nunique()
    total_complaints = df["complaints"].sum()
    avg_aqi = int(df["aqi"].mean())
    
    # Map categorical or numeric traffic values for risk scoring
    def get_traffic_val(val):
        if not val:
            return 10.0
        s = str(val).strip().lower()
        if s == "high":
            return 100.0
        elif s == "medium":
            return 50.0
        elif s == "low":
            return 10.0
        try:
            return float(s)
        except ValueError:
            return 10.0

    df["traffic_score"] = df["traffic"].apply(get_traffic_val)
    # Calculate official risk score
    df["risk_priority"] = (0.4 * df["complaints"]) + (0.3 * df["traffic_score"]) + (0.3 * df["aqi"])
    critical_row = df.loc[df["risk_priority"].idxmax()]
    critical_ward = critical_row["area"]
    
    # Color-coded badge for AQI status
    if avg_aqi > 100:
        aqi_class = "danger"
        aqi_status = "Unhealthy"
    elif avg_aqi > 50:
        aqi_class = "warning"
        aqi_status = "Moderate"
    else:
        aqi_class = "success"
        aqi_status = "Good"

    st.markdown(
        f"""
        <div class="metric-container">
            <div class="metric-card primary">
                <div class="metric-title">Wards Monitored</div>
                <div class="metric-value">{total_wards}</div>
                <div class="metric-subtitle">Active neighborhoods in database</div>
            </div>
            <div class="metric-card warning">
                <div class="metric-title">Logged Complaints</div>
                <div class="metric-value">{total_complaints}</div>
                <div class="metric-subtitle">Total tickets registered</div>
            </div>
            <div class="metric-card {aqi_class}">
                <div class="metric-title">Average AQI</div>
                <div class="metric-value">{avg_aqi} <span style="font-size:12px; font-weight:normal;">({aqi_status})</span></div>
                <div class="metric-subtitle">City-wide Air Quality index</div>
            </div>
            <div class="metric-card danger">
                <div class="metric-title">Critical Area Hotspot</div>
                <div class="metric-value" style="font-size: 20px;">{critical_ward}</div>
                <div class="metric-subtitle">Highest calculated risk score</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. Charts Section
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🌡️ Air Quality Index (AQI) by Area")
        # Sort values for a neat bar chart
        df_aqi = df.sort_values(by="aqi", ascending=False)
        fig_aqi = px.bar(
            df_aqi,
            x="area",
            y="aqi",
            color="aqi",
            color_continuous_scale="Reds",
            labels={"aqi": "AQI Score", "area": "Neighborhood"},
            title="AQI Levels (Threshold Line at 100)"
        )
        # Add safety threshold line (AQI=100)
        fig_aqi.add_hline(y=100, line_dash="dash", line_color="#EF4444", annotation_text="Unhealthy Threshold")
        fig_aqi.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#F3F4F6",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_aqi, use_container_width=True)

    with col2:
        st.markdown("### 🎫 Complaints Contribution")
        fig_comp = px.pie(
            df,
            names="area",
            values="complaints",
            hole=0.4,
            title="Percentage Contribution of Complaints",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_comp.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#F3F4F6",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    col3, col4 = st.columns([1, 2])
    
    with col3:
        st.markdown("### 🚗 Traffic Congestion Share")
        # Group by traffic category
        traffic_counts = df["traffic"].value_counts().reset_index()
        traffic_counts.columns = ["Traffic Level", "Count"]
        
        fig_traffic = px.pie(
            traffic_counts,
            names="Traffic Level",
            values="Count",
            title="Wards Grouped by Traffic Density",
            color="Traffic Level",
            color_discrete_map={"High": "#EF4444", "Medium": "#F59E0B", "Low": "#10B981"}
        )
        fig_traffic.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#F3F4F6",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_traffic, use_container_width=True)

    with col4:
        st.markdown("### 📋 Neighborhood Indicators Table")
        # Format dates for table display
        table_df = df[["area", "complaints", "traffic", "aqi", "timestamp"]].copy()
        table_df["timestamp"] = pd.to_datetime(table_df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M")
        table_df.columns = ["Neighborhood Wards", "Complaints", "Traffic Level", "Air Quality (AQI)", "Recorded Date"]
        st.dataframe(table_df, use_container_width=True, hide_index=True)

    # 3. Decision Recommendation Engine Integration
    if recommendations:
        st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 30px 0px;' />", unsafe_allow_html=True)
        st.markdown("<h2>🛡️ Decision Priority & AI Recommendations</h2>", unsafe_allow_html=True)
        st.markdown("### Official Risk Score Rankings and Departmental Directives")
        
        col_recs_chart, col_recs_details = st.columns([2, 3])
        
        with col_recs_chart:
            st.markdown("### 📊 Priority Vulnerability Ranking")
            df_recs = pd.DataFrame(recommendations)
            df_chart = df_recs.sort_values(by="risk_score", ascending=True)
            
            fig_recs = px.bar(
                df_chart,
                x="risk_score",
                y="area",
                orientation="h",
                color="risk_score",
                color_continuous_scale="Turbo",
                labels={"risk_score": "Risk Index Score", "area": "Ward Neighborhood"},
                title="Vulnerability Ranking (Higher Score = Priority Dispatch)",
                height=400
            )
            
            fig_recs.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#F3F4F6",
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(showgrid=False),
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_recs, use_container_width=True)
            
        with col_recs_details:
            st.markdown("### 📋 AI Directives & Resource Allocation")
            for item in recommendations:
                area = item["area"]
                score = item["risk_score"]
                rank = item["rank"]
                rec_actions = item["recommended_actions"]
                res_alloc = item["resource_allocation"]
                
                # Risk level color indicators
                if score >= 80:
                    badge = '<span class="status-badge danger">CRITICAL RISK</span>'
                elif score >= 50:
                    badge = '<span class="status-badge warning">MEDIUM RISK</span>'
                else:
                    badge = '<span class="status-badge success">LOW RISK</span>'
                    
                expander_label = f"Rank #{rank} - {area} (Risk Score: {score:.1f})"
                with st.expander(expander_label):
                    st.markdown(f"**Status Indicator:** {badge}", unsafe_allow_html=True)
                    st.markdown(f"**🎯 Recommended Actions:**\n{rec_actions}")
                    st.markdown(
                        f"""
                        <div style="background: rgba(99, 102, 241, 0.06); border: 1px solid rgba(99, 102, 241, 0.15); padding: 12px; border-radius: 6px; margin-top: 8px;">
                            <p style="font-size:13.5px; color:#A5B4FC; margin-bottom: 4px; margin-top:0px;">💰 <b>Resource Allocation Suggestion:</b></p>
                            <p style="font-size:13.5px; color:#E0E7FF; margin: 0px; line-height: 1.5; font-weight: 500;">{res_alloc}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
