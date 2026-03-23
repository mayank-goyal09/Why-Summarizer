import streamlit as st
import os
import time
from src.utils import GitDetective
from src.ingestion import initialize_vector_db, load_mock_jira_data
from src.engine import generate_why_summary

# --- 1. ELITE UI CONFIGURATION ---
st.set_page_config(
    page_title="Sherlock-RAG | Forensic Code Intelligence",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for "Forensic" Dashboard feel with Dark Green & Dark Yellow Theme
st.markdown("""
    <style>
    /* Dark green and dark yellow background gradient with overlay effect */
    .stApp {
        background: radial-gradient(circle at 20% 30%, rgba(204, 153, 0, 0.15) 0%, transparent 40%),
                    radial-gradient(circle at 80% 70%, rgba(0, 100, 0, 0.2) 0%, transparent 40%),
                    linear-gradient(135deg, #05140b 0%, #15200b 50%, #2b2b0a 100%);
        background-attachment: fixed;
    }
    
    /* Screen shading background */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: repeating-linear-gradient(
            0deg,
            rgba(0, 0, 0, 0.1),
            rgba(0, 0, 0, 0.1) 1px,
            transparent 1px,
            transparent 2px
        );
        pointer-events: none;
        z-index: 1000;
    }

    /* Text Colors */
    h1, h2, h3, h4, p, label, span {
        color: #e8ede4 !important;
    }

    /* Light gray button styling */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        background: linear-gradient(145deg, #e6e6e6, #cccccc) !important;
        color: #000000 !important;
        font-weight: 800;
        letter-spacing: 1px;
        border: 1px solid #b3b3b3;
        transition: all 0.3s ease-in-out;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        text-transform: uppercase;
    }
    .stButton>button p, .stButton>button div, .stButton>button span {
        color: #000000 !important;
    }
    .stButton>button:hover {
        background: linear-gradient(145deg, #ffffff, #e6e6e6) !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(200, 200, 100, 0.4);
    }

    /* Glass nodes / Glassmorphism Elements */
    .glass-card {
        background: rgba(10, 30, 15, 0.4) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5) !important;
        margin-bottom: 20px !important;
    }

    .reasoning-card {
        background: rgba(20, 40, 20, 0.45);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        border-left: 5px solid #d4af37; /* Dark yellow accent */
        padding: 24px;
        margin-top: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.6);
    }

    .timeline-node {
        background: rgba(40, 45, 20, 0.5); /* dark greenish yellow */
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }

    .timeline-arrow {
        text-align: center;
        font-size: 24px;
        color: #d4af37;
        margin: -5px 0;
        text-shadow: 0 0 5px rgba(212, 175, 55, 0.5);
    }
    
    /* Hero section styling */
    .hero-title {
        font-size: 3.5rem !important;
        font-weight: 900 !important;
        background: linear-gradient(45deg, #4CAF50, #ffd700);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px !important;
        line-height: 1.2;
        text-shadow: 0px 4px 20px rgba(0,0,0,0.8);
    }
    
    .hero-subtitle {
        font-size: 1.3rem;
        color: #b0c0b0 !important;
        margin-bottom: 30px;
        font-weight: 500;
        letter-spacing: 0.5px;
    }

    /* Input elements overriding */
    .stTextInput div[data-baseweb="input"] {
        background-color: rgba(0, 20, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #fff !important;
        border-radius: 6px;
    }
    .stTextArea div[data-baseweb="textarea"] {
        background-color: rgba(0, 20, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #fff !important;
        border-radius: 6px;
    }
    
    /* Sidebar glass effect */
    [data-testid="stSidebar"] {
        background: rgba(5, 15, 5, 0.6) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DUAL-PANE SIDEBAR (Configuration) ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; font-size: 80px; margin-bottom: 0;'>🕵️‍♂️</h1>", unsafe_allow_html=True)
    st.title("Forensic Config")
    st.markdown("---")
    
    st.subheader("🌐 Integration")
    repo_path = st.text_input("Local Repository Path", value="./", help="Absolute path to the git repo")
    jira_url = st.text_input("Jira Workspace URL", value="https://company.atlassian.net")
    
    st.markdown("---")
    st.subheader("🧠 Knowledge Engine")
    if st.button("⚡ Re-Index Jira Data"):
        progress_text = "Scanning Jira Tickets..."
        my_bar = st.progress(0, text=progress_text)
        
        mock_data = load_mock_jira_data()
        for percent_complete in range(100):
            time.sleep(0.01)
            my_bar.progress(percent_complete + 1, text=f"Indexing: {percent_complete+1}%")
        
        # Actual Indexing
        with st.spinner("Finalizing Vector Database..."):
            initialize_vector_db(mock_data)
        st.success("Indexing Complete!")

    st.info("💡 Currently using **Mock Mode** for Jira data retrieval.")

# --- 3. MAIN DASHBOARD AREA ---
col_left, col_right = st.columns([1.2, 0.8], gap="large")

with col_left:
    st.markdown("<h1 class='hero-title'>🕵️‍♂️ Sherlock-RAG</h1>", unsafe_allow_html=True)
    st.markdown("<div class='hero-subtitle'>Forensic Code Intelligence Dashboard<br><span style='font-size: 0.9em; color: #8a9a8a;'>Identify the Business Origin and Intent behind legacy code blocks.</span></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📝 Evidence Submission")
    code_input = st.text_area("Paste 'Confusing' Code Snippet:", height=250, placeholder="def complex_refactor(): ...", help="The code you want to investigate")
    
    c1, c2 = st.columns(2)
    with c1:
        file_name = st.text_input("Source File", value="app.py", placeholder="e.g. models/user.py")
    with c2:
        line_range = st.text_input("Line Range", value="1,5", placeholder="e.g. 104,120")

    investigate_btn = st.button("🔎 START INVESTIGATION")

with col_right:
    st.subheader("🕰️ Provenance Timeline")
    timeline_placeholder = st.empty()
    
    if not investigate_btn:
        timeline_placeholder.info("Submit evidence to begin forensic trace.")

# --- 4. INVESTIGATION LOGIC ---
if investigate_btn:
    if not code_input:
        st.error("Please provide a code snippet for analysis.")
    else:
        with st.status("🔍 Running Forensic Trace...", expanded=True) as status:
            # Step 1: Git Trace
            st.write("Checking Git history for commit signatures...")
            detective = GitDetective(repo_path=repo_path)
            start, end = line_range.split(',')
            jira_ids = detective.get_jira_id_from_code(file_name, start, end)
            time.sleep(0.8)
            
            # Update Timeline on the right
            with col_right:
                st.markdown(f"""
                <div class="timeline-node">
                    <strong>📄 Target:</strong> {file_name} (Lines {line_range})
                </div>
                <div class="timeline-arrow">↓</div>
                """, unsafe_allow_html=True)
                
                if jira_ids:
                    st.markdown(f"""
                    <div class="timeline-node" style="border-color: #4CAF50;">
                        <strong>📡 Git Link:</strong> Found Reference {', '.join(jira_ids)}
                    </div>
                    <div class="timeline-arrow">↓</div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="timeline-node" style="border-color: #ff4b4b;">
                        <strong>❓ Git Link:</strong> Unlinked Commit
                    </div>
                    """, unsafe_allow_html=True)

            if jira_ids:
                # Step 2: RAG Retrieval
                st.write(f"Connecting to Jira at {jira_url}...")
                raw_data = load_mock_jira_data()
                index = initialize_vector_db(raw_data)
                time.sleep(0.6)
                
                with col_right:
                    st.markdown(f"""
                    <div class="timeline-node">
                        <strong>🎟️ Jira Context:</strong> Retrieved metadata for {jira_ids[0]}
                    </div>
                    <div class="timeline-arrow">↓</div>
                    <div class="timeline-node" style="background-color: #00f2ff; color: #0e1117;">
                        <strong>🧠 AI Analysis:</strong> Generating 'Why' Summary
                    </div>
                    """, unsafe_allow_html=True)

                # Step 3: LLM Synthesis
                st.write("Synthesizing business intent with Mistral AI...")
                answer = generate_why_summary(jira_ids[0], code_input, index)
                
                status.update(label="Investigation Complete!", state="complete", expanded=False)
                
                # Show Result in "Reasoning Card"
                st.markdown("---")
                st.subheader("💡 Forensic Conclusion")
                st.markdown(f"""
                    <div class="reasoning-card">
                        <small style="color: #00f2ff;">AGENT CONCLUSION FOR {jira_ids[0]}</small>
                        <p style="font-size: 1.1em; color: white; margin-top: 10px;">
                            {answer}
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                status.update(label="Investigation Stalled: No Trace Found", state="error", expanded=False)
                st.error("No linked Jira tickets found in the commit messages for this code block.")
