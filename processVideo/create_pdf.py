from itertools import count
from pathlib import Path
import markdown
from weasyprint import HTML
import os
from openai import OpenAI
from processVideo.common import text_file_to_image
import subprocess
def create_pdf_correctedTranscription(correctedTranscriptionPath, caption,videoName):
    with open(correctedTranscriptionPath, "r", encoding="utf-8") as f:
        md_content = f.read()
    # Load caption text file
   

    # Extract title and header lines
    if caption:
    # Split into lines safely
        lines = [line.strip() for line in caption.splitlines()]

        # First line is title
        title = lines[0] if lines else ""

        # Remaining non-empty lines become headers
        header_lines = [l for l in lines[1:] if l]   # remove empty lines
    else:
        title = ""
        header_lines = []

    # Build caption markdown block
    caption_md = ""

    # Add title
    if title:
        caption_md += f"# {title}\n"

    # Add remaining lines as second-level headers
    for line in header_lines:
        caption_md += f"## {line}\n"

        # Merge with original markdown content
        merged_md = caption_md + md_content

    # Convert merged markdown to HTML
    html_content = markdown.markdown(
        merged_md,
        extensions=['extra', 'tables', 'fenced_code']
    )

    # HTML template with justified RTL text
    html_template = f"""
    <html lang="ar" dir="rtl">
    <head>
    <meta charset="UTF-8">
    <style>
    @font-face {{
        font-family: 'Amiri';
        src: url('Amiri-Regular.ttf') format('truetype');
    }}
    body {{
        font-family: 'Amiri', serif;
        direction: rtl;

        text-align: justify;      /* Justify full lines */
        text-align-last: right;   /* Do NOT justify last line */

        line-height: 1.6;
        font-size: 13pt;
        margin: 0.3cm;
    }}
    </style>
    </head>
    <body>
    {html_content}
    </body>
    </html>
    """
    
    output_pdf_path = os.path.join(os.path.dirname(correctedTranscriptionPath), f"transcription_{videoName}.pdf")
    HTML(string=html_template).write_pdf(output_pdf_path)
    return output_pdf_path

def correctTranscriptionText(transcriptionPath,videoName):
   
    promptContent = "صحح الاخطاء في هذا النص واجمع الفقرات بطريقة مناسبة، لا تغير أي كلمة في النص ولا تزد اي كلمة، ابقي النص كما هو، صحح فقط الاخطاء الاملائية واجمع المقاطع بطريقة مناسبة لتكوين فكرات متناسقة وكاملة المعنى. أريد ان انسخ النص التي ستعطيه، فلا تزد اي عبارة اضافية عن النص المصحح مثل: حسنا اليك النص المصحح، هذا هو نصك المصحح، ..."

    promptContent += "\n"
    promptContent += "النص هو:\n"

    with open(transcriptionPath, "r", encoding="utf-8") as f:
        speechTranscContent = f.read()

    

    lines = speechTranscContent.split("\n\n")
    count = len(lines) 
    print(count)
    client = OpenAI(
        api_key= os.getenv("API_KEY_DEEPSEEK"),  #
        base_url="https://api.deepseek.com/v1", #"https://dashscope-intl.aliyuncs.com/compatible-mode/v1",  
    )
    
    
    correctAllChunks = False
    allOutput = ""
    i = 0
    while correctAllChunks==False:
        lines = speechTranscContent.split("\n\n")
        count = len(lines)
        
        if count > 120:
            parttsContent = "\n\n".join(lines[:120])
            speechTranscContent = "\n\n".join(lines[120:])
        else:
            parttsContent = speechTranscContent
            correctAllChunks = True
        
        fullPrompt = promptContent + "\n" + parttsContent
        
        i += 1
        fullPrompt = promptContent + "\n" + parttsContent
        with open(f"debug_prompt_{i}.txt", "w", encoding="utf-8") as f:
            f.write(fullPrompt)

        completion = client.chat.completions.create(
            model="deepseek-reasoner", #qwen3-max",
            messages=[
                {"role": "system", "content": "أنت مدقق لغوي في اللغة العربية"},
                {"role": "user", "content": fullPrompt},
            ],
            stream=False
        )
        output = completion.choices[0].message.content
        allOutput += output + "\n"
    
    outputPath = os.path.join(os.path.dirname(transcriptionPath), f"correctedTranscription_{videoName}.txt")
    with open(outputPath, "w", encoding="utf-8") as f:
        f.write(allOutput)
    return outputPath



def corectTranscription_CreatePdf_allVideos(mainFolderPath):
    for folder1 in os.listdir(mainFolderPath):
        i = 0
        folder_yearpath = os.path.join(mainFolderPath, folder1)
        print(f"Processing year folder: {folder1}")
        for folder_name in os.listdir(folder_yearpath):
            folder_path = os.path.join(folder_yearpath, folder_name)
            i = i+1
            print(f"Processing folder {i}/{len(os.listdir(mainFolderPath))}: {folder_name}")
            if os.path.isdir(folder_path):
                transcriptionPath = os.path.join(folder_path, "Transcription")
                if(os.path.exists(transcriptionPath)):
                    transcription_textPath = os.path.join(transcriptionPath, "transcription_full_text.txt")
                    correctTranscPath = os.path.join(transcriptionPath, f"correctedTranscription_{folder_name}.txt")
                    if os.path.exists(correctTranscPath):
                        print(f"Corrected transcription already exists for {folder_name}, skipping correction.")
                        correctTranscriptionPath = correctTranscPath
                    else:
                        correctTranscriptionPath = correctTranscriptionText(transcription_textPath,folder_name)

                    captionPath = os.path.join(folder_path, "caption.txt")
                    with open(captionPath, "r", encoding="utf-8") as f:
                        caption = f.read()                   
                    output_pdf_path = create_pdf_correctedTranscription(correctTranscriptionPath, caption,folder_name)
                else:
 
                    print(f"No transcription file found in {folder_name}")


