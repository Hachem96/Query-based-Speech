import glob
from processVideo.common import*
#from ASR.SpeechTextConversion import transcribe_One_Speech
import os
from backend.DataBaseFunctions import*
from pathlib import Path





def bookIsExist(configuration,Titlle,author):
    connection, cursor = connectTodatabase()
    check_query = 'SELECT 1 FROM "Book" WHERE "Title" = %s AND "Author" = %s LIMIT 1;'
    cursor.execute(check_query, (Titlle, author))
    exists = cursor.fetchone()

    if exists:
        return True
    else:
        return False
    
def add_new_book(title,linkToBook, linktoCover, caption="Not Available", author="Unknown", year=0):
    
    exist = bookIsExist(title, author)
    if exist:
        print(f"Book '{title}' by '{author}' already exists in the database. Skipping addition.")
        return
    table_name = "Book"
    book_info = {
        "Title": title,
        "linkToPdf": linkToBook,
        "linkToCover": linktoCover,
        "caption": caption,
        "Author": author,
        "Year": year
    }

    bookId = add_row(table_name, book_info)
    print(f"Added new book: {title}")
    return

def initialize_books_table(bookPath):
      IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp")
      for folder_name in os.listdir(bookPath):
            folder_path = os.path.join(bookPath, folder_name)

            # Skip if not a folder
            if not os.path.isdir(folder_path):
                continue

            # Get all PDF files in the folder
            pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]

            # Skip if zero or more than one PDF
            if len(pdf_files) != 1:
                print(f"Skipping {folder_name}: found {len(pdf_files)} PDF files.")
                continue

            pdf_file = pdf_files[0]
            pdf_path = os.path.join(folder_path, pdf_file)

            # Check for cover.png
            image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(IMAGE_EXTENSIONS)]

            if not image_files:
                print(f"Skipping {folder_name}: no image files found for cover.")
                print("book is not added to database")
                continue

            if len(image_files) == 1:
                cover_file = image_files[0]
            else:
                # Look for one named 'cover' ignoring extension
                cover_candidates = [f for f in image_files if os.path.splitext(f)[0].lower() == "cover"]
                if cover_candidates:
                    cover_file = cover_candidates[0]
                else:
                    # If no 'cover' named image, skip
                    print(f"Skipping {folder_name}: multiple image files found, none named 'cover'.")
                    print("book is not added to database")
                    continue
            coverPath = os.path.join(folder_path, cover_file)
            captionPath = os.path.join(folder_path, "caption.txt")
            with open(captionPath, 'r', encoding='utf-8') as f:
                caption = f.read().strip()
            # If everything is valid, push to database
            pdf_path = os.path.join("videosPerYear/Pdf_AllSpeech", folder_name, os.path.basename(pdf_file))
            coverPath = os.path.join("videosPerYear/Pdf_AllSpeech", folder_name, os.path.basename(cover_file))
            add_new_book(caption, pdf_path, coverPath, year=2025, author="سيد حسن")

if __name__ == "__main__":
    bookPath = "/mnt/d/Personal/PromptSpeech/videosPerYear/Pdf_AllSpeech"
    initialize_books_table(bookPath)