from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import qdrant_client
import yaml

# Load Config
with open("config.yaml", 'r') as f:
    config = yaml.safe_load(f)

def initialize_vector_db(jira_data_list):
    """Stores Jira ticket info into local Qdrant."""
    # 1. Setup Client
    client = qdrant_client.QdrantClient(path=config['paths']['qdrant_path'])
    
    # 2. Setup Embedding Model (Local)
    embed_model = HuggingFaceEmbedding(model_name=config['models']['embed_model'])
    
    # 3. Create Documents from Jira Data
    documents = [
        Document(text=item['description'], metadata={'jira_id': item['id'], 'title': item['title']})
        for item in jira_data_list
    ]
    
    # 4. Initialize Vector Store
    vector_store = QdrantVectorStore(client=client, collection_name="jira_knowledge")
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    # 5. Build Index
    index = VectorStoreIndex.from_documents(
        documents, 
        storage_context=storage_context, 
        embed_model=embed_model
    )
    print("✅ Jira Knowledge Base Indexed Locally!")
    return index