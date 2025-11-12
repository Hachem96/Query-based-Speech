import torch

from transformers import pipeline
#from transformers import WhisperTimeStampLogitsProcessor
#from transformers import  WhisperForConditionalGeneration,WhisperProcessor
from pyannote.audio import Pipeline
import librosa
import numpy as np
import json
from pydub import AudioSegment
import os
from pathlib import Path
import re
from jiwer import wer, cer
from collections import Counter

def load_and_resample_wav(file_path, averagChannel=False, channelNumber=0,target_sr=16000):
    """
    Load a WAV file and resample it to the target sample rate.
    Args:
        file_path (str): Path to the input WAV file.
        target_sr (int): Target sample rate (default is 16000 Hz).
        averagChannel (bool): If True, average all channels to mono.
        channelNumber (int): If averagChannel is False, select this channel number (0-indexed).
    Returns:
        audio (np.ndarray): Resampled audio data.
        sr (int): Sample rate of the resampled audio (should be target_sr).
    """
    # Load and resample the audio
    if(averagChannel):
        audio, sr = librosa.load(file_path, sr=target_sr,mono=True)
    else:
        audio, sr = librosa.load(file_path, sr=target_sr,mono=False)
        if(audio.ndim>1):
            if(channelNumber>=audio.shape[0]):
                channelNumber=0
            audio = audio[channelNumber, :]
            
    return audio, sr


def split_audio_by_diarization(wav_file, diarization_infoFile, output_dir="AudioSegments",max_duration=30.0,
                                overlap=True,skip_silence=True,oneSperaker=True):
    """
    Split audio file into chunks based on diarization results and save them in output_dir.
    Each chunk will have a maximum duration of max_duration seconds.
    Args:
        wav_file (str): Path to the input WAV file (full audio).
        diarization_infoFile (str): Path to the JSON file containing diarization results.
        output_dir (str): Name of Directory to save the output chunks.
        max_duration (float): Maximum duration (in seconds) for each chunk.
        overlap (bool): Whether to overlap segments, it is ignored if speaker changes or skip_silence is False.
        skip_silence (bool): Whether to skip silent parts between segments.
    Returns:
        None

    """    # Load audio
    audio = AudioSegment.from_wav(wav_file)
    parent_dir = os.path.dirname(wav_file)
    nameFolder = f"AudioSegments_{max_duration}Sec_SkipSilence_{skip_silence}_Overlap_{overlap}"
    output_dir = os.path.join(parent_dir, nameFolder)
    # Load diarization results
    with open(diarization_infoFile, "r") as f:
        diarization = json.load(f)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Initialize buffers
    chunk_audio = AudioSegment.empty()
    chunk_duration = 0.0
    chunk_index = 1
    max_ms = int(max_duration * 1000)
    segment_metadata = []
    start_chunk = 0
    end_chunk = 0
    previous_duration = 0
    previousSegAudio = AudioSegment.empty()
    start_previous = 0
    
    for i in range(0,len(diarization)):

        segment = diarization[i]
        start_ms = int(segment["start"] * 1000)
        end_ms = int(segment["end"] * 1000)
        speaker = segment["speaker"]
        if(oneSperaker):
            previous_speaker = "السيد"
         # For the first segment, initialize previous_speaker
        else:
            if(i==0):
                previous_speaker = speaker

        
        seg_audio = audio[start_ms:end_ms]
        if(skip_silence):
            seg_duration = (end_ms - start_ms) / 1000.0
        else:
            # If not skipping silence, consider the full range from end of current segment to end of previous segment including silence between them
            seg_duration = (end_ms - end_chunk) / 1000.0  # in seconds

        if ((oneSperaker) & (speaker== "السيد")) | (oneSperaker==False): # ignore very short segments      
        # If adding this segment would exceed the max_duration or speaker changes -> save current chunk first
            if (((chunk_duration + seg_duration) > max_duration) | (speaker!=previous_speaker)) & (len(chunk_audio) > 0):
                if chunk_duration > max_duration:
                    print(f"Warning: Chunk {chunk_index} exceeds max duration with {chunk_duration:.2f}s")
                #chunk_audio = chunk_audio[:max_ms]
                
                filename = f"chunk_{chunk_index}.wav"
                filepath = os.path.join(output_dir, filename)
                chunk_audio.export(filepath, format="wav")
                print(f"Saved {filepath} ({chunk_duration:.2f}s)")

                segment_metadata.append({
                    "index": chunk_index,
                    "start": round(start_chunk / 1000, 3),       # convert ms → seconds, 3 decimals
                    "end": round(end_chunk / 1000, 3),           # convert ms → seconds, 3 decimals
                    "duration": round(chunk_duration, 2),         # seconds, 2 decimals
                    "speaker": previous_speaker
                })

                # Reset for next chunk
                chunk_index += 1
                chunk_audio = AudioSegment.empty()
                chunk_duration = 0

                if(speaker==previous_speaker):
                    
                    if(skip_silence==False):
                        start_chunk = start_ms
                    else:
                        if(previous_duration<5) & (overlap):
                            # Add previous segment to current chunk if overlap is enabled and previous segment is short
                            chunk_audio += previousSegAudio
                            chunk_duration = previous_duration
                            start_chunk = start_previous
                        else:
                            start_chunk = start_ms
                else:
                    previous_speaker = speaker
                    start_chunk = start_ms
                    
            # Add segment to current chunk
            end_chunk = end_ms
            # ADD the current segment to chunck
            if(skip_silence) | (speaker!=previous_speaker) | (overlap):
                chunk_audio += seg_audio
                chunk_duration += seg_duration
                previousSegAudio= seg_audio
                previous_duration = seg_duration
                start_previous = start_ms
            else:
                chunk_audio = audio[start_chunk:end_chunk]
                chunk_duration  = (end_chunk - start_chunk)/1000

    # Save last chunk if it has content
    if len(chunk_audio) > 0:
        if chunk_duration > max_duration:
                print(f"Warning: Chunk {chunk_index} exceeds max duration with {chunk_duration:.2f}s")
                #chunk_audio = chunk_audio[:max_ms]
        filename = f"chunk_{chunk_index}.wav"
        filepath = os.path.join(output_dir, filename)
        chunk_audio.export(filepath, format="wav")
        print(f"Saved {filepath} ({chunk_duration:.2f}s)")
        segment_metadata.append({
                    "index": chunk_index,
                    "start": round(start_chunk / 1000, 3),       # convert ms → seconds, 3 decimals
                    "end": round(end_chunk / 1000, 3),           # convert ms → seconds, 3 decimals
                    "duration": round(chunk_duration, 2),         # seconds, 2 decimals
                    "speaker": previous_speaker
                })
    metadata_file = "ChunkMetadata.json"
    with open(os.path.join(output_dir, metadata_file), "w") as f:
        json.dump(segment_metadata, f, indent=4, ensure_ascii=False)
    
    return output_dir
  


