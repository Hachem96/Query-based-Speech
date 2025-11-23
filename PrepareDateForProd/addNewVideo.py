from PrepareDateForProd.common import*
#from ASR.SpeechTextConversion import transcribe_One_Speech
import os
from embedding.embeddingScript import embed_chunks
from Database.DataBaseFunctions import*
transcriptionConfiguration = {
        "averagChannel": False,
        "channelNumber": 0,
        "nb_speakers":-1 ,
        "max_duration": 30.0,
        "overlap_segments": False,
        "skip_silence": True,
        "addnameSpeaker": False,
        "predictTimeStamp": False
    }

configuration_db = {"db_name": "SpeechDatabaseInfo",
                     "password": "root",
                     "host": "localhost",
                      "port": 5433 }

nbChunksToMerge = 3 # number of chunks to merge
nbOverlapChunks = 2 # number of overal chunks 

def add_new_video(videoName,year,mp4Path,caption,mp3Path=None,transcribe=True):
    """
    function to add a new video to the database
    convert mp4 to mp3, transcribe video, mergechunks and compute embeddings
    each step is added to table in database
        transcription to initial chunk table
        mergedchunks to merged chunk table
        embeddings to embeddings table (three embedding models)
    """

    exist = videoIsExist(configuration_db,videoName)
    if exist:
         print(f"video {videoName} already exists in database")
    else:
        parent_dir = os.path.dirname(mp4Path)
        # convert video to mp4
        if(mp3Path==None):
        
            mp3Path = os.path.join(parent_dir, os.path.splitext(mp4Path)[0] + ".wav")
        #convert_mp4_to_wav(mp4Path,mp3Path)

        # create cover image for video using caption
        cover_path =os.path.join(parent_dir, "cover.png")
        text_file_to_image(cover_path, caption)

        if(transcribe):
            textTranscription_path, transcriptionChunk_path = transcribe_One_Speech(mp3Path,transcriptionConfiguration)
        else:
            transcriptionChunk_path = os.path.join(parent_dir,"Transcription", "transcription_whisper_large_v3.json")
            
            textTranscription_path =  os.path.join(parent_dir,"Transcription","transcription_full_text.txt")
        
        # add video information to video table 
        table_name = "Video"
        columnInfo = {
                    "name": videoName,
                    "year": year,
                    "caption": (caption,),
                    "linkToCover": f"{videoName}/cover.png",
                    "linkToMP4": f"{videoName}/{videoName}.mp4",
                    "linkToMP3": f"{videoName}/{videoName}.wav",
                    "fullTranscriptionPath": f"{videoName}/Transcription/transcription_full_text.txt",
                    "pdfContent": "TEXT",          # raw text extracted from PDF
                    "linkToPdf": "TEXT",
                    "summary": "TEXT",
                    "linToSummaryPdf": "TEXT"
                }
       
        videoId = add_row(configuration_db,table_name,columnInfo)
        
        # add chunk data to db
        table_name = "InitialChunks"
        with open(transcriptionChunk_path, "r", encoding="utf-8") as f:
            chunkData = json.load(f)
        keys = list(chunkData.keys())
        for i, key in enumerate(keys):
            chunk = chunkData[key]
            chunkColumnsInfo = {
                    "videoId":videoId,   # adjust table name if needed
                    "number": int(i+1),
                    "text": chunk["full_text"],
                    "startTimeStamp": chunk["start"],
                    "endTimeStamp": chunk["end"],
                    "duration": chunk["duration"],
                    "speaker": chunk["speaker"]
                }
            temp = add_row(configuration_db,table_name,chunkColumnsInfo)
        
        # merge transcribed chunk: 3 chunks with overal equals to 2
        merged_chunksPath = merge_transcribed_chunks(transcriptionChunk_path, nbChunksToMerge, nbOverlapChunks)
        
        
        # add merged chunk info and their embeddings 

        table_name = "MergedChunks"
        with open(merged_chunksPath, "r", encoding="utf-8") as f:
            mergedchunkData = json.load(f)
        
        Keys = list(mergedchunkData.keys())
        
        embeddingJina,embeddingOmar,embeddingQwen = embed_chunks(merged_chunksPath)
        
        for i, key in enumerate(Keys):
            chunk = mergedchunkData[key]
            mergedChunkColumnsInfo = {
                "videoId": videoId,   # adjust parent table name if needed
                "number": int(i+1),
                "InitialChunkNumber": chunk["keys"],                # list of integer IDs
                "text": chunk["full_text"],
                "startTimeStamp": chunk["start"],
                "endTimeStamp": chunk["end"],
                "speaker": chunk["speaker"]
            }
            
            # add merged chunk to table and use its id to add the embeddings in embedding table
            id = add_row(configuration_db,table_name,mergedChunkColumnsInfo)
            embeddingTableInfo = {
                "mergedChunkId": id,
                "videoId": videoId, 
                "jinaV3": embeddingJina[i,:].tolist(),
                "omarelshehy": embeddingOmar[i,:].tolist(),
                "Qwen-0.6B": embeddingQwen[i,:].tolist() 
            }
            temp = add_row(configuration_db,"Embeddings",embeddingTableInfo)   
        print(f"adding your video {videoName} was done succefully")

def add_listVideos(folderPath,transcribe):
    """
    function to add list of videos to database
    Input
        folderPath: path contains folders of videos to be added
        transcribe: boolean indicating if videos must be transcribed
    """
    if not os.path.isdir(folderPath):
        raise ValueError(f"Provided path '{folderPath}' is not a valid directory.")
    i = 0
    # Iterate over immediate subfolders
    for folder_name in os.listdir(folderPath):
        folder_path = os.path.join(folderPath, folder_name)
        i = i + 1
        if os.path.isdir(folder_path):
            print(f"Processing subfolder: {folder_name}  {i}/ {len(os.listdir(folderPath))} files")
            mp4Path = os.path.join(folderPath,folder_name,folder_name + '.mp4')
            year = int(folder_name[0:4])
            captionPath = os.path.join(folderPath,folder_name,"caption.txt")
            with open(captionPath, "r", encoding="utf-8") as f:
                caption = f.read()
            add_new_video(folder_name,year,mp4Path,caption,mp3Path=None,transcribe=transcribe)
if __name__ == "__main__":
    # mp4path = "/mnt/d/Personal/PromptSpeech/TestVideo/2005-04-25 - Trim.mp4"
    # caption = "test code on this video"
    # add_new_video("25-04-2005","2005",mp4path,caption)
    evaluationPath = "/mnt/d/Personal/PromptSpeech/EvaluationData"
    add_listVideos(evaluationPath,transcribe=False)