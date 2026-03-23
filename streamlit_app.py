import streamlit as st
import os
from src.utils import GitDetective
from src.ingestion import initialize_vector_db, load_mock_jira_data
from src.engine import generate_why_summary

# --- 1. SET UP THE UI PAGE ---
st.set_page_config(page_title="Sherlock-RAG: Code Archaeologist", page_icon="🕵️‍♂️")
st.title("🕵️‍♂️ Sherlock-RAG: Code Archaeologist")
st.markdown("Connect your **Git** to your **Jira** to find out the 'Why' behind the code.")

# --- 2. SIDEBAR FOR SETTINGS (The 'App' way to handle the YAML) ---
with st.sidebar:
    st.header("⚙️ Configuration")
    repo_path = st.text_input("Local Repo Path", value="./")
    jira_url = st.text_input("Jira URL", value="https://company.atlassian.net")
    st.info("💡 For the demo, we are using Mock Jira data.")

# --- 3. MAIN INTERFACE ---
code_input = st.text_area("Paste the 'Confusing' Code Snippet here:", height=200)
line_range = st.text_input("Which lines are these? (e.g., 10,15)", value="1,5")
file_name = st.text_input("File Name (e.g., app.py)", value="app.py")

if st.button("🔍 Investigate the 'Why'"):
    with st.spinner("Searching through history..."):
        # Logic 1: Find Jira IDs using GitDetective
        detective = GitDetective(repo_path=repo_path)
        start, end = line_range.split(',')
        jira_ids = detective.get_jira_id_from_code(file_name, start, end)

        if jira_ids:
            st.success(f"🎟️ Found Linked Jira Tickets: {', '.join(jira_ids)}")
            
            # Logic 2: Get Context from Mock Data (or Real API)
            raw_data = load_mock_jira_data()
            index = initialize_vector_db(raw_data) # This would usually be pre-indexed
            
            # Logic 3: Ask the Brain (Ollama)
            answer = generate_why_summary(jira_ids[0], code_input, index)
            
            st.subheader("💡 The Historical Summary:")
            st.write(answer)
        else:
            st.error("❌ No Jira IDs found for this code block")