def diarization_speech(wav_path, modelPipeline,nb_speakers=2,averagChannel=False, channelNumber=0):
     """
     perform speaker diarization of a speech file and save the results in json file
        Args:
            wave_file (str): Path to the input WAV file.
            modelPipeline: pipeline object of diarization model ( example: pyannote audio ).
            nb_speakers (int): Number of speakers to diarize.
            averagChannel (bool): If True, average all channels to mono.
            channelNumber (int): If averagChannel is False, select this channel number (0-indexed).
     """

     audio_array, fs = load_and_resample_wav(wav_path, averagChannel=averagChannel, channelNumber=channelNumber,target_sr=16000)
     input_tensor = torch.from_numpy(audio_array[None, :]).float()
     if(nb_speakers!=-1):
         outputs = modelPipeline({"waveform": input_tensor, "sample_rate": fs},num_speakers=nb_speakers)
     else:
         outputs = modelPipeline({"waveform": input_tensor, "sample_rate": fs},min_speakers=1,max_speakers=3)
     results = []
     
     for turn, _, speaker in outputs.itertracks(yield_label=True):
        results.append({
            "start": round(turn.start, 3),
            "end": round(turn.end, 3),
            "speaker": speaker
        })
     parent_dir = os.path.dirname(wav_path)
     json_path = os.path.join(parent_dir, "diarization_results.json")

     with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
     if(len(results)==0):
        return None
     # Rename speakers in the JSON file to more meaningful names
     update_json_path = rename_speakers(json_path)
     print(f"Diarization results saved to {update_json_path}")
     return update_json_path

def natural_key(path):
    """Sort key that handles numbers in filenames naturally."""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', path.stem)]

def transcribe_directory(input_dir, pipelineModel,predictTimeStamp,averagChannel=False, channelNumber=0, addnameSpeaker=True):
    """
    Transcribe all .wav files in input_dir using a given Whisper pipeline and save results in a JSON file.

    Args:
        input_dir (str | Path): Directory containing .wav files.
        segmentsInfo (str | Path): Path to the JSON file containing diarization results and segmentation audio.
        pipeline: Hugging Face Whisper pipeline object.
        predictTimeStamp (bool): Whether to return timestamps for each segment.
        averagChannel (bool): If True, average all channels to mono of each segment audio.
        channelNumber (int): If averagChannel is False, select this channel number (0-indexed).
    """
    input_dir = Path(input_dir)
       # Load diarization results
    segmentsInfoFile = os.path.join(input_dir, "ChunkMetadata.json")

    with open(segmentsInfoFile, "r") as f:
        segmentsInfo = json.load(f)

    results = {}
    fullText =[]
    wav_files = sorted(input_dir.glob("*.wav"), key=natural_key)
    nbFiles = len(wav_files)
    # Iterate over all .wav files in directory
    for i, wav_file in enumerate(wav_files):
        print(f"Processing: {wav_file.name} ({i}/{nbFiles})")
        audio_array, sr = load_and_resample_wav(wav_file, averagChannel=averagChannel,channelNumber=channelNumber,target_sr=16000)
        duration = len(audio_array) / sr
        if duration >30:
            temppredictTimeStamp=True
        else:
            temppredictTimeStamp=predictTimeStamp
        # Transcribe audio with Hugging Face pipeline
        if(temppredictTimeStamp):
            generate_kwargs = {
            "task": "transcribe",
            "language": "ar"
                }
            output = pipelineModel(audio_array,generate_kwargs=generate_kwargs,return_timestamps=temppredictTimeStamp)
        else:
            dict =  {"task": "transcribe", 
                    "language": "ar"}
            output = pipelineModel(audio_array,generate_kwargs=dict,return_timestamps=temppredictTimeStamp)

        if(addnameSpeaker):
            fullText.append(f"{segmentsInfo[i]['speaker']}: {output['text'].strip()}")
        else:
            fullText.append(output["text"].strip())
         # Store results

        # if(temppredictTimeStamp):
        #     results[wav_file.name] = {
        #         "full_text": output["text"].strip(),
        #         "segments": [
        #             {
        #                 "start": seg["timestamp"][0],
        #                 "end": seg["timestamp"][1],
        #                 "text": seg["text"].strip()
        #             }
        #             for seg in output["chunks"]
        #         ]
        #     }
            
        # else:
        results[wav_file.name] = {
            "full_text": output["text"].strip(),
            "speaker": segmentsInfo[i]["speaker"],
            "start": segmentsInfo[i]["start"],
            "end": segmentsInfo[i]["end"],
            "duration": segmentsInfo[i]["duration"]}
            
    fullText = "\n\n".join(fullText)
    print("Transcription completed.")
    # Save results as JSON in same directory
    transcription_dir = os.path.join(input_dir, "Transcription")
    os.makedirs(transcription_dir, exist_ok=True)
    json_path = os.path.join(transcription_dir, "transcription_whisper_large_v3.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
     # Save full text in same directory
    full_result_path = os.path.join(transcription_dir, "transcription_full_text.txt")
    with open(full_result_path, "w", encoding="utf-8") as f:
        f.write(fullText)

    print(f"Results saved to {json_path}")
    return full_result_path

def transcribe_One_Speech(wav_path,diarization_pipeline, ASR_Pipeline,configuration):
    """
    Transcribe a single speech file using diarization and ASR pipelines.
    Args:
        wav_path (str): Path to the input WAV file.
        diarization_pipeline: Pipeline object for speaker diarization.
        ASR_Pipeline: Pipeline object for automatic speech recognition (ASR).
        configuration (dict): Configuration parameters for diarization and ASR.
    Returns:
        None"""
    averChannel = configuration["averagChannel"]
    channelNumber = configuration["channelNumber"]
    nb_speakers = configuration["nb_speakers"]
    # Step 1: Diarization
    print("Starting diarization...")
    outputDiarizationPath = diarization_speech(wav_path, diarization_pipeline,nb_speakers=nb_speakers,
                                               averagChannel=averChannel, channelNumber=channelNumber)
    if(outputDiarizationPath is None):
       print(f"Diarization failed of wave in {wav_path}.")
       return
    print("Diarization completed.")
    # Step 2: Split audio by time stamps and speakers obtained by diarization model
    max_duration = configuration["max_duration"]
    overlap_segments = configuration["overlap_segments"]
    skip_silence = configuration["skip_silence"]
    predictTimeStamp = configuration["predictTimeStamp"]
    print("Splitting audio into segments...")
    OutputSegmentPath = split_audio_by_diarization(wav_path, outputDiarizationPath,max_duration=max_duration,overlap=overlap_segments,
                                                   skip_silence=skip_silence)
    print("Starting transcription...")
    # Step 3: Transcribe each segment using Whisper model
    full_transcribptionPath = transcribe_directory(OutputSegmentPath, ASR_Pipeline,predictTimeStamp,
                                                   averagChannel=averChannel, channelNumber=channelNumber,
                                                   addnameSpeaker=configuration["addnameSpeaker"])
    return

def transcribe_OneYearFolder(input_folder_path,diarization_pipeline, ASR_Pipeline,configuration):
    """
    Process the first .wav file in each subfolder of the given input folder path.
    Calls transcribe_One_Speech on the first .wav file found in each subfolder
    Parameters:
        input_folder_path (str): Path containing subfolders with .wav files
            a folder represents one year of speech data.
        diarization_pipeline: Pipeline object for speaker diarization.
        ASR_Pipeline: Pipeline object for automatic speech recognition (ASR).
        configuration (dict): Configuration parameters for diarization and ASR.
    Returns:
        None
    """
       # Ensure input path exists
    if not os.path.isdir(input_folder_path):
        raise ValueError(f"Provided path '{input_folder_path}' is not a valid directory.")
    i = 0
    max_duration = configuration["max_duration"]
    overlap_segments = configuration["overlap_segments"]
    skip_silence = configuration["skip_silence"]
    predictTimeStamp = configuration["predictTimeStamp"]
    # Iterate only over immediate subfolders
    for folder_name in os.listdir(input_folder_path):
       
        i = i + 1
        folder_path = os.path.join(input_folder_path, folder_name)
        print(f"Processing subfolder: {folder_name}  {i}/ {len(os.listdir(input_folder_path))} folders")
        if os.path.isdir(folder_path):
            # Collect all .wav files in the folder
            nameFolder = f"AudioSegments_{max_duration}Sec_SkipSilence_{skip_silence}_Overlap_{overlap_segments}"
            temp = os.path.join(folder_path, nameFolder)    
            transciption_dir = os.path.join(temp, "Transcription")
            if os.path.exists(transciption_dir) and os.path.isdir(transciption_dir):
                print(f"Folder '{folder_path}' already transcriped. Skipping process.")
                continue
            wav_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".wav")]

            if wav_files:
                print(f"Processing folder: {folder_name}") 
                wav_path = os.path.join(folder_path, wav_files[0])
                transcribe_One_Speech(wav_path,diarization_pipeline, ASR_Pipeline,configuration)


