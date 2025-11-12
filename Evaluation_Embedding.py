import ast
import json
import os
import numpy as np
from transformers import AutoModel
import copy
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer
import matplotlib.pyplot as plt
def embed_chunks(json_path,model_name):
    """
    function to embed chunks of transcribed speech using a specified embedding model
    Input:
        json_path: Path to the input JSON file containing chunks
        embedding_model: Preloaded embedding model (e.g., from transformers)
        model_name: Name of the embedding model (used for saving the output file)
    Output:        
        embedded_path: Path to the saved numpy file containing embeddings
    """
    # Save embedded JSON
    parent_folder = os.path.dirname(json_path)
    embedded_path = os.path.join(parent_folder, f"{model_name}_embedding.npy")
    if os.path.isfile(embedded_path):
        print(f"Embedded file {embedded_path} already exists, skipping embedding...")
        return embedded_path
    # Load JSON contains chunks of transcribed speech
    with open(json_path, "r", encoding="utf-8") as f:
        chunks_data = json.load(f)

    chunk_keys = list(chunks_data.keys())
    embeddings = []
    
    for key in chunk_keys:
        vector = embedding_model.encode(chunks_data[key]["full_text"])#.to(device) #,max_length=2048)
        #vector = vector.cpu().numpy()
        embeddings.append(vector)
    embeddings = np.vstack(embeddings)
    
    
    
    np.save(embedded_path, embeddings)
    return embedded_path

def embedd_evaluation_data(evaluationPath,dataFolderName,model_name):
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
                embedded_path = embed_chunks(transcription_json,model_name)
                print(f"Embedded data saved to: {embedded_path}")
            else:
                print(f"Directory {folder_path} does not exist")
                print("folder was not prepared for evaluation using Prepare_EvaluationData.py, skipping...")
    return
            # Call the existing function on this folder

