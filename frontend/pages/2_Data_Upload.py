import streamlit as st
import pandas as pd
import requests
import os
from config import BACKEND_API_URL  # type: ignore

st.set_page_config(
    page_title="Data Upload - CDIP",
    page_icon="📥",
    layout="wide"
)

# Load CSS stylesheet
css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "styles.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Page header
st.markdown("<h1>📥 Ingest Community Datasets</h1>", unsafe_allow_html=True)
st.markdown("### Upload, validate, and index neighborhood indicators in AlloyDB")

st.markdown(
    """
    <div class="glass-card">
        <h4>📋 CSV File Schema Guidelines</h4>
        <p>The uploaded CSV file must contain the following columns:</p>
        <ul>
            <li><b>area</b>: Name of the neighborhood or district (e.g., <i>Downtown, Northside</i>).</li>
            <li><b>complaints</b>: Positive integer representing local tickets (e.g., <i>14, 25</i>).</li>
            <li><b>traffic</b>: Density tier (must be either <i>Low, Medium, High</i>).</li>
            <li><b>aqi</b>: Air Quality Index rating (e.g., <i>48, 156</i>).</li>
            <li><b>timestamp</b> (Optional): Timestamp of observation (e.g., <i>2026-06-23 12:00:00</i>).</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True
)

# Demo Dataset Options
st.markdown("### 🧪 Quick Demo Options")
demo_csv_content = """area,complaints,traffic,aqi,timestamp
Downtown,12,High,140,2026-06-23 12:00:00
Northside,8,Medium,75,2026-06-23 12:00:00
West End,25,85.0,210,2026-06-23 12:00:00
East Gate,3,Low,40,2026-06-23 12:00:00
Southside,15,45.5,90,2026-06-23 12:00:00
Metro Hub,30,High,180,2026-06-23 12:00:00
Riverfront,14,Low,55,2026-06-23 12:00:00
Green Valley,2,Low,25,2026-06-23 12:00:00
Industrial Zone,35,High,260,2026-06-23 12:00:00
Academic District,9,Medium,65,2026-06-23 12:00:00"""

col_demo_1, col_demo_2 = st.columns([1, 1])
with col_demo_1:
    st.download_button(
        label="📥 Download Demo CSV (10 Rows)",
        data=demo_csv_content,
        file_name="sample.csv",
        mime="text/csv",
        help="Download a 10-row sample CSV file configured with standard community indicators."
    )
with col_demo_2:
    if st.button("🚀 Load Demo Dataset (10 Rows)", help="Directly ingest the 10-row demo dataset into AlloyDB"):
        with st.spinner("Processing Demo CSV and writing to AlloyDB..."):
            files = {"file": ("sample.csv", demo_csv_content.encode("utf-8"), "text/csv")}
            try:
                response = requests.post(f"{BACKEND_API_URL}/datasets/upload", files=files)
                if response.status_code == 201:
                    result = response.json()
                    st.success("🎉 Demo CSV Ingested successfully!")
                    
                    # Generate AI Insights in background to populate Risk Analysis page immediately
                    try:
                        requests.post(f"{BACKEND_API_URL}/insights/generate", timeout=15)
                    except Exception:
                        pass
                    
                    st.balloons()
                    st.markdown(
                        f"""
                        <div class="metric-container">
                            <div class="metric-card success">
                                <div class="metric-title">Successfully Inserted</div>
                                <div class="metric-value">{result['inserted_rows']}</div>
                                <div class="metric-subtitle">New rows added to AlloyDB</div>
                            </div>
                            <div class="metric-card warning">
                                <div class="metric-title">Ignored Duplicates</div>
                                <div class="metric-value">{result['ignored_duplicates']}</div>
                                <div class="metric-subtitle">Already indexed in DB</div>
                            </div>
                            <div class="metric-card danger">
                                <div class="metric-title">Validation Errors</div>
                                <div class="metric-value">{len(result['errors'])}</div>
                                <div class="metric-subtitle">Skipped due to validation issues</div>
                            </div>
                        </div>
                        
                        <div style='text-align: center; margin-top: 25px; margin-bottom: 15px;'>
                            <a href='/Dashboard' target='_self' style='text-decoration: none;'>
                                <button style='background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%); color: white; border: none; border-radius: 10px; padding: 12px 30px; font-weight: 700; box-shadow: 0 4px 15px rgba(99, 102, 241, 0.35); cursor: pointer; transition: all 0.3s ease;'>
                                    📊 View Dashboard & Risk scoring
                                </button>
                            </a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.error(f"❌ API Server Error (Status Code {response.status_code}): {response.text}")
            except Exception as e:
                st.error(f"❌ Failed to connect to backend API server: {str(e)}")


st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 20px 0px;' />", unsafe_allow_html=True)

# File uploader widget
uploaded_file = st.file_uploader("Or choose your own CSV file", type=["csv"])

if uploaded_file is not None:
    # 1. Preview using Pandas locally
    try:
        df = pd.read_csv(uploaded_file)
        st.markdown("### 📊 Dataset Preview")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Display metadata
        col1, col2 = st.columns(2)
        col1.metric("Total Rows in File", len(df))
        col2.metric("Total Columns", len(df.columns))

        # Reset pointer for the backend request
        uploaded_file.seek(0)
        
        # Ingestion trigger button
        if st.button("🚀 Ingest into AlloyDB", type="primary"):
            with st.spinner("Processing CSV and writing to AlloyDB..."):
                # Prepare payload
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
                
                try:
                    # POST request to FastAPI backend
                    response = requests.post(f"{BACKEND_API_URL}/datasets/upload", files=files)
                    
                    if response.status_code == 201:
                        result = response.json()
                        st.success("🎉 CSV Ingested successfully!")
                        
                        # Generate AI Insights in background to populate Risk Analysis page immediately
                        try:
                            requests.post(f"{BACKEND_API_URL}/insights/generate", timeout=15)
                        except Exception:
                            pass
                        
                        st.balloons()
                        # Custom Metric Summary
                        st.markdown(
                            f"""
                            <div class="metric-container">
                                <div class="metric-card success">
                                    <div class="metric-title">Successfully Inserted</div>
                                    <div class="metric-value">{result['inserted_rows']}</div>
                                    <div class="metric-subtitle">New rows added to AlloyDB</div>
                                </div>
                                <div class="metric-card warning">
                                    <div class="metric-title">Ignored Duplicates</div>
                                    <div class="metric-value">{result['ignored_duplicates']}</div>
                                    <div class="metric-subtitle">Already indexed in DB</div>
                                </div>
                                <div class="metric-card danger">
                                    <div class="metric-title">Validation Errors</div>
                                    <div class="metric-value">{len(result['errors'])}</div>
                                    <div class="metric-subtitle">Skipped due to validation issues</div>
                                </div>
                            </div>
                            
                            <div style='text-align: center; margin-top: 25px; margin-bottom: 15px;'>
                                <a href='/Dashboard' target='_self' style='text-decoration: none;'>
                                    <button style='background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%); color: white; border: none; border-radius: 10px; padding: 12px 30px; font-weight: 700; box-shadow: 0 4px 15px rgba(99, 102, 241, 0.35); cursor: pointer; transition: all 0.3s ease;'>
                                        📊 View Dashboard & Risk scoring
                                    </button>
                                </a>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        
                        # Display individual row validation errors if any
                        if result["errors"]:
                            with st.expander("⚠️ View Row Validation Log"):
                                for error in result["errors"]:
                                    st.write(f"• {error}")
                                    
                    elif response.status_code == 422:
                        detail = response.json().get("detail", "Validation failed.")
                        st.error(f"❌ Ingestion rejected by server: {detail}")
                    else:
                        st.error(f"❌ API Server Error (Status Code {response.status_code}): {response.text}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("❌ Connection Error: Could not connect to backend API server. Make sure FastAPI backend is running.")
                except Exception as e:
                    st.error(f"❌ Unexpected Error: {str(e)}")
                    
    except Exception as e:
        st.error(f"❌ Failed to parse CSV: {str(e)}")
else:
    st.info("💡 Please upload a CSV file above to begin ingestion.")
