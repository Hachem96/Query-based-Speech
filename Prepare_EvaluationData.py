import itertools
import json
import os
import numpy as np

def merge_json_chunks_with_context(json_path: str, n: int, overlap: int=0):
    """
    Merges every n consecutive keys in a JSON file into one chunk,
    breaks early if speakers differ
    Input:
        json_path: Path to the input JSON file
        n: Number of consecutive chunks to merge
    Output:        
        merged: Merged JSON dictionary
    """
    # Load input JSON
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    keys = list(data.keys())
    merged = {}
    chunk_counter = 1
    buffer = []
    current_speaker = None

    for i, k in enumerate(keys):
        item = data[k]
        # Keep original index key for reference
        item["key"] = i+1  

        # If speaker changes, flush current buffer and reset
        if buffer and item["speaker"] != current_speaker:
             chunk_key = f"chunk {chunk_counter}"
             merged[chunk_key] = {
            "start": buffer[0]["start"],
            "end": buffer[-1]["end"],
            "full_text": " ".join([item["full_text"] for item in buffer]),
            "keys": [item["key"] for item in buffer],
            "speaker": buffer[0]["speaker"]
            }
             chunk_counter += 1
             buffer = []
             current_speaker = None

        buffer.append(item)
        current_speaker = item["speaker"]

        # flush buffer if it reaches size n
        if len(buffer) >= n:
             chunk_key = f"chunk {chunk_counter}"
             merged[chunk_key] = {
            "start": buffer[0]["start"],
            "end": buffer[-1]["end"],
            "full_text": " ".join([item["full_text"] for item in buffer]),
            "keys": [item["key"] for item in buffer],
            "speaker": buffer[0]["speaker"]
            }
             chunk_counter += 1
             if(overlap!=0):
                    
                    # keep last item in buffer for overlap
                    if(overlap==1):
                        buffer = [buffer[-1]]
                    else:
                        buffer = buffer[len(buffer)-overlap:len(buffer)]
                    current_speaker = buffer[0]["speaker"]
             else:
                buffer = []
                current_speaker = None

    if buffer:
         chunk_key = f"chunk {chunk_counter}"
         merged[chunk_key] = {
        "start": buffer[0]["start"],
        "end": buffer[-1]["end"],
        "full_text": " ".join([item["full_text"] for item in buffer]),
        "keys": [item["key"] for item in buffer],
        "speaker": buffer[0]["speaker"]
        }


    return merged

def prepare_evaluation_data(evaluationPath,dataFolderName,n,overlap=0):
    """
    Prepares evaluation data for each subfolder in the given evaluationPath.
    Merges every n consecutive chunks in the transcription JSON files and
    prepares the corresponding ground truth QuestionsAnswers.json based on the new chunks.
    Input:
        evaluationPath: Path to the main evaluation directory containing subfolders.
        dataFolderName: Name of the folder to save the processed data.
                        (name of folder depends on configuration of merging (nb of chunks merged, overalap, etc))
        n: Number of consecutive chunks to merge.
    Output:        
        None (saves processed JSON files in respective subfolders)
    """

    if not os.path.isdir(evaluationPath):
        raise ValueError(f"Provided path '{evaluationPath}' is not a valid directory.")
    i = 0
    count = 0
    # Iterate over immediate subfolders
    for folder_name in os.listdir(evaluationPath):
        
        Mainfolder_path = os.path.join(evaluationPath, folder_name)
        Transcriptionfolder = os.path.join(Mainfolder_path, "AudioSegments_30.0Sec_SkipSilence_True_Overlap_False")
        folder_path = os.path.join(Transcriptionfolder, "Transcription")
        
        # check if folder_path is a directory (folder was transcribed)
        if os.path.isdir(folder_path):
            i = i + 1
            json_path = os.path.join(folder_path, "QuestionsAnswers.json")
            # verify if ground truth file exists
            if not os.path.isfile(json_path):
                print(f"QuestionsAnswers.json not found in {folder_path}, skipping...")
                continue
            print(f"Processing subfolder: {folder_name}  {i}/ {len(os.listdir(evaluationPath))} files")
            count+= 1
            json_path = os.path.join(folder_path, "transcription_whisper_large_v3.json")
            
            merged_json = merge_json_chunks_with_context(json_path, n,overlap)
            # Save merged JSON
           
            output_dir = os.path.join(Mainfolder_path, dataFolderName)
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir,f"{dataFolderName}.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(merged_json, f, indent=4, ensure_ascii=False)
            
            # prepare ground truth based on new merged chunks and save it in the same folder
            prepare_ground_truth(folder_path,output_dir,merged_json, overlap)
    print(f"Processed {count} folders out of {i} total folders.")

