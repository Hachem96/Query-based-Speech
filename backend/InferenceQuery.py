
import os
import psycopg2
from backend.embedding import embed_query
from backend.searchinDatabase import get_table_from_db,compute_similarities
import numpy as np
import pandas as pd
#from moviepy import VideoFileClip

topK = 25
oneHole = True
startIdx = 0

def connectTodatabase():
    connection = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user="postgres",
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT"))
        )
    connection.autocommit = True
    cursor = connection.cursor()
    return connection, cursor
    
def inference_query(query,videoName):
    """
    function returns the start end time stamp represents the answer of query in videoName
    """
    # first step: embedd query
    embeddingQuery = embed_query(query)
    connection, cursor = connectTodatabase()

    # get information of videoName
    Table_Name = "Video"
    list_columns = ["id","name","year"]
    filter_condition = {"name": [videoName]}
    videoInfo = get_table_from_db(cursor, Table_Name, list_columns, filter_conditions=filter_condition)
    videoId = videoInfo["id"].loc[0]
    videoId = int(videoId)
    
    # compute the similaritie between the query and merged chunks of video
    mergedChunkSimilarities = compute_similarities(cursor,videoId, embeddingQuery)
    
    mergedChunkSimilarities["Scores"] = mergedChunkSimilarities["Qwen-0.6B"] #""]

    # sorte the chunks
    mergedChunkSimilarities = mergedChunkSimilarities.sort_values("Scores", ascending=True).reset_index(drop=True)
    if(len(mergedChunkSimilarities)>topK):
        topMergedChunkIds = mergedChunkSimilarities["mergedChunkId"].iloc[:topK].values
    else:
        topMergedChunkIds = mergedChunkSimilarities["mergedChunkId"].values
    
    topMergedChunkIds = topMergedChunkIds.tolist()
    
    # get topk merged chunks info using their ids
    Table_Name = "MergedChunks"
    list_columns = ["id","number","InitialChunkNumber","speaker"]
    filter_condition ={"id": topMergedChunkIds}
    mergedChunkInfo = get_table_from_db(cursor, Table_Name, list_columns, filter_conditions=filter_condition)

    # reorder merged chunk info in the same order of ids in topMergedChunkIds
    mergedChunkInfo["__order__"] = mergedChunkInfo["id"].apply(lambda x: topMergedChunkIds.index(x))
    mergedChunkInfo= mergedChunkInfo.sort_values("__order__").drop(columns="__order__").reset_index(drop=True)

    # get the chunk numbers of topk merged chunk
    topMergedChunkNumbers =  mergedChunkInfo["number"].values
    topMergedChunkNumbers = topMergedChunkNumbers.tolist()
    
    # get the sequental segment from topk where first chunk is top 1
    selectedChunks = getSegmentTopK(topMergedChunkNumbers,startIdx,oneHole)
    Table_Name = "MergedChunks"
    list_columns = ["id","number","InitialChunkNumber","speaker"]
    filter_condition ={"number": selectedChunks,
                       "videoId": [videoId]}
    mergedChunkInfo = get_table_from_db(cursor, Table_Name, list_columns, filter_conditions=filter_condition)

    # get the initial chunk numbers of the selected chunk
    initialChunkNumber = []
    for chunk in selectedChunks:
        value = mergedChunkInfo.loc[mergedChunkInfo["number"] == chunk, "InitialChunkNumber"].iloc[0]
        numbers = value.strip("[]").split(',')
        value = [float(num) for num in numbers]
        initialChunkNumber.extend(value)

    initialChunkNumber = sorted(set(initialChunkNumber))
    
    # extract the information time of the first and last initialchunk number
    Table_Name = "InitialChunks"
    list_columns = ["startTimeStamp","endTimeStamp","speaker"]
    filter_condition ={"number": [initialChunkNumber[0],initialChunkNumber[-1]],
                       "videoId": [videoId]}
    initialChunkInfo = get_table_from_db(cursor, Table_Name, list_columns, filter_conditions=filter_condition)
    output ={"startTimeStamp": np.min(initialChunkInfo["startTimeStamp"].values),
             "endTimeStamp": np.max(initialChunkInfo["endTimeStamp"].values)}
    output["duration"] = output["endTimeStamp"] - output["startTimeStamp"]
    return output

def getSegmentTopK(TopKChunks,chunkIndex,oneHole):
    
    selectedChunks =[TopKChunks[chunkIndex]]  
    if(selectedChunks[0]-1 in TopKChunks[0:5]):
        selectedChunks.insert(0,selectedChunks[0]-1)
        
        
    
    
    nextChunk = TopKChunks[chunkIndex] + 1
    if(oneHole):
        nextnextChunk = TopKChunks[chunkIndex] +2
    else:
        nextnextChunk = TopKChunks[chunkIndex] + 1
    while(nextChunk in TopKChunks) or (nextnextChunk in TopKChunks):
        if(len(selectedChunks)>=len(TopKChunks)):
            break 
        
        if(nextChunk in TopKChunks) and (nextnextChunk not in TopKChunks):
            selectedChunks.append(nextChunk)
            nextChunk = nextChunk + 1
            nextnextChunk = nextnextChunk + 1
        else:
            selectedChunks.append(nextChunk)
           
            
            if(oneHole):
                selectedChunks.append(nextnextChunk)
                nextChunk = nextChunk + 2
                nextnextChunk = nextnextChunk + 2
            else:
                nextChunk = nextChunk + 1
                nextnextChunk = nextnextChunk + 1     
    return selectedChunks


# def trim_and_show_video(video_path, start_time, end_time):
#     """
#     Trim and preview a segment of a video.

#     :param video_path: Path to the mp4 file
#     :param start_time: Start timestamp (seconds or 'HH:MM:SS')
#     :param end_time: End timestamp (seconds or 'HH:MM:SS')
#     """

#     # Load the video
#     clip = VideoFileClip(video_path)

#     # Trim video
#     trimmed = clip.subclipped(start_time, end_time)

#     # Preview the trimmed video
#     trimmed.preview()

#     # Close clips to free memory
#     trimmed.close()
#     clip.close()
if __name__ == "__main__":
    # create_database()
    videoName = "2005-04-25"
    videoPath = f"/mnt/d/Personal/PromptSpeech/EvaluationData/{videoName}/{videoName}.mp4"
    query = "ما هي اهم العوامل التي تجعل من القران معجزة خالدة ودليل على نبوة محمد على مدى التاريخ"
    output = inference_query(query,videoName)
    start = int(output["startTimeStamp"])
    end = int(output["endTimeStamp"])
    #trim_and_show_video(videoPath,start,end)
    print(output)
    