def evaluate_one_folder(folder_path,model_name, top_k=20):
    """
    function to retrieve the most relevant chunks of transcribed speech based on a query
    Input:
        query: The input query string
        embedding_model: Preloaded embedding model (e.g., from transformers)
        embedded_path: Path to the numpy file containing precomputed embeddings
        """
    json_path = os.path.join(folder_path, "QuestionsAnswers.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
  
    embed_chunks = os.path.join(folder_path, f"{model_name}_embedding.npy")
    
    if not os.path.isfile(embed_chunks):
        print(f"Embedded file {embed_chunks} not found, skipping...")
        return [],[],[],[],[]
    embeddings_array = np.load(embed_chunks)
    thresholds = np.linspace(0, 1, num=1000)
    if(top_k == -1):
        precision = np.zeros((len(thresholds),len(data)))
        recall = np.zeros((len(thresholds),len(data)))
    else:
        precision = np.zeros(len(data))
        recall = np.zeros(len(data))
    f1 = np.zeros(len(data))
    meanAvgPrecision = np.zeros(len(data))
    nbSegments = np.zeros(len(data))
    scores = []
    diff_FirstSegment = np.zeros(len(data))
    list_answers = []
    topAnswers = []
    for i, item in enumerate(data):
        query = item["question"]
        top_k_indices, similarities = getTopK_embedding(embedding_model,query,embeddings_array, top_k)
        
        scores.append(similarities[top_k_indices].tolist())
        
        top_k_indices = [int(idx+1) for idx in top_k_indices]
        topAnswers.append(top_k_indices)

        answer = item["answer"]
        isListofList = all(isinstance(el, list) for el in answer)
        idxMax = 0
        
        if not isListofList:
            answer = [answer]
        if(top_k == -1):
            length = [len(answer[j]) for j in range(len(answer))]
            maxLengthIdx = np.argmax(length)
            answer = answer[maxLengthIdx]
            precision[:,i], recall[:,i] = calculate_ROC(similarities, thresholds, answer)
        else:
            
            for j in range(len(answer)):
                tempPrec, tempRec, tempF1, tempMAP = compute_metrics(answer[j], top_k_indices)
                if(tempRec >= recall[i]):
                    if(tempRec == recall[i] and tempMAP < meanAvgPrecision[i]):
                        continue
                    precision[i] = tempPrec
                    recall[i] = tempRec              
                    f1[i] = tempF1
                    meanAvgPrecision[i] = tempMAP   
                    idxMax = j
                   
                    
            nbSegments[i],segments = getAnswerSegements(answer[idxMax])
            diff_FirstSegment[i] = 1000
            tempDiff = 1000
            for seg in segments:
                if(tempDiff > abs(top_k_indices[0] - seg[0])):
                    tempDiff = abs(top_k_indices[0] - seg[0])
                    diff_FirstSegment[i] = seg[0] - top_k_indices[0]

            list_answers.append(answer[idxMax])
    if(top_k == -1):
        return precision, recall, [], [], []
    return precision, recall, f1, meanAvgPrecision, list_answers, nbSegments,scores, diff_FirstSegment, topAnswers

def getTopK_embedding(embedding_model,query,embeddings_array,top_k):
    vector = embedding_model.encode(query) #,max_length=2048)
        # Normalize embeddings and vector
    embeddings_norm = embeddings_array / np.linalg.norm(embeddings_array, axis=1, keepdims=True)
    vector_norm = vector / np.linalg.norm(vector)

    # Compute cosine similarity
    similarities = embeddings_norm @ vector_norm.T
    #similarities = (similarities - np.min(similarities)) / (np.max(similarities) - np.min(similarities))
    if(top_k<len(similarities)):
        top_k_indices = np.argsort(similarities)[-top_k:][::-1]
    else:
        top_k_indices = np.argsort(similarities)[::-1]
    return top_k_indices, similarities

def getAnswerSegements(new_Fullanswer):
    """
    Splits the new_Fullanswer list into segments of consecutive numbers.
    Input:
        new_Fullanswer: List of new chunk indices.
    Output:
        segments: List of lists, each containing a segment of consecutive numbers.
    """
    segments = []
    
    current_segment = []
   
    current_segment.append(new_Fullanswer[0])
    
    for i in range(1,len(new_Fullanswer)):
        if new_Fullanswer[i] == new_Fullanswer[i - 1] + 1:
            current_segment.append(new_Fullanswer[i])
            

        else:
            segments.append(current_segment)
            
            current_segment = [new_Fullanswer[i]]
           
    if current_segment:
        segments.append(current_segment)
        

    return len(segments),segments

def calculate_ROC(similarities, thresholds,ground_truth):
    """
    Computes precision and recall at various similarity thresholds.
    
    Args:
        similarities (np.array): Array of similarity scores between the query and each chunk.
        thresholds (np.array): Array of thresholds to evaluate.  

    Returns:
        precision (np.array): Array of precision values at each threshold.
        recall (np.array): Array of recall values at each threshold.
    """
    precision = np.zeros(len(thresholds))
    recall = np.zeros(len(thresholds))

    for i, threshold in enumerate(thresholds):
        # Apply threshold to get binary relevance
        relevant = np.argwhere(similarities >= threshold)
        relevant = [int(idx+1) for idx in relevant.flatten()]
        # Compute precision and recall
        precision[i], recall[i], _, _ = compute_metrics(ground_truth, relevant)

    return precision, recall

def compute_metrics(ground_truth, retrieved):
    """
    Computes precision, recall, F1-score, and Mean Average Precision (MAP) for a single query.
    
    Args:
        ground_truth (list): List of ground truth chunk indices (1-based).
        retrieved (list): List of retrieved chunk indices (1-based).
        epsilon (float): Small value to avoid division by zero. Default is 1e-8.
    """
    nb_true_retrieved = [idx for idx in retrieved if idx in ground_truth]
    num_true_retrieved = len(nb_true_retrieved)
    num_retrieved = len(retrieved)
    num_ground_truth = len(ground_truth)
    if num_retrieved == 0:
        return 0.0, 0.0, 0.0, 0.0
    
    precision = num_true_retrieved / (num_retrieved) 
    recall = num_true_retrieved / (num_ground_truth )
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * (precision * recall) / (precision + recall)

    # calculate average precision
    num_relevant = 0
    precision_sum = 0.0

    for i, doc_id in enumerate(retrieved, start=1):
        if doc_id in ground_truth:
            num_relevant += 1
            tempPrecision = num_relevant / i
            precision_sum += tempPrecision

    avg_precision = precision_sum / num_ground_truth
    return precision, recall, f1, avg_precision

def evaluate_all_folders(evaluationPath,model_name,dataFolderName, top_k=20):
    """
    function to evaluate all subfolders in the evaluation data directory
    Input:
        evaluationPath: Path to the evaluation data directory containing subfolders
        embedding_model: Preloaded embedding model (e.g., from transformers)
        model_name: Name of the embedding model (used for saving the output file)
        dataFolderName: Name of the folder within each subfolder that contains the transcription JSON
                        each key in the JSON is a chunk of transcribed speech
        top_k: Number of top relevant chunks to retrieve for each query
    Output:
        precision, recall, f1, meanAvgPrecision: Arrays containing metrics for each query across all subfolders
    """

    if not os.path.isdir(evaluationPath):
        raise ValueError(f"Provided path '{evaluationPath}' is not a valid directory.")
    i = 0
    
    resultPath = os.path.join(evaluationPath, f"Results")
    # Iterate over immediate subfolders
    results_all_folders = pd.DataFrame()
    avg_results_speech = pd.DataFrame()
    for folder_name in os.listdir(evaluationPath):
        folder_path = os.path.join(evaluationPath, folder_name)
        i = i + 1
        if os.path.isdir(folder_path):
            resullts_one_folder = pd.DataFrame()
            print(f"Evaluating subfolder: {folder_name}  {i}/ {len(os.listdir(evaluationPath))} files")
            folder_path = os.path.join(folder_path, dataFolderName)
            # check if folder_path is a directory (folder was transcribed and prepared for embedding using Prepare_EvaluationData.py)
            if os.path.isdir(folder_path):
                if(top_k == -1):
                    temprecision, temprecall, _, _, _ = evaluate_one_folder(folder_path,model_name, top_k=top_k)
                    if(i==1):
                        precision = temprecision
                        recall = temprecall
                    else:
                        precision = np.hstack((precision, temprecision))
                        recall = np.hstack((recall, temprecall))
                else:
                    precision, recall, f1, meanAvgPrecision, list_answers, nbSegments, scores,diff_FirstSegment, topAnswers = evaluate_one_folder(folder_path,model_name, top_k=top_k)
    
                    if(len(precision) == 0):
                        print(f"No data to evaluate in folder {folder_name}, skipping...")
                        continue
                    resullts_one_folder["GroundTruth"] = list_answers
                    resullts_one_folder["Diff_FirstSegment"] = diff_FirstSegment
                    resullts_one_folder["TopAnswers"] = topAnswers
                    resullts_one_folder["nbSegments"] = nbSegments
                    resullts_one_folder["scores"] = scores
                    resullts_one_folder["question"] = [i+1 for i in range(len(precision))]
                    resullts_one_folder["precision"] = precision
                    resullts_one_folder["recall"] = recall
                    resullts_one_folder["f1"] = f1
                    resullts_one_folder["meanAvgPrecision"] = meanAvgPrecision
                    resullts_one_folder["folder_name"] = folder_name
                    cols = ['folder_name'] + [col for col in resullts_one_folder.columns if col != 'folder_name']
                    resullts_one_folder = resullts_one_folder[cols]
                    results_all_folders = pd.concat([results_all_folders,resullts_one_folder],ignore_index=True)

                    avg_result_One_folder = resullts_one_folder[['precision', 'recall', 'f1', 'meanAvgPrecision', 'Diff_FirstSegment']].mean().to_frame().T
                    avg_result_One_folder["folder_name"] = folder_name
                    avg_result_One_folder["Nb questions"] = len(precision)

                    cols = ['folder_name'] + [col for col in avg_result_One_folder.columns if col != 'folder_name']
                    avg_result_One_folder = avg_result_One_folder[cols]
                    avg_results_speech = pd.concat([avg_results_speech, avg_result_One_folder], ignore_index=True)

                    results_all_folders.to_csv(os.path.join(resultPath, f"Results_{dataFolderName}_{model_name}_top{top_k}.csv"), index=False)
                    #avg_results_speech.to_csv(os.path.join(resultPath, f"Avg_Results_{dataFolderName}_{model_name}_top{top_k}.csv"), index=False)


            else:
                print(f"Directory {folder_path} does not exist")
                print("folder was not prepared for evaluation using Prepare_EvaluationData.py, skipping...")
    if(top_k == -1):
        return np.mean(precision, axis=1), np.mean(recall, axis=1)
    #avg_result_all_folders = results_all_folders[['precision', 'recall', 'f1', 'meanAvgPrecision', 'Diff_FirstSegment']].mean().to_frame().T
    #avg_result_all_folders["Nb questions"] = len(results_all_folders)
    #avg_result_all_folders.to_csv(os.path.join(resultPath, f"Overall_Avg_Results_{dataFolderName}_{model_name}_top{top_k}.csv"), index=False)
    return 


    
   

if __name__ == "__main__":
    # jinaai/jina-embeddings-v3
    # "omarelshehy/Arabic-Retrieval-v1.0"
    # "Alibaba-NLP/gte-multilingual-base"
    # "intfloat/multilingual-e5-large-instruct"
    # "Qwen/Qwen3-Embedding-0.6B"
    device = torch.device('cuda')
    #embedding_model = SentenceTransformer("omarelshehy/Arabic-Retrieval-v1.0", trust_remote_code=True).to(device)
    
    embedding_model = AutoModel.from_pretrained("jinaai/jina-embeddings-v3", trust_remote_code=True).to(device) 
    model_name = "jinaV3"
    evaluationPath = "/mnt/d/Personal/PromptSpeech/EvaluationData"
    resultPath = "/mnt/d/Personal/PromptSpeech/EvaluationData/Results"
    dataFolderName = "TranscriptionChunk_120Sec_Overlap_60Sec"
    
    embedd_evaluation_data(evaluationPath,dataFolderName,model_name)
    top_k = 100
    evaluate_all_folders(evaluationPath,model_name,dataFolderName, top_k=top_k)
    # np.save(os.path.join(resultPath, f'MeanAvgPrec_{dataFolderName}_{model_name}.npy'), precision)
    # np.save(os.path.join(resultPath, f'Recall_{dataFolderName}_{model_name}.npy'), recall)
    # print("Precision:", precision.shape)
    # plt.figure()
    # plt.scatter(precision,recall) #, color='blue', s=10)
    # plt.xlabel('Precision')
    # plt.ylabel('Recall')
    # plt.title(f'Precision-Recall Curve for {model_name} on Evaluation Data')
    # plt.grid()
    # plt.show()
    # plt.savefig(os.path.join(evaluationPath, f'Precision_Recall_Curve_{dataFolderName}_{model_name}.png'))
    
