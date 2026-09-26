from processVideo.common import*
#from ASR.SpeechTextConversion import transcribe_One_Speech
import os
from processVideo.embedding import embed_chunks
from backend.DataBaseFunctions import*
from pathlib import Path
import json
# processVideo.create_pdf (weasyprint + DeepSeek) is imported lazily below, only when a
# PDF/correction actually has to be generated.

# When set, merged-chunk JSON is written under this dir instead of into each video folder,
# so ingestion can read straight from a read-only media drive.
MERGED_CHUNKS_DIR = os.getenv("MERGED_CHUNKS_DIR")

# When set, a run stops after adding this many new videos (existing ones don't count),
# so the corpus can be ingested in batches.
MAX_NEW_VIDEOS = int(os.getenv("MAX_NEW_VIDEOS", "0")) or None
nbNewVideos = 0
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

def add_new_video(videoName,year,mp4Path,caption,transcribe=True,correctTranscription=False, makeSummary=False):
    """
    function to add a new video to the database
    convert mp4 to mp3, transcribe video, mergechunks and compute embeddings
    each step is added to table in database
        transcription to initial chunk table
        mergedchunks to merged chunk table
        embeddings to embeddings table (three embedding models)
    """

    exist = videoIsExist(videoName)
    if exist:
         print(f"video {videoName} already exists in database")
    else:
        parent_dir = os.path.dirname(mp4Path)
        
        # create mo3 file
        mp3Path = os.path.join(parent_dir, os.path.splitext(mp4Path)[0] + ".wav")
        # convert video to mp4
        if transcribe and not os.path.exists(mp3Path):
            convert_mp4_to_wav(mp4Path,mp3Path)
        
        # create cover image for video using caption
        cover_path =os.path.join(parent_dir, "cover.png")
        if not os.path.exists(cover_path):
            text_file_to_image(cover_path, caption,font_size=38)
        
        # transcruption
        if(transcribe):
            textTranscription_path, transcriptionChunk_path = transcribe_One_Speech(mp3Path,transcriptionConfiguration)
        else:
            transcriptionChunk_path = os.path.join(parent_dir,"Transcription", "transcription_whisper_large_v3.json")
            textTranscription_path = os.path.join(parent_dir,"Transcription", "transcription_full_text.txt")
            transcriptionExist = os.path.exists(transcriptionChunk_path)
            if(not transcriptionExist):
                transcriptionChunk_path = "Not Available"
        
        
        if transcriptionChunk_path != "Not Available":
            
            # correct transcription if needed
            correctTranscription_path = os.path.join(parent_dir,"Transcription", f"correctedTranscription_{videoName}.txt")
            if correctTranscription:
                if not os.path.exists(correctTranscription_path):
                    from processVideo.create_pdf import correctTranscriptionText
                    correctTranscription_path = correctTranscriptionText(textTranscription_path,videoName)
            
            if not os.path.exists(correctTranscription_path):
                correctTranscription_path = "Not Available"
            

            if correctTranscription_path != "Not Available":
                # create pdf from corrected transcription
                output_pdf_path = os.path.join(parent_dir,"Transcription", f"transcription_{videoName}.pdf")
                if not os.path.exists(output_pdf_path):
                    from processVideo.create_pdf import create_pdf_correctedTranscription
                    output_pdf_path = create_pdf_correctedTranscription(correctTranscription_path, caption,videoName)
                
                if(makeSummary):
                    # summary_pdf_path = create_summary_pdf(correctTranscription_path, videoName)
                    sumary_pdf_path = "Not Available"
                else:
                    sumary_pdf_path = "Not Available"
            else:
                output_pdf_path = "Not Available"
                sumary_pdf_path = "Not Available"
        else:
            correctTranscription_path = "Not Available"
            output_pdf_path = "Not Available"
            sumary_pdf_path = "Not Available"
                
           
        
        yearVolderName = Path(parent_dir).parent.name
        mainFolderName = Path(parent_dir).parent.parent.name

        urlCover = f"{mainFolderName}/{yearVolderName}/{videoName}/cover.png"
        urlMP4 = f"{mainFolderName}/{yearVolderName}/{videoName}/{videoName}.mp4"
        urlMP3 = f"{mainFolderName}/{yearVolderName}/{videoName}/{videoName}.wav"
       
        if(output_pdf_path != "Not Available"):
            urlPdf = f"{mainFolderName}/{yearVolderName}/{videoName}/Transcription/" + os.path.basename(output_pdf_path)
        else:
            urlPdf = "Not Available"
        if(sumary_pdf_path != "Not Available"):
            urlSummaryPdf = f"{mainFolderName}/{yearVolderName}/{videoName}/Transcription/" + os.path.basename(sumary_pdf_path)
        else:
            urlSummaryPdf = "Not Available"
        if(textTranscription_path != "Not Available"):
            urlfullTranscription = f"{mainFolderName}/{yearVolderName}/{videoName}/Transcription/transcription_full_text.txt"
        else:
            urlfullTranscription = "Not Available"
        
        if(correctTranscription_path != "Not Available"):
            urlCorrectTranscription = f"{mainFolderName}/{yearVolderName}/{videoName}/Transcription/" + os.path.basename(correctTranscription_path) + ".txt"
        else:
            urlCorrectTranscription = "Not Available"

        #print(urlPdf)
        
        # add video information to video table 
        table_name = "Video"
        columnInfo = {
                    "name": videoName,
                    "year": year,
                    "caption": caption,
                    "linkToCover": urlCover,
                    "linkToMP4": urlMP4,
                    "linkToMP3": urlMP3,
                    "fullTranscriptionPath": urlfullTranscription,
                    "correctedTranscriptionPath": urlCorrectTranscription,
                    "linkToPdf": urlPdf,
                    "linkToSummaryPdf": urlSummaryPdf,
                    "linkToTranslation": "Not Available"
                }
       
        videoId = add_row(table_name,columnInfo)
        
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
            temp = add_row(table_name,chunkColumnsInfo)
        
        # merge transcribed chunk: 3 chunks with overal equals to 2
        merged_chunksPath = merge_transcribed_chunks(transcriptionChunk_path, nbChunksToMerge, nbOverlapChunks, MERGED_CHUNKS_DIR)
        
        
        # add merged chunk info and their embeddings 

        table_name = "MergedChunks"
        with open(merged_chunksPath, "r", encoding="utf-8") as f:
            mergedchunkData = json.load(f)
        
        Keys = list(mergedchunkData.keys())
        
        embeddingQwen = embed_chunks(merged_chunksPath)
        
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
            id = add_row(table_name,mergedChunkColumnsInfo)
            embeddingTableInfo = {
                "mergedChunkId": id,
                "videoId": videoId, 
                "Qwen-0.6B": embeddingQwen[i,:].tolist() 
            }
            temp = add_row("Embeddings",embeddingTableInfo)   
        print(f"adding your video {videoName} was done succefully")

