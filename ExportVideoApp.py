from telethon import TelegramClient
import os
from moviepy import VideoFileClip
import os
import shutil
import re

def organize_by_year(input_folder, output_folder):
    # Create output folder if not exists
    os.makedirs(output_folder, exist_ok=True)

    # Loop through all subfolders
    for item in os.listdir(input_folder):
        item_path = os.path.join(input_folder, item)

        if os.path.isdir(item_path):
            # Look for a .txt file inside this folder
            txt_files = [f for f in os.listdir(item_path) if f.endswith(".txt")]
            if not txt_files:
                continue  # skip if no caption file

            caption_file = os.path.join(item_path, txt_files[0])

            # Read the caption file and search for a year between 2000-2024
            with open(caption_file, "r", encoding="utf-8") as f:
                text = f.read()
            
            match = re.search(r"\b(200[0-9]|201[0-9]|202[0-4])\b", text)
            if not match:
                print(f"No valid year found in {caption_file}")
                continue

            year = match.group(0)

            # Create year folder inside output
            year_folder = os.path.join(output_folder, year)
            os.makedirs(year_folder, exist_ok=True)

            # Destination path for the whole folder
            dest_path = os.path.join(year_folder, item)

            # Copy entire folder (video + caption)
            if os.path.exists(dest_path):
                print(f"Skipping {item} - already exists in {year_folder}")
            else:
                shutil.copytree(item_path, dest_path)

    print("Organization completed!")

def read_fromTelegramChanngel(api_id,api_hash,phone,channel_username,base_download_folder):
    # Where to save videos
   
    os.makedirs(base_download_folder , exist_ok=True)



    client = TelegramClient('session_name', api_id, api_hash)

    async def readFromChannel():
        channel = await client.get_entity(channel_username)

        async for message in client.iter_messages(channel):
            if message.video:
                # Get file name
                file_name = None
                if message.file and message.file.name:
                    file_name = message.file.name
                else:
                    file_name = f"video_{message.id}.mp4"
                folder_name = os.path.splitext(file_name)[0]
                folder_path = os.path.join(base_download_folder, folder_name)
                if os.path.exists(folder_path):
                    print(f"Skipping '{file_name}' (already exists).")
                else:
                    os.makedirs(folder_path, exist_ok=True)
                    # Video path
                    video_path = os.path.join(folder_path, file_name)

                    # Download video
                    print(f"Downloading: {file_name}")
                    await message.download_media(video_path)

                    # Get caption/message
                    caption = message.text if message.text else ""
                    if caption:
                        caption_file = os.path.join(folder_path, "caption.txt")
                        with open(caption_file, "w", encoding="utf-8") as f:
                            f.write(caption)
                        print(f"Saved caption to {caption_file}")
    with client:
        client.loop.run_until_complete(readFromChannel())

def convert_mp4_to_wav(root_folder):
    for subdir, _, files in os.walk(root_folder):
        for file in files:
            if file.lower().endswith(".mp4"):
                mp4_path = os.path.join(subdir, file)
                wav_path = os.path.join(subdir, os.path.splitext(file)[0] + ".wav")

                try:
                    print(f"Converting: {mp4_path} -> {wav_path}")
                    video = VideoFileClip(mp4_path)
                    video.audio.write_audiofile(wav_path, codec='pcm_s16le')  # Save as WAV
                    video.close()
                except Exception as e:
                    print(f"Error processing {mp4_path}: {e}")
if __name__ == "__main__":
    

    # Replace these with your details
    api_id = 26860339       # your API ID
    api_hash = '7b01d9b55b6b7adcf14446a017e46d20'
    phone = '+33772204196' # your phone number with country code
    channel_username = 'sayyed_speeches'  # e.g. 'my_channel'
    base_download_folder = "/mnt/d/Personal/PromptSpeech/videos"
    output_folder = "/mnt/d/Personal/PromptSpeech/videosPerYear"
    # read_fromTelegramChanngel(api_id,api_hash,phone,channel_username,base_download_folder)
    # organize_by_year(base_download_folder, output_folder)
    convert_mp4_to_wav(output_folder)