def arabic_chapter_title(filename, header_lines):
    """Generate an Arabic chapter title from filename."""
    #name = Path(filename).stem.replace("-", " ").replace("_", " ")
    caption_md = ""
    for line in header_lines:
        caption_md += f"{line.strip()} "
    return f"# {filename}: {caption_md}\n"

def create_pdf_videos_list(listFolderPath,outdirPath, templateLatexPath):
    i = 0
    parts = []
    outputFolderName = ""
    bookTitle = "خطابات السيد: " 
    bookTitle += "\n\n"
    bookTitle += f"{len(listFolderPath)} خطاب "
    bookTitle += "\n\n"
    bookTitle += "من "
    bookTitle += "\n\n"
    for folder_path in listFolderPath:
        
        folder_name = os.path.basename(folder_path)
        i = i+1
        
        #print(f"Processing folder {i}/{len(os.listdir(mainFolderPath))}: {folder_name}")
        if os.path.isdir(folder_path):
            transcriptionPath = os.path.join(folder_path, "Transcription")
            correctedTransc = os.path.join(transcriptionPath, f"correctedTranscription_{folder_name}.txt")
            if os.path.exists(correctedTransc):
                with open(correctedTransc, "r", encoding="utf-8") as f:
                    content = f.read()
                captionPath = os.path.join(folder_path, "caption.txt")
                # 1) Merge markdown files
                
                caption_lines = Path(captionPath).read_text(encoding="utf-8").strip().splitlines()
               
                # Extract title and header lines
                if caption_lines:
                    title = caption_lines[0].strip()
                    header_lines = caption_lines[1:]  # remaining lines
                else:
                    header_lines = []
                if(len(parts)==0):
                    bookTitle += title
                    outputFolderName += folder_name
                # Insert arabic chapter heading at the top of each file
                chapter_title = arabic_chapter_title(title, header_lines)
                parts.append(chapter_title)
                parts.append(content)
                parts.append("\n\n\\newpage\n\n")

    bookTitle += "\n\n"
    bookTitle += " إلى "
    bookTitle += "\n\n"
    bookTitle += title
    
    outputFolderName += "_" + folder_name
    outdirPath = os.path.join(outdirPath, outputFolderName)
    os.makedirs(outdirPath, exist_ok=True)
    # 1) Write merged markdown file
    merged_mdPath = Path(os.path.join(outdirPath, f"{outputFolderName}.md"))
    output_pdfPath = Path(os.path.join(outdirPath, f"{outputFolderName}.pdf"))
    
    # create cover image and caption file
    captionPath = os.path.join(outdirPath, "caption.txt")
    with open(captionPath, "w", encoding="utf-8") as f:
        f.write(bookTitle)
    coverOutput_path = os.path.join(outdirPath, "cover.png")
    text_file_to_image(coverOutput_path, bookTitle, captionPath=None, font_size=36, image_size=(600, 800))
    merged_mdPath.write_text("\n".join(parts), encoding="utf-8")

    print("Merged markdown created.")

    # 2) Call Pandoc with XeLaTeX and Arabic template
    cmd = [
        "pandoc",
        str(merged_mdPath),
        "--from=markdown",
        "--pdf-engine=xelatex",
        f"--template={templateLatexPath}",
        "--toc",
        "--variable=lang:ar",
        "--variable=documentclass:book",
        f"--variable=title:{bookTitle}",
        "-o", str(output_pdfPath),
    ]

    print("Running Pandoc...")
    subprocess.run(cmd, check=True)

    print("PDF created:", output_pdfPath)

def create_books_from_videos(mainFolderPath, outputPath, templateLatexPath):
    nb_speeches_per_book = 40
    nbBook = 0
    listFolderPath = []
    for folder1 in os.listdir(mainFolderPath):
        folder_yearpath = os.path.join(mainFolderPath, folder1)
        print(f"Processing year folder: {folder1}")
        for folder_name in os.listdir(folder_yearpath):
            folder_path = os.path.join(folder_yearpath, folder_name)        
            if os.path.isdir(folder_path):
                listFolderPath.append(folder_path)
                if len(listFolderPath) == nb_speeches_per_book:
                    nbBook += 1
                    firstFolder = os.path.basename(listFolderPath[0])
                    lastFolder = os.path.basename(listFolderPath[-1])
                    print(f"Creating book {nbBook} from {firstFolder} to {lastFolder}...")
                    create_pdf_videos_list(listFolderPath, outputPath, templateLatexPath)
                    listFolderPath = []
    
    if listFolderPath:
        create_pdf_videos_list(listFolderPath, outputPath, templateLatexPath)
    
    return
                
    
if __name__ == "__main__":
    mainFolderPath = "/mnt/d/Personal/PromptSpeech/videosPerYear"
    #corectTranscription_CreatePdf_allVideos(mainFolderPath)
    template = "/mnt/d/Personal/PromptSpeech/Pdf_AllSpeech/template.tex"
    outputPath = "/mnt/d/Personal/PromptSpeech/Pdf_AllSpeech"
    create_books_from_videos(mainFolderPath, outputPath, template)