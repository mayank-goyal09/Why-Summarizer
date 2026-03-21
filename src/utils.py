import re
from git import Repo

class GitDetective:
    def __init__(self, repo_path):
        self.repo = Repo(repo_path)

    def get_jira_id_from_code(self, file_path, line_start, line_end):
        """Finds Jira IDs linked to specific lines of code."""
        # Run git blame on the specific lines
        blame_data = self.repo.git.blame('-L', f"{line_start},{line_end}", "--", file_path)
        
        # Regex to find patterns like 'PROJ-123'
        jira_pattern = r'[A-Z]+-\d+'
        found_ids = set()
        
        for line in blame_data.split('\n'):
            if line:
                # Extract the commit hash (first part of the blame line)
                commit_hash = line.split(' ')[0]
                commit_msg = self.repo.commit(commit_hash).message
                
                ids = re.findall(jira_pattern, commit_msg)
                found_ids.update(ids)
        
        return list(found_ids)

# 💡 Director's Note: This is our 'Search Key' for the RAG!