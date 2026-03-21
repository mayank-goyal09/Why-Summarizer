import os
import yaml
from src.utils import GitDetective
from src.ingestion import initialize_vector_db, load_mock_jira_data
from src.engine import generate_why_summary

# 1. Load Configurations
with open("config.yaml", 'r') as f:
    config = yaml.safe_load(f)

def run_project_why(file_to_check, lines):
    print(f"🔍 Analyzing lines {lines} in {file_to_check}...")

    # --- PHASE 1: Git Traceability ---
    detective = GitDetective(repo_path=".")
    # Extract line range (e.g., "10,15")
    start, end = lines.split(',')
    jira_ids = detective.get_jira_id_from_code(file_to_check, start, end)

    if not jira_ids:
        print("❌ No Jira IDs found in Git history for these lines.")
        return

    print(f"🎟️ Found Linked Jira Tickets: {jira_ids}")

    # --- PHASE 2: Knowledge Retrieval ---
    # In a real app, you'd only do this once to setup the DB
    raw_data = load_mock_jira_data()
    index = initialize_vector_db(raw_data)

    # --- PHASE 3: AI Reasoning ---
    # We'll grab the code snippet to show the LLM
    with open(file_to_check, 'r') as f:
        all_lines = f.readlines()
        snippet = "".join(all_lines[int(start)-1 : int(end)])

    print("🧠 Asking Mistral for the 'Why'...")
    # Using the first Jira ID found for the summary
    answer = generate_why_summary(jira_ids[0], snippet, index)
    
    print("\n" + "="*50)
    print(f"💡 THE HISTORICAL 'WHY':\n{answer}")
    print("="*50)

if __name__ == "__main__":
    # Example usage: check lines 1 to 5 of our own config file!
    # Make sure you've committed this file with a [PROJ-101] message first!
    run_project_why("config.yaml", "1,5")