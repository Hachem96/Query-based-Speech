# Data Ingestion (processVideo)

This directory contains scripts and utilities for ingesting new content (Videos and Books) into the Query-based Speech Retrieval platform.

## Key Scripts

### `addNewVideo.py`
The main script for processing video files. It performs the following steps:
1.  **Ingestion**: Reads the MP4 video file and extract audio.
2. **create a cover image**: using the video title and year.
3.  **Transcription**: Converts audio to text using ASR.
4.  **Pdf Generation**: correct transcription through LLM model and generate pdf file.
5.  **Chunking**: Splits the transcript into manageable chunks.
6.  **Embedding**: Generates vector embeddings for each chunk.
7.  **Storage**: Saves the video metadata, transcript chunks, and embeddings to the database.

**Usage:**
check the `__name__ == "__main__"` block in the file for examples.
```python
from processVideo.addNewVideo import add_new_video, add_all_videos

# Add a single video
add_new_video(
    videoName="My Video",
    year="2024",
    mp4Path="/path/to/video.mp4",
    caption="Video description",
    transcribe=True,
    correctTranscription=True,
    makeSummary=False
)

# Add all videos from a directory structure (VideosPerYear/Year/Video)
add_all_videos(basePath="/path/to/VideosPerYear", transcribe=True)
```

### `addNewBook.py`
add the information of a new book to the database (name, year, linktoCover, linkToPdf, author,etc)

### `create_pdf.py`
Helper script to generate PDF files (likely for transcriptions or summaries).

### `ConvertVideoSpeech.py`
Utility to extract audio from video files

## Workflow to add list of videos

1.  Place your media files in the appropriate directory.
2.  Update the paths in the `__main__` block of the relevant script (e.g., `addNewVideo.py`).
3.  Run the script:
    ```bash
    python -m processVideo.addNewVideo
    ```