def add_VideosOneYear(folderPath,transcribe,correctTranscription, makeSummary):
    """
    function to add list of videos to database
    Input
        folderPath: path contains folders of videos to be added
        transcribe: boolean indicating if videos must be transcribed
        year: the year of the videos in the folder
    """
    if not os.path.isdir(folderPath):
        raise ValueError(f"Provided path '{folderPath}' is not a valid directory.")
    global nbNewVideos
    i = 0
    # Iterate over immediate subfolders
    for folder_name in sorted(os.listdir(folderPath)):
        folder_path = os.path.join(folderPath, folder_name)
        i = i + 1
        if os.path.isdir(folder_path):
            print(f"Processing subfolder: {folder_name}  {i}/ {len(os.listdir(folderPath))} files")
            mp4Path = os.path.join(folderPath,folder_name,folder_name + '.mp4')
            try:
                year = int(folder_name[0:4])
            except:
                year = 0000
            captionPath = os.path.join(folderPath,folder_name,"caption.txt")
            transcriptionPath = os.path.join(folderPath,folder_name,"Transcription","transcription_whisper_large_v3.json")
            if not (os.path.exists(mp4Path) and os.path.exists(captionPath)):
                print(f"Skipping {folder_name}: missing mp4 or caption.txt")
                continue
            if not transcribe and not os.path.exists(transcriptionPath):
                print(f"Skipping {folder_name}: no transcription JSON and transcription is disabled.")
                continue
            with open(captionPath, "r", encoding="utf-8") as f:
                caption = f.read()

            if MAX_NEW_VIDEOS is not None and nbNewVideos >= MAX_NEW_VIDEOS:
                return
            if videoIsExist(folder_name):
                continue
            try:
                add_new_video(folder_name,year,mp4Path,caption,transcribe,correctTranscription, makeSummary)
                nbNewVideos += 1
            except Exception as e:
                # keep going; a failed video may leave a Video row without chunks/embeddings
                print(f"FAILED {folder_name}: {e!r}")

def add_all_videos(basePath,transcribe,correctTranscription, makeSummary):
    """
    function to add all videos in basePath to database
    Input
        basePath: path contains folders of years
        transcribe: boolean indicating if videos must be transcribed
    """
    if not os.path.isdir(basePath):
        raise ValueError(f"Provided path '{basePath}' is not a valid directory.")
    # Iterate over immediate subfolders
    for folder_name in sorted(os.listdir(basePath)):
        if MAX_NEW_VIDEOS is not None and nbNewVideos >= MAX_NEW_VIDEOS:
            print(f"Reached MAX_NEW_VIDEOS={MAX_NEW_VIDEOS}, stopping.")
            break
        folder_path = os.path.join(basePath, folder_name)
        if os.path.isdir(folder_path):
            print(f"Processing year folder: {folder_name}")
            add_VideosOneYear(folder_path,transcribe,correctTranscription, makeSummary)
            
if __name__ == "__main__":
    # mp4path = "/mnt/d/Personal/PromptSpeech/TestVideo/2005-04-25 - Trim.mp4"
    # caption = "test code on this video"
    # add_new_video("25-04-2005","2005",mp4path,caption)
    #evaluationPath = "/mnt/d/Personal/PromptSpeech/EvaluationData"
    # add_VideosOneYear(evaluationPath,transcribe=False)
    # exact on-disk case matters: the folder name becomes the prefix of every stored media path
    basePath = os.getenv("VIDEOS_BASE_PATH", "/mnt/d/Personal/PromptSpeech/videosPerYear")
    add_all_videos(basePath,transcribe=False,correctTranscription=False, makeSummary=False)