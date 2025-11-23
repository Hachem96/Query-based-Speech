import os
from PIL import Image, ImageDraw, ImageFont
import textwrap
from moviepy import VideoFileClip
import json
font_path = "/mnt/d/Personal/PromptSpeech/Amiri/Amiri-Bold.ttf"

def text_file_to_image(output_path, captionText, captionPath=None, font_size=48, image_size=(800, 600)):
    """
    Reads a text file, removes the first line, and generates an image 
    with the text centered on it.

    Args:
        input_path (str): Path to the text file.
        output_path (str): Path to save the generated image.
        font_path (str): Path to a .ttf font file (optional).
        font_size (int): Font size for the text.
        image_size (tuple): (width, height) of the output image.
    """
    # Read and clean the text
    if(captionPath!=None):
        with open(captionPath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        text = ''.join(lines[1:]).strip()  # remove first line
    else:
        text = captionText
    
    if not text:
        raise ValueError("The text file is empty after removing the first line.")

    # Create blank image
    img = Image.new("RGB", image_size, color="white")
    draw = ImageDraw.Draw(img)

    # Load font (use default if none provided)
    try:
        font = ImageFont.truetype(font_path or "arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Wrap text to fit width
    wrapper = textwrap.TextWrapper(width=50)
    wrapped_text = "\n".join(wrapper.wrap(text))

    # Measure text size
    text_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, align="center")
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Calculate centered position
    x = (image_size[0] - text_width) / 2
    y = (image_size[1] - text_height) / 2

    # Draw text
    draw.multiline_text((x, y), wrapped_text, fill="black", font=font, align="center")

    # Save image
    img.save(output_path)
    return
   

def create_image_allAudio(input_path, font_size=48, image_size=(800, 600)):
    """
    Processes all text files in the given directory and its subdirectories,
    generating an image for each text file with the text centered on it.

    """
    if not os.path.isdir(input_path):
        raise ValueError(f"Provided path '{input_path}' is not a valid directory.")
    i = 0
    # Iterate over immediate subfolders
    for folder_name in os.listdir(input_path):
        folder_OneYearPath = os.path.join(input_path, folder_name)
        i = i + 1
        if os.path.isdir(folder_OneYearPath):
            print(f"Processing subfolder: {folder_name}  {i}/ {len(os.listdir(folder_OneYearPath))} folders")
            # Call the existing function on this folder
            j = 0
            for folderVideoName in os.listdir(folder_OneYearPath):
       
                j = j + 1
                folder_path = os.path.join(folder_OneYearPath, folderVideoName)
                print(f"Processing subfolder: {folderVideoName}  {j}/ {len(os.listdir(folder_OneYearPath))} folders")
                if os.path.isdir(folder_path):
                    captions_file = os.path.join(folder_path, "caption.txt")
                    if os.path.isfile(captions_file):
                        output_path =os.path.join(folder_path, "caption.png")
                        text_file_to_image(output_path, " ", captions_file, font_size, image_size)

def convert_mp4_to_wav(videoPath,wav_path):
   
        try:
            video = VideoFileClip(videoPath)
            video.audio.write_audiofile(wav_path, codec='pcm_s16le')  # Save as WAV
            video.close()
        except Exception as e:
            print(f"Error processing {videoPath}: {e}")

def merge_transcribed_chunks(transcribed_path: str, n: int, overlap: int=0):
    """
    Merges every n consecutive transcribed chunks (keys) into one chunk,
    breaks early if speakers differ
    Input:
        transcribed_path: path of transcribed file (JSON format)
        n: Number of consecutive chunks to merge
        overal: number of overlap chunks
    Output:        
        merged: Merged JSON dictionary
    """
    # Load input JSON
    with open(transcribed_path, "r", encoding="utf-8") as f:
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
    chunklength = int(n*30)
    overalpLength = int(overlap*30)
    dataFolderName = f"Transcription_{chunklength}Sec_Overlap_{overalpLength}Sec"
    #
    Mainfolder_path = os.path.dirname(transcribed_path)
    Mainfolder_path = os.path.dirname(Mainfolder_path)
    output_dir = os.path.join(Mainfolder_path,dataFolderName)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir,f"{dataFolderName}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=4, ensure_ascii=False)
    return output_path


if __name__ == "__main__":
    folder_allData_path = "/mnt/d/Personal/PromptSpeech/videosPerYear"
    
    create_image_allAudio(folder_allData_path)