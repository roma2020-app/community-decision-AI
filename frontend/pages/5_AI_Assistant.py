import streamlit as st
import requests
import os
from config import BACKEND_API_URL  # type: ignore

st.set_page_config(
    page_title="AI Assistant - CDIP",
    page_icon="💬",
    layout="wide"
)

# Load CSS stylesheet
css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "styles.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Page header
st.markdown("<h1>💬 AI Decisions Assistant</h1>", unsafe_allow_html=True)
st.markdown("### Contextual planning partner connected to AlloyDB and powered by Vertex AI Gemini")

# Session State for chat log
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar panel with helper tips
with st.sidebar:
    st.markdown("### Prompt Library")
    st.markdown("Select a quick query to test the platform:")
    
    col_width_css = """
    <style>
    div.stButton > button {
        width: 100%;
        text-align: left;
        padding: 8px 12px;
        background-color: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 8px;
        color: #ddd;
    }
    div.stButton > button:hover {
        border-color: #6366F1;
        color: white;
    }
    </style>
    """
    st.markdown(col_width_css, unsafe_allow_html=True)
    
    q1 = st.button("🚨 Which ward needs attention?")
    q2 = st.button("⚠️ What area has the highest risk?")
    q3 = st.button("📋 Summarize community issues.")
    q4 = st.button("💡 Provide policy recommendations.")
    
    st.divider()
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Welcome instruction banner
if not st.session_state.messages:
    st.markdown(
        """
        <div class="glass-card">
            <h4>💡 How to use the Assistant</h4>
            <p>
                The Decisions Assistant reads community data tables directly from AlloyDB. 
                You can ask questions about specific neighborhood profiles, ask for comparison reports, 
                or inquire about environmental (AQI) and service complaints vulnerabilities.
            </p>
            <p><i>Example queries: "Is there any area with an AQI higher than 100?", "Compare complaints in Downtown vs West End"</i></p>
        </div>
        """,
        unsafe_allow_html=True
    )

# Render Chat History
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Callback for processing message submission
def handle_message_submission(user_msg: str):
    # Render user query
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_msg)
        
    # Append to session state
    st.session_state.messages.append({"role": "user", "content": user_msg})
    
    # Send request to backend FastAPI endpoint
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        with st.spinner("AI is thinking..."):
            try:
                # Construct history payload for Vertex AI
                # We limit to last 10 messages to keep request payload light
                history_payload = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[:-1]
                ][-10:]
                
                payload = {
                    "message": user_msg,
                    "history": history_payload
                }
                
                response = requests.post(f"{BACKEND_API_URL}/chat/message", json=payload)
                
                if response.status_code == 200:
                    ai_response = response.json().get("response", "No response received.")
                    message_placeholder.markdown(ai_response)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                else:
                    err_msg = f"❌ API Server Error (Status Code {response.status_code}): {response.text}"
                    message_placeholder.markdown(err_msg)
            except requests.exceptions.ConnectionError:
                message_placeholder.markdown("❌ Connection Error: Could not connect to backend API server. Make sure FastAPI backend is running.")
            except Exception as e:
                message_placeholder.markdown(f"❌ Unexpected Error: {str(e)}")

# Capture direct input from suggestions buttons
suggested_query = None
if q1:
    suggested_query = "Which ward needs attention?"
elif q2:
    suggested_query = "What area has the highest risk?"
elif q3:
    suggested_query = "Summarize community issues."
elif q4:
    suggested_query = "Provide policy recommendations."

if suggested_query:
    handle_message_submission(suggested_query)

# Input text box
if prompt := st.chat_input("Ask a question about the community data..."):
    # If a button was clicked in the same run, ignore chat input to prevent double sending
    if not suggested_query:
        handle_message_submission(prompt)
