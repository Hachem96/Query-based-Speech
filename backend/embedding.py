import json
import os
import numpy as np
#from transformers import AutoModel
#from sentence_transformers import SentenceTransformer
#import torch
from openai import OpenAI

# device = torch.device('cpu')
# #embedding_OmarModel = SentenceTransformer("omarelshehy/Arabic-Retrieval-v1.0", trust_remote_code=True).to(device)
# embedding_QwenModel = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B", trust_remote_code=True).to(device)
# #embedding_JinaModel = AutoModel.from_pretrained("jinaai/jina-embeddings-v3", trust_remote_code=True).to(device) 
# embedding_models = {#"jinaV3":embedding_JinaModel,
#                     #"omarelshehy":embedding_OmarModel,
#                     "Qwen-0.6B":embedding_QwenModel}

client = OpenAI(api_key=os.getenv("Qwen_API_KEY"),  # Replace with your API Key if you have not configured environment variables
                base_url="https://1274199.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1")
model_name = "Qwen_3_7_1024"
dimension = 1024

def embed_query(query):
    """
    function to embed query using embedding models in the embedding_models dictionary
    """
    completion = client.embeddings.create(
        model="qwen3.7-text-embedding",
        input= query,
        dimensions=dimension, # 768 # 1536 # 512
        encoding_format="float"
    )
    #vector = embedding_models["Qwen_37_512"].encode(query)#.to(device) #,max_length=2048)
    
    vector = np.array(completion.data[0].embedding, dtype=np.float32)  # Keep intermediate as float32
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector


