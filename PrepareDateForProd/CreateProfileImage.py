import os
from PIL import Image, ImageDraw, ImageFont
import textwrap

def text_file_to_image(input_path, output_path, font_path, font_size=48, image_size=(800, 600)):
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
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    text = ''.join(lines[1:]).strip()  # remove first line
    
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
   

def create_image_allAudio(input_path, font_path, font_size=48, image_size=(800, 600)):
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
                        text_file_to_image(captions_file, output_path, font_path, font_size, image_size)

if __name__ == "__main__":
    folder_allData_path = "/mnt/d/Personal/PromptSpeech/videosPerYear"
    font_path = "/mnt/d/Personal/PromptSpeech/Amiri/Amiri-Bold.ttf"
    create_image_allAudio(folder_allData_path, font_path)