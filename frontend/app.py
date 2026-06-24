import streamlit as st
import requests
import os
from config import BACKEND_API_URL  # type: ignore

# Page config
st.set_page_config(
    page_title="Community Decision Intelligence Platform",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS stylesheet
css_path = os.path.join(os.path.dirname(__file__), "styles.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Application Header & Sidebar Branding
st.sidebar.markdown("""
<div style='text-align: center; margin-bottom: 25px; padding: 15px; background: rgba(99, 102, 241, 0.08); border-radius: 14px; border: 1px solid rgba(99, 102, 241, 0.2);'>
    <h2 style='margin: 0px; font-weight: 800; background: linear-gradient(135deg, #818CF8 0%, #C084FC 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>CDIP</h2>
    <p style='color: #A5B4FC; font-size: 11px; margin: 4px 0 0 0; text-transform: uppercase; letter-spacing: 0.06em;'>Decision Intelligence</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()

# Verify Backend API Status
api_healthy = False
try:
    response = requests.get(f"{BACKEND_API_URL.replace('/api/v1', '')}/health", timeout=2)
    if response.status_code == 200:
        api_healthy = True
except Exception:
    pass

# Display Status in Sidebar
st.sidebar.markdown("### System Status")
if api_healthy:
    st.sidebar.markdown('<span class="status-badge success">● Backend: Connected</span>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<span class="status-badge danger">● Backend: Offline</span>', unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.info("Navigate using the standard sidebar pages directory options.")

# Main landing page design
st.markdown("<h1 style='font-size: 2.6rem; font-weight: 800; line-height: 1.2; margin-bottom: 8px; background: linear-gradient(135deg, #FFFFFF 30%, #A5B4FC 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>Community Decision Intelligence Platform</h1>", unsafe_allow_html=True)
st.markdown("### Empowering Local Leadership with AI-Driven Decision Insights")

# Banner layout
st.markdown(
    """
    <div class="glass-card">
        <h3>Welcome to the Platform</h3>
        <p>
            The <b>Community Decision Intelligence Platform (CDIP)</b> is a senior-architected, hackathon-ready solution 
            designed to ingest public datasets, identify community issues (complaints, traffic density, Air Quality Index), 
            and generate predictive risk assessments. Using Vertex AI (Gemini), CDIP converts complex urban data 
            into actionable policy recommendations for city administrators.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        <div class="glass-card">
            <h4>💡 Core Capabilities</h4>
            <ul>
                <li><b>High-Scale Ingestion</b>: Seamless CSV uploading with type validation and in-memory duplicate filtering.</li>
                <li><b>Interactive Command Center</b>: Dynamic dashboard tracking critical risk alerts and historical metrics.</li>
                <li><b>AI-Powered Prioritization</b>: Vertex AI automated risk calculation and priority scoring.</li>
                <li><b>Policy Recommendations</b>: Actionable, cost-estimated suggestions generated for municipal stakeholders.</li>
                <li><b>Contextual Assistant</b>: Interactive chat interface keeping track of data tables for complex queries.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <div class="glass-card" style="height: 100%;">
            <h4>🚀 Getting Started Guide</h4>
            <ol>
                <li><b>Step 1</b>: Go to the <b>Data Upload</b> page in the sidebar.</li>
                <li><b>Step 2</b>: Download or prepare a CSV dataset containing neighborhood metrics.</li>
                <li><b>Step 3</b>: Upload the CSV. The platform validates columns (area, complaints, traffic, aqi) and updates AlloyDB.</li>
                <li><b>Step 4</b>: Browse the <b>Dashboard</b> and run <b>Risk Analysis</b>.</li>
                <li><b>Step 5</b>: Query the <b>AI Assistant</b> to generate custom localized reports.</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True
    )