def transcribe_all_subfolders(input_path, diarization_pipeline, ASR_Pipeline,configuration):
    """
    Process all immediate subfolders of the given input path.
    Calls transcribe_OneYearFolder on each subfolder.
    Parameters:
        input_path (str): Path containing subfolders to process.
        diarization_pipeline: Pipeline object for speaker diarization.
        ASR_Pipeline: Pipeline object for automatic speech recognition (ASR).
        configuration (dict): Configuration parameters for diarization and ASR.
    Returns:
        None

    """
    if not os.path.isdir(input_path):
        raise ValueError(f"Provided path '{input_path}' is not a valid directory.")
    i = 0
    # Iterate over immediate subfolders
    for folder_name in os.listdir(input_path):
        folder_path = os.path.join(input_path, folder_name)
        i = i + 1
        if os.path.isdir(folder_path):
            print(f"Processing subfolder: {folder_name}  {i}/ {len(os.listdir(folder_path))} files")
            # Call the existing function on this folder
            transcribe_OneYearFolder(folder_path, diarization_pipeline, ASR_Pipeline,configuration)

def rename_speakers(json_path):
    """
    Reads a JSON file containing a list of dictionaries with 'start', 'end', and 'speaker'.
    Renames speakers:
      - Most frequent speaker becomes "السيد"
      - Remaining speakers become "متحدث_1", "متحدث_2", ...
    Saves the updated JSON list in the same directory with '_updated' suffix.
    
    Args:
        json_path (str): Path to the original JSON file.
    
    Returns:
        str: Path to the updated JSON file.
    """
    # Load JSON list
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Count occurrences of each speaker
    speaker_counts = Counter(item["speaker"] for item in data)
    
    # Find the most frequent speaker
    most_common_speaker = speaker_counts.most_common(1)[0][0]
    
    # Build mapping for speakers
    mapping = {most_common_speaker: "السيد"}
    remaining_speakers = [spk for spk in speaker_counts if spk != most_common_speaker]
    for idx, spk in enumerate(remaining_speakers, start=1):
        mapping[spk] = f"متحدث_{idx}"
    
    # Apply mapping to each dictionary
    for item in data:
        item["speaker"] = mapping[item["speaker"]]
    
    # Prepare output file path
    base, ext = os.path.splitext(json_path)
    updated_path = f"{base}_updatedSpeakerName{ext}"
    
    # Save updated JSON
    with open(updated_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return updated_path

def load_and_clean_text(file1):
    with open(file1, "r", encoding="utf-8") as f1:
        text = f1.read()
    # Remove tashkeel (diacritics)
    text = re.sub(r"[\u0617-\u061A\u064B-\u0652]", "", text)
    
    # Remove tatweel (ـ)
    text = re.sub(r"ـ", "", text)
    
    # Normalize Alef forms
    text = re.sub(r"[إأآا]", "ا", text)
    
    # Normalize Yaa
    text = re.sub(r"[يى]", "ي", text)
    
    # Normalize Taa Marbuta
    text = re.sub(r"ة", "ه", text)
    
    text = re.sub(r"[،,]", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()
    
    return text

def evaluate_model(txt_path, ground_truth_path,result_path):

    ground_truth = load_and_clean_text(ground_truth_path)
    asr_text = load_and_clean_text(txt_path)
    # Calculate WER and CER
    wer_result = wer(ground_truth, asr_text)
    cer_result = cer(ground_truth, asr_text)

    # Print results
    #print(f"\n Results for {model_name}:")
    print(f"   Word Error Rate (WER): {wer_result:.2%}")
    print(f"   Character Error Rate (CER): {cer_result:.2%}")
    results = {"WER": round(wer_result,2),
               "CER": round(cer_result,2)}
   
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    return 


if __name__ == "__main__":
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch.device(device)
    print(device)
  
    # model = whisper.load_model("large-v3", download_root="/mnt/d/Personal/PromptSpeech/models")
    #wav_path = "/mnt/d/Personal/PromptSpeech/videosPerYear/2006/2006-09-22/2006-09-22.wav"
    folder_oneYear_path = "/mnt/d/Personal/PromptSpeech/videosPerYear"
    diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
    diarization_pipeline.to(torch.device(device))
    asr_pipeline = pipeline("automatic-speech-recognition",
                              model="openai/whisper-large-v3",
                             device=device)
    configuration = {
        "averagChannel": False,
        "channelNumber": 0,
        "nb_speakers":-1 ,
        "max_duration": 30.0,
        "overlap_segments": False,
        "skip_silence": True,
        "addnameSpeaker": False,
        "predictTimeStamp": False
    }
    wav_path = "/mnt/d/Personal/PromptSpeech/test_presentation.wav"
    #transcribe_One_Speech(wav_path,diarization_pipeline, asr_pipeline,configuration)
    #transcribe_OneYearFolder(folder_oneYear_path,diarization_pipeline, asr_pipeline,configuration)
    transcribe_all_subfolders(folder_oneYear_path, diarization_pipeline, asr_pipeline,configuration)
    
    


    
    print("diarization done")
    print("splite the segments")
    # 
    #
    # with open("output.json", "r", encoding="utf-8") as f:
    # loaded_data = json.load(f)