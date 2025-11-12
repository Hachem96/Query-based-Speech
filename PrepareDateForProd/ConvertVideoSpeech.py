from moviepy import VideoFileClip
import os
import shutil
import re

def convert_mp4OneFolder_to_wav(root_folder):
    for subdir, _, files in os.walk(root_folder):
        for file in files:
            if file.lower().endswith(".mp4"):
                mp4_path = os.path.join(subdir, file)
                wav_path = os.path.join(subdir, os.path.splitext(file)[0] + ".wav")
                print(f"Converting: {mp4_path} -> {wav_path}")
                convert_mp4_to_wav(mp4_path,wav_path):
                  
                   
def convert_mp4_to_wav(videoPath,wav_path):
   
        try:
            video = VideoFileClip(videoPath)
            video.audio.write_audiofile(wav_path, codec='pcm_s16le')  # Save as WAV
            video.close()
        except Exception as e:
            print(f"Error processing {mp4_path}: {e}")
if __name__ == "__main__":
    

    # Replace these with your details
    
    output_folder = "/mnt/d/Personal/PromptSpeech/videosPerYear"
    # read_fromTelegramChanngel(api_id,api_hash,phone,channel_username,base_download_folder)
    # organize_by_year(base_download_folder, output_folder)
    convert_mp4_to_wav(output_folder)