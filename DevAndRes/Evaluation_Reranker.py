import ast
import json
import os
import numpy as np
#from transformers import AutoModel
import torch
#from transformers import AutoModelForSequenceClassification, AutoTokenizer
import copy
import pandas as pd
#from sentence_transformers import SentenceTransformer
#from sentence_transformers import CrossEncoder
import matplotlib.pyplot as plt
from Evaluation_Embedding import*


def reranker_one_folder(folder_path,embedding_model_name, dataFolderName,top_k=20):
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

    json_path = os.path.join(folder_path, f"{dataFolderName}.json")
    with open(json_path, "r", encoding="utf-8") as f:
        transcription = json.load(f)
    textual_answers = []
    for key in transcription.keys():
        textual_answers.append(transcription[key]["full_text"])

    embed_chunks = os.path.join(folder_path, f"{embedding_model_name}_embedding.npy")
    
    if not os.path.isfile(embed_chunks):
        print(f"Embedded file {embed_chunks} not found, skipping...")
        return [],[]
    embeddings_array = np.load(embed_chunks)
    scores = []
    topAnswers = []
    for i, item in enumerate(data):
        query = item["question"]
        top_k_indices, similarities = getTopK_embedding(embedding_model,query, embeddings_array, top_k)
        textAnswers = [textual_answers[idx] for idx in top_k_indices]
        ranked_indices,rankingScores = rerank_embedding_results(query, textAnswers)
        top_k_indices = [top_k_indices[idx] for idx in ranked_indices]
        
        top_k_indices = [int(idx)+1 for idx in top_k_indices]  # Convert to 1-based indexing
        topAnswers.append(top_k_indices)
        scores.append(rankingScores.tolist())
    return scores, topAnswers

def reranker_all_folders(evaluationPath,embedding_model_name,rerankerModelName,dataFolderName, top_k=20):
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
    resultPath = os.path.join(resultPath,"Reranker")
    # Iterate over immediate subfolders
    results_all_folders = pd.DataFrame()
    for folder_name in os.listdir(evaluationPath):
        folder_path = os.path.join(evaluationPath, folder_name)
        i = i + 1
        if os.path.isdir(folder_path):
            resullts_one_folder = pd.DataFrame()
            print(f"Evaluating subfolder: {folder_name}  {i}/ {len(os.listdir(evaluationPath))} files")
            folder_path = os.path.join(folder_path, dataFolderName)
            # check if folder_path is a directory (folder was transcribed and prepared for embedding using Prepare_EvaluationData.py)
            if os.path.isdir(folder_path):
                    scores, topAnswers = reranker_one_folder(folder_path,embedding_model_name, dataFolderName, top_k=top_k)
    
                    if(len(scores) == 0):
                        print(f"No data to evaluate in folder {folder_name}, skipping...")
                        continue
                   
                    resullts_one_folder["TopAnswers"] = topAnswers
                    
                    resullts_one_folder["scores"] = scores
                    resullts_one_folder["question"] = [i+1 for i in range(len(scores))]
                    resullts_one_folder["folder_name"] = folder_name
                    cols = ['folder_name'] + [col for col in resullts_one_folder.columns if col != 'folder_name']
                    resullts_one_folder = resullts_one_folder[cols]
                    results_all_folders = pd.concat([results_all_folders,resullts_one_folder],ignore_index=True)
                    results_all_folders.to_csv(os.path.join(resultPath, f"Results_{dataFolderName}_{embedding_model_name}_{rerankerModelName}_top{top_k}.csv"), index=False)
                  

            else:
                print(f"Directory {folder_path} does not exist")
                print("folder was not prepared for evaluation using Prepare_EvaluationData.py, skipping...")
    return 

def rerank_embedding_results(query,answers):
    """
    function to rerank candidate answers based on a query using a reranker model
    Input:
        query: The input query string
        answers: List of candidate answer strings 
                sorted in descending order based on results of embedding model  
    Output:
        ranked_indices: Indices of answers ranked by relevance to the query
    """
    query_candidate_pairs = [(query, candidate) for candidate in answers]
    