def prepare_ground_truth(transcription_folder,output_dir,merged_json, overlap):
    """
    Prepares the ground truth QuestionsAnswers.json based on the merged chunks.
    Input:
        transcription_folder: Path to the folder containing the original QuestionsAnswers.json.
        output_dir: Directory to save the processed QuestionsAnswers.json.
        merged_json: The merged JSON dictionary with new chunk keys.
    Output:
        None (saves processed QuestionsAnswers.json in the output_dir)
    """
    
    json_path = os.path.join(transcription_folder, "QuestionsAnswers.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    processed_data = []
    newchunks_keys = list(merged_json.keys())
    # iterate over each question-answer pair
    for item in data:
        new_item = {}
        new_item["question"] = item["question"]
        answer = item["answer"]
        new_answer = []
        new_answer_keys = []
        # find which new chunks contain the original answer keys
        for ans in answer:
            for i, chunk_key in enumerate(newchunks_keys):
                if ans in merged_json[chunk_key]["keys"] and (i+1) not in new_answer:
                    new_answer.append(i+1)
                    if(overlap!=0):
                        new_answer_keys.append(merged_json[chunk_key]["keys"])
        if overlap!=0:
            list_CombinationsAnswers = getCombinations_Answers(new_answer,answer,new_answer_keys)
            new_item["answer"] = list_CombinationsAnswers
        else:
            new_item["answer"] = new_answer
        processed_data.append(new_item)
    # Save processed QuestionsAnswers.json
    output_path = os.path.join(output_dir, "QuestionsAnswers.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(processed_data, f, indent=4, ensure_ascii=False)
    return 

def getCombinations_Answers(new_Fullanswer,original_answer,new_answer_keys):
    """
    Generates all combinations of new answer chunks that cover the original answer keys.
    This is useful when overlapping chunks are used, as multiple combinations may cover the same original answer.
    Input:
        new_Fullanswer: the full List of new chunk indices that contain original answer.
        original_answer: List of original answer keys.
    Output:
        list_CombinationsAnswers: List of lists, each containing a combination of new chunk indices.
    """
    list_CombinationsAnswers = []
    
    
    sorted_indices = [i for i, _ in sorted(enumerate(new_Fullanswer), key=lambda x: x[1])]
    new_Fullanswer = [new_Fullanswer[i] for i in sorted_indices]
    
    new_answer_keys = [new_answer_keys[i] for i in sorted_indices]
    newAnswer_Segments, keySegments = getAnswerSegements(new_Fullanswer,new_answer_keys)
    for i, segment in enumerate(newAnswer_Segments):
        if (len(newAnswer_Segments) > 1):
            a = 1
        keySegments_i = keySegments[i]  
        unique_keys = set(x for sublist in keySegments_i for x in sublist)
        segmentOriginalAnswer = [ele for ele in list(unique_keys) if ele in original_answer]
        combinationOneSegment = []
        for j, element in enumerate(segment):
            oneCombination = []
            keys_covered = []         
            k = j
            while (k < len(segment)):
                element_index = segment.index(segment[k])
                key_element = keySegments_i[element_index]
                intersection = [key for  key in key_element if key in segmentOriginalAnswer] # and key not in keys_covered]
                if(len(intersection) > 0):
                    keys_covered.extend(intersection)
                    oneCombination.append(segment[k])
                    if set(keys_covered) == set(segmentOriginalAnswer):
                        combinationOneSegment.append(oneCombination.copy())
                k += 1
            
        list_CombinationsAnswers.append(combinationOneSegment.copy())
    list_CombinationsAnswers = [sum(combo, []) for combo in itertools.product(*list_CombinationsAnswers)]
    # list_CombinationsAnswers.append(new_Fullanswer)
    return list_CombinationsAnswers


def getAnswerSegements(new_Fullanswer,new_answer_keys):
    """
    Splits the new_Fullanswer list into segments of consecutive numbers.
    Input:
        new_Fullanswer: List of new chunk indices.
    Output:
        segments: List of lists, each containing a segment of consecutive numbers.
    """
    segments = []
    keySegments = []
    current_segment = []
    current_keySegment = []
    current_segment.append(new_Fullanswer[0])
    current_keySegment.append(new_answer_keys[0])
    for i in range(1,len(new_Fullanswer)):
        if new_Fullanswer[i] == new_Fullanswer[i - 1] + 1:
            current_segment.append(new_Fullanswer[i])
            current_keySegment.append(new_answer_keys[i])

        else:
            segments.append(current_segment)
            keySegments.append(current_keySegment)
            current_segment = [new_Fullanswer[i]]
            current_keySegment = [new_answer_keys[i]]

    if current_segment:
        segments.append(current_segment)
        keySegments.append(current_keySegment)

    return segments, keySegments
def add_chunk_numbers(file_path, output_path):
    """
    Reads a transcription file, splits paragraphs by empty lines, 
    and adds 'chunk i:' at the beginning of each paragraph.
    Args:
        file_path (str): Path to the input transcription file.
        output_path (str): Path to save the updated file. 
                           
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Split by double newlines (paragraph separation)
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    updated_paragraphs = []
    for i, paragraph in enumerate(paragraphs):
        updated_paragraphs.append(f"مقطع {i+1}: {paragraph}")

    updated_text = "\n\n".join(updated_paragraphs)

    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(updated_text)

    print(f"File updated successfully. Saved at: {output_path}")

if __name__ == "__main__":
   
   evaluationPath = "/mnt/d/Personal/PromptSpeech/EvaluationData"
   dataFolderName = "TranscriptionChunk_120Sec_Overlap_90Sec"
   n = 4 # Number of chunks to merge
   prepare_evaluation_data(evaluationPath,dataFolderName,n, overlap=3)