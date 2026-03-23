from llama_index.llms.ollama import Ollama
from llama_index.core import VectorStoreIndex
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

def generate_why_summary(jira_id, code_snippet, index):
    llm = Ollama(model="mistral", request_timeout=120.0)
    
    # Correct filtering logic for LlamaIndex
    filters = MetadataFilters(
        filters=[ExactMatchFilter(key="jira_id", value=jira_id)]
    )
    
    # Query the index for that specific Jira ID context
    retriever = index.as_retriever(filters=filters)
    nodes = retriever.retrieve(jira_id)
    context = nodes[0].text if nodes else "No specific Jira context found."

    prompt = f"""
    [Context from Jira]: {context}
    [Code Snippet]: {code_snippet}
    
    Explain WHY this code exists based on the business logic in the Jira ticket. 
    Be concise and focus on the 'Why', not the 'What'.
    """
    
    return llm.complete(prompt)