# Tokenize the input texts
   
    # with torch.no_grad():
    #     inputs = tokenizer(query_candidate_pairs,truncation=True, max_length=8192, padding=True, return_tensors='pt').to(device)
    #     scores = rerankerModel(**inputs, return_dict=True).logits.view(-1, ).float()
    # scores = scores.cpu().numpy()
    scores = np.zeros(len(answers))
    for i, ans in enumerate(answers):
        temp = rerankerModel.rerank(query, [ans])
        scores[i] = temp[0]["relevance_score"]
      # 

    ranked_indices = np.argsort(scores)[::-1]
    ranked_answers = [answers[i] for i in ranked_indices]
    return ranked_indices,scores[ranked_indices]
    


def evaluate_mergeRerankerEmbeddResults(ListofResultPaths, evaluationPath,dataFolderName,oneHole,topK):
    listResults = []
    for paths in ListofResultPaths:
        listResults.append(pd.read_csv(paths))
    #resultRerannker = pd.read_csv(rerankerResultPath)
    #resultEmbedding = pd.read_csv(embeddingResultPath)
    resultRerannker = listResults[0]
    folderNames = pd.unique(resultRerannker['folder_name'])
    PercTop1inAnswer = 0
    output_df = pd.DataFrame()
    idxInresult = 0
    idxHighDiff = []
    folderNames = [fold for fold in folderNames if fold not in ["2018-02-24"]]
    for folder in folderNames:
        
        QuestionAnswerPath = os.path.join(evaluationPath, folder, dataFolderName,"QuestionsAnswers.json")
        with open(QuestionAnswerPath, "r", encoding="utf-8") as f:
            QuestionAnswer = json.load(f)
        resultsOneFolder = []
        for df in listResults:
            resultsOneFolder.append(df[df['folder_name'] == folder])
        #resultEmbedding = resultsOneFolder[1]
        #rerankerOneFolder = resultRerannker[resultRerannker['folder_name'] == folder]
        #embeddingOneFolder = resultEmbedding[resultEmbedding['folder_name'] == folder]
        precisionOneFolder = np.zeros(len(QuestionAnswer))
        recalloneFolder = np.zeros(len(QuestionAnswer))
        f1oneFolder = np.zeros(len(QuestionAnswer))
        meanAvgPrecisionOneFolder = np.zeros(len(QuestionAnswer))
        diffTopAnswer = np.zeros(len(QuestionAnswer))
        lengthAnaswer = np.zeros(len(QuestionAnswer))
        scoreOneFolder = np.zeros(len(QuestionAnswer))
        groundTruthOneFolder = []
        answerOneFolder = []
        for i in range(len(QuestionAnswer)):
            answer = QuestionAnswer[i]["answer"]
            isListofList = all(isinstance(el, list) for el in answer)
            
            # read embedding answers and scores
            for l,res in enumerate(resultsOneFolder):
                TopKChunksEmbed = res.iloc[i]["TopAnswers"]
                TopKChunksEmbed = TopKChunksEmbed.strip("[]").split(",")
                TopKChunksEmbed = [int(idx) for idx in TopKChunksEmbed]
                TopKChunksEmbed = np.array(TopKChunksEmbed)
                TopScoresEmbed = res.iloc[i]["scores"]
                TopScoresEmbed = TopScoresEmbed.strip("[]").split(",")
                TopScoresEmbed = [float(score) for score in TopScoresEmbed]
                TopScoresEmbed = np.array(TopScoresEmbed)
                if(l==0):
                    TopKChunks = []
                    TopScores = {}
                    outputScores = {}
                    for z in range(len(TopKChunksEmbed)):
                        TopScores[TopKChunksEmbed[z]] = 0
                        outputScores[TopKChunksEmbed[z]] = 100
                for k in range(len(TopKChunksEmbed)):
                    tempChunk = TopKChunksEmbed[k]
                    if(tempChunk in TopScores.keys()):
                            
                        if(tempChunk==1):
                            overlapChunks = [tempChunk]
                        else:
                            overlapChunks = [tempChunk]
                        minrank = 10000
                        
                        for chunk in overlapChunks:
                            if chunk in TopKChunksEmbed:
                                idx = np.argwhere(TopKChunksEmbed == chunk)
                                idx = idx[0][0]
                                minrank = min(minrank, idx)
                        TopScores[tempChunk] += TopScoresEmbed[k]
                        outputScores[tempChunk] = min(outputScores[tempChunk],TopScoresEmbed[k])
                        #TopScores[tempChunk] +=  1/(len(TopKChunksEmbed)+ minrank+1) # TopScoresReranker[idx] #+
            scores  = np.array(list(TopScores.values()))
            #scores = scores/len(listResults)
            TopKChunks = np.array(list(TopScores.keys()))
            TopScores = scores
            idxSorted = np.argsort(-TopScores)
            TopKChunks = TopKChunks[idxSorted]
            TopScores = TopScores[idxSorted]
            outputScores = np.array(list(outputScores.values()))
            outputScores = outputScores[idxSorted]
            if not isListofList:
                answer = [answer] 
            isTopFirstInAnswer = False   
            bestSelectedChunks = []
            groundTruth = []    
            for j in range(len(answer)):
                
                maxF1 = -1
                nbSegments, segments = getAnswerSegements(answer[j])
                for seg in segments:
                    maxScore = -10000
                    idxMax = 0
                   
                    #for chunkIndex in range(0,topK):
                    selectedChunks, avgScore = getSegmentTopK(TopKChunks[0:topK],0,TopScores[0:topK],oneHole)
                        # if avgScore > maxScore:
                        #     maxScore = avgScore
                        #     idxMax = chunkIndex
                        #     selectedChunks = tempselectedChunks
                    # if(bestSelectedChunks[0] in seg) or (bestSelectedChunks[0] == seg[0]-1):
                    #     if(bestSelectedChunks[0] == seg[0]-1):
                    #         bestSelectedChunks.insert(0, bestSelectedChunks[0]+1)
                    #     isTopFirstInAnswer = True
                    precision, recall, f1, avgPrec = compute_metrics(seg, selectedChunks)
                   

                    if f1 > maxF1:
                        maxF1 = f1
                        precisionOneFolder[i] = precision
                        recalloneFolder[i] = recall
                        f1oneFolder[i] = f1
                        meanAvgPrecisionOneFolder[i] = avgPrec
                        bestSelectedChunks = selectedChunks
                        diffTopAnswer[i] = (selectedChunks[0] - seg[0]) #/len(seg)
                        lengthAnaswer[i] = len(seg)
                        
                        groundTruth = seg
                        scoreOneFolder[i] = outputScores[0]
                    for selectedChunk in bestSelectedChunks:
                        if(selectedChunk in seg):
                            isTopFirstInAnswer = True
                   
            answerOneFolder.append(bestSelectedChunks)
            groundTruthOneFolder.append(groundTruth)       
            if(isTopFirstInAnswer):
                PercTop1inAnswer = PercTop1inAnswer + 1
            else:
                idxHighDiff.append(i + idxInresult)
                #diffTopAnswer[i] = -1000
            outputOneFolder = {"Recall": recalloneFolder,
                           "Precision":precisionOneFolder,
                           "f1":f1oneFolder,
                           "MeanAvgPrecision": meanAvgPrecisionOneFolder,
                           "diffTopAnswer":diffTopAnswer,
                           "lengthAnswer":lengthAnaswer,
                           "Score": scoreOneFolder,
                           "Question": np.arange(1,len(QuestionAnswer)+1),
                           "GroundTruth":groundTruthOneFolder,
                           "Answer":answerOneFolder}
        outputOneFolder = pd.DataFrame(outputOneFolder)
        outputOneFolder["Folder"] = folder

        output_df = pd.concat([output_df,outputOneFolder],ignore_index=True)

        idxInresult  += len(QuestionAnswer)
    output_df = output_df.reset_index(drop=True)    
    print(f"Percentage of times top 1 chunk is in the answer: {PercTop1inAnswer/len(output_df)*100}%")
    return output_df,idxHighDiff

