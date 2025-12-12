import json
import os
import numpy as np
# from transformers import AutoModel
import torch
from sentence_transformers import SentenceTransformer
from openai import OpenAI

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
#embedding_OmarModel = SentenceTransformer("omarelshehy/Arabic-Retrieval-v1.0", trust_remote_code=True).to(device)
embedding_QwenModel = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B", trust_remote_code=True).to(device)
#embedding_JinaModel = AutoModel.from_pretrained("jinaai/jina-embeddings-v3", trust_remote_code=True).to(device) 
embedding_models = {#"jinaV3":embedding_JinaModel,
                    #"omarelshehy":embedding_OmarModel,
                    "Qwen-0.6B":embedding_QwenModel}

client = OpenAI(api_key=os.getenv("API_KEY_QWENEMBEDDING"),  # Replace with your API Key if you have not configured environment variables
                base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
model_name = "Qwen_V4"
dimension = 512

def embed_query(query):
    """
    function to embed query using embedding models in the embedding_models dictionary
    """
    completion = client.embeddings.create(
        model="text-embedding-v4",
        input= query,
        dimensions=dimension, # 768 # 1536 # 512
        encoding_format="float"
    )
    vector = np.array(completion.data[0].embedding, dtype=np.float32)  # Keep intermediate as float32
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector

def embed_chunks(transcriptionPath):
    """
    function to embed chunks of transcribed speech using list of models in  embedding_models
    Input:
        transcriptionPath: Path to the input JSON file containing chunks
    Output:        
        embeddeds: embedding arrays of models in embedding_models
    """
    # Save embedded JSON
    parent_folder = os.path.dirname(transcriptionPath)
    # Load JSON contains chunks of transcribed speech
    with open(transcriptionPath, "r", encoding="utf-8") as f:
        chunks_data = json.load(f)

    chunk_keys = list(chunks_data.keys())
    embeddings = []
    for embedModelName in embedding_models.keys():
        embeddingsOneModel = []
       
        embedded_path = os.path.join(parent_folder, f"{embedModelName}_embedding.npy")
        if os.path.isfile(embedded_path):
            print(f"Embedded file {embedded_path} already exists, skipping embedding...")
            return np.load(embedded_path)
        for key in chunk_keys:
            vector = embedding_models[embedModelName].encode(chunks_data[key]["full_text"])#.to(device) #,max_length=2048)
            norm = np.linalg.norm(vector)
            embeddingsOneModel.append(vector/norm)
        embeddingsOneModel = np.vstack(embeddingsOneModel)
        np.save(embedded_path, embeddingsOneModel)
        # embeddingInfo = {"modelName": embedModelName,
        #                  "embeddingPath": embedded_path,
        #                  "embeddingArray": embeddingsOneModel
        #                 }
        #embeddings.append(embeddingsOneModel)
    
    return  embeddingsOneModel #embeddings[0],embeddings[1],embeddings[2]

def embed_chunks_API(transcriptionPath,embedModelName="Qwen_V4_512"):
    """
    embedd chunks of transcription file using API Qwen embedding model
    """

    

    parent_folder = os.path.dirname(transcriptionPath)
    # Load JSON contains chunks of transcribed speech
    with open(transcriptionPath, "r", encoding="utf-8") as f:
        chunks_data = json.load(f)

    chunk_keys = list(chunks_data.keys())
    embeddingsModel = []
    embedded_path = os.path.join(parent_folder, f"{embedModelName}_embedding.npy")
    if( os.path.isfile(embedded_path)):
        print(f"Embedded file {embedded_path} already exists, skipping embedding...")
        return np.load(embedded_path)
    
    for key in chunk_keys:
        completion = client.embeddings.create(
        model="text-embedding-v4",
        input=chunks_data[key]["full_text"],
        dimensions=dimension, # 768 # 1536 # 512
        encoding_format="float"
    )
        vector = np.array(completion.data[0].embedding, dtype=np.float32)  # Keep intermediate as float32
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        #vector = vector.astype(np.float16)  # Final storage as float16
        embeddingsModel.append(vector)
    embeddingsModel = np.vstack(embeddingsModel)
    np.save(embedded_path, embeddingsModel)
    return embeddingsModel

def embedd_evaluation_data(evaluationPath,dataFolderName,model_name,dimension):
    """
    function to embed all transcribed text (chunks) of evaluation data using a specified embedding model
    Input:
        evaluationPath: Path to the evaluation data directory containing subfolders
        embedding_model: Preloaded embedding model (e.g., from transformers)
        dataFolderName: Name of the folder within each subfolder that contains the transcription JSON
                        each key in the JSON is a chunk of transcribed speech
        model_name: Name of the embedding model (used for saving the output file)
    """

    if not os.path.isdir(evaluationPath):
        raise ValueError(f"Provided path '{evaluationPath}' is not a valid directory.")
    i = 0
    # Iterate over immediate subfolders
    for folder_name in os.listdir(evaluationPath):
        folder_path = os.path.join(evaluationPath, folder_name)
        i = i + 1
        if os.path.isdir(folder_path):
            print(f"Processing subfolder: {folder_name}  {i}/ {len(os.listdir(evaluationPath))} files")
            folder_path = os.path.join(folder_path, dataFolderName)
            # check if folder_path is a directory (folder was transcribed and prepared for embedding using Prepare_EvaluationData.py)
            if os.path.isdir(folder_path):
                transcription_json = os.path.join(folder_path, f"{dataFolderName}.json")
                embeddedings = embed_chunks_API(transcription_json, dimension, model_name)
                print(f"Embedded data saved")
            else:
                print(f"Directory {folder_path} does not exist")
                print("folder was not prepared for evaluation using Prepare_EvaluationData.py, skipping...")
    return
            # Call the existing function on this folder