def getSegmentTopK(TopKChunks,chunkIndex,scores,oneHole):
    
    selectedChunks =[TopKChunks[chunkIndex]]  
    avgScore = scores[chunkIndex]
    previousChunk = TopKChunks[chunkIndex] -1
    if(selectedChunks[0]-1 in TopKChunks[0:5]):
        idx = np.argwhere(TopKChunks == selectedChunks[0]-1)[0][0]
        selectedChunks.insert(0,selectedChunks[0]-1)
        
        avgScore = avgScore + scores[idx]
    
    idxScore = chunkIndex + 1
    nextChunk = TopKChunks[chunkIndex] + 1
    if(oneHole):
        nextnextChunk = TopKChunks[chunkIndex] +2
    else:
        nextnextChunk = TopKChunks[chunkIndex] + 1
    while(nextChunk in TopKChunks) or (nextnextChunk in TopKChunks):
        if(len(selectedChunks)>len(TopKChunks)-1):
            break 
        if(idxScore>len(TopKChunks)-1):
            break
        if(nextChunk in TopKChunks) and (nextnextChunk not in TopKChunks):
            selectedChunks.append(nextChunk)
            nextChunk = nextChunk + 1
            nextnextChunk = nextnextChunk + 1
            avgScore = avgScore + scores[idxScore]
            idxScore = idxScore + 1
        else:
            selectedChunks.append(nextChunk)
            avgScore = avgScore + scores[idxScore]
            idxScore = idxScore + 1
            if(oneHole) & (idxScore<=len(TopKChunks)-1):
                selectedChunks.append(nextnextChunk)
                avgScore = avgScore + scores[idxScore]
                idxScore = idxScore + 1
                nextChunk = nextChunk + 2
                nextnextChunk = nextnextChunk + 2
            else:
                nextChunk = nextChunk + 1
                nextnextChunk = nextnextChunk + 1

        

           
    return selectedChunks, avgScore/len(selectedChunks) 


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
if __name__ == "__main__":
   
    #device = torch.device('cuda')
    #embedding_model = SentenceTransformer("omarelshehy/Arabic-Retrieval-v1.0", trust_remote_code=True)
    # model_name_or_path = "Qwen/Qwen3-Reranker-0.6B"
    
    # tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
    # rerankerModel = AutoModelForSequenceClassification.from_pretrained(model_name_or_path).to(device) 
   
    #     model_name_or_path, trust_remote_code=True,unpad_inputs=True,
    #     #use_memory_efficient_attention=True,
    #     torch_dtype=torch.float16
    # ).to(device)
    #rerankerModel.eval()
    # rerankerModel = AutoModel.from_pretrained("jinaai/jina-reranker-v3", trust_remote_code=True).to(device)
    # embedding_model_name = "omarelshehy"
    # rerankerModelName = "jinaV3"
    # evaluationPath = "/mnt/d/Personal/PromptSpeech/EvaluationData"
    # resultPath = "/mnt/d/Personal/PromptSpeech/EvaluationData/Results/Reranker"
    # dataFolderName = "TranscriptionChunk_90Sec_Overlap_60Sec"
    # # # embedd_evaluation_data(evaluationPath,dataFolderName,model_name)
    # top_k = 100 
    # reranker_all_folders(evaluationPath,embedding_model_name,rerankerModelName,dataFolderName, top_k=top_k)

    evaluationPath = "/mnt/d/Personal/PromptSpeech/EvaluationData"
    dataFolderName = "TranscriptionChunk_90Sec_Overlap_60Sec"
    embeddingOmar  = "/mnt/d/Personal/PromptSpeech/EvaluationData/Results/Results_TranscriptionChunk_90Sec_Overlap_60Sec_omarelshehy_top100.csv"
    embeddingQwen = "/mnt/d/Personal/PromptSpeech/EvaluationData/Results/Results_TranscriptionChunk_90Sec_Overlap_60Sec_Qwen3-0.6B_top100.csv"
    embeddingJina = "/mnt/d/Personal/PromptSpeech/EvaluationData/Results/Results_TranscriptionChunk_90Sec_Overlap_60Sec_jinaV3_top100.csv"

    listResultPaths = [embeddingOmar,embeddingQwen,embeddingJina] #embeddingQwen,embeddingJina
    topK = 1
    oneHole = True
    outputResult,idxHighDiff = evaluate_mergeRerankerEmbeddResults(listResultPaths,evaluationPath,dataFolderName,oneHole=oneHole, topK=topK)