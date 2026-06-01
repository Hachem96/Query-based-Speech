# Hebrew Video Transcription and Evaluation

This project builds and evaluates a Hebrew ASR transcription pipeline.

It includes video transcription, audio extraction, speaker diarization, Hebrew transcription, transcript export, model comparison, and result saving.

The project was tested on three datasets to compare model performance across different Hebrew speech sources.

---

## Project Overview

The project includes:

- Hebrew video/audio transcription
- Speaker diarization
- Transcript export to JSON and PDF
- Model evaluation using WER and CER
- Comparison between Hebrew-specific and multilingual ASR models

---

## Datasets

This project worked on three datasets:

- **Dataset 1:** Main Hebrew speech dataset used for model evaluation
- **Dataset 2:** Additional Hebrew transcription dataset used for comparison
- **YouTube Hebrew Dataset:** Real-world Hebrew video/audio dataset

The use of three datasets helped compare model performance on both cleaner audio and real-world audio.

---

## Models Used

### Transcription Models

- `openai/whisper-large-v3`
- `openai/whisper-large-v3-turbo`
- `ivrit-ai/whisper-large-v3`
- `ivrit-ai/whisper-large-v3-turbo`
- `OzLabs/Caspi-1.7B`
- `facebook/seamless-m4t-v2-large`
- `Qwen/Qwen3-ASR-1.7B`

### Diarization Models

- `pyannote/speaker-diarization-3.1`
- `pyannote/speaker-diarization-community-1`

`Qwen/Qwen3-ASR-1.7B` was tested but removed from the final Hebrew evaluation because Hebrew is not officially supported.

---

## YouTube Evaluation Results

| Rank | Model | WER | CER |
|---:|---|---:|---:|
| 1 | `ivrit_ai_whisper_large_v3` | 0.1196 | 0.0852 |
| 2 | `ivrit_ai_whisper_large_v3_ct2` | 0.1225 | 0.0877 |
| 3 | `ivrit_ai_whisper_large_v3_turbo_ct2` | 0.1250 | 0.0878 |
| 4 | `ivrit_ai_whisper_large_v3_turbo` | 0.1260 | 0.0887 |
| 5 | `caspi_1_7b` | 0.1427 | 0.0928 |
| 6 | `openai_whisper_large_v3_turbo` | 0.1450 | 0.0914 |
| 7 | `openai_whisper_large_v3` | 0.1459 | 0.0926 |

---

## Results Summary

The best model in the YouTube evaluation was:

```text
ivrit_ai_whisper_large_v3
## YouTube Evaluation Conclusion

The best model in the YouTube evaluation was `ivrit_ai_whisper_large_v3`.

It achieved the lowest WER and CER.

The `ivrit.ai` models were the strongest models overall in the YouTube evaluation.

`Caspi-1.7B` worked successfully and performed better than the OpenAI Whisper models in WER, but it was still weaker than the `ivrit.ai` models.

---

## General Conclusions

The strongest model overall was usually the Hebrew-specific `ivrit.ai` model.

It performed best on:

* SASpeech
* YouTube Hebrew video evaluation
* Dataset 1 WER

`Caspi-1.7B` also performed well, especially in character-level accuracy on Dataset 1.

`Whisper large-v3` was a good general model, but it was not the best model for Hebrew in these experiments.

`SeamlessM4T` was tested, but it was weaker than the Hebrew-specific models in the SASpeech experiment.

---

## Important Observations

Dataset quality strongly affected the results.

Clean studio audio gave better scores, while real-world audio produced worse results because of noise, interruptions, overlapping speech, informal speech, slang, and microphone quality.

Hebrew-specific models performed better than general multilingual models, especially the `ivrit.ai` models.

---

## How to Use

### 1. Clone the repository

```bash
git clone https://github.com/mhmddirany/Video-Transcription-Hebrew-ASR-Pipeline.git
cd Video-Transcription-Hebrew-ASR-Pipeline
```

### 2. Install requirements

```bash
pip install -r requirements.txt
```

In Google Colab, most required libraries are installed automatically inside the notebooks.

### 3. Add Hugging Face Token

Some models require a Hugging Face token.

In Colab, add the token in **Colab Secrets** using the name:

```text
HF_TOKEN
```

Do not write the token directly inside the notebook.

### 4. Run the Transcription Notebook

Open:

```text
notebooks/video_transcription_pipeline.ipynb
```

Set the video path:

```python
MP4_PATH = "/content/drive/MyDrive/hebrew/video.mp4"
```

Set the output folder:

```python
OUTPUT_DIR = "/content/drive/MyDrive/output"
```

Then run the notebook cells from top to bottom.

### 5. Run the Evaluation Notebooks

Open one of the evaluation notebooks:

```text
notebooks/dataset1_transcription_model_evaluation.ipynb
notebooks/dataset2_transcription_model_evaluation.ipynb
notebooks/youtube_hebrew_transcription_model_evaluation.ipynb
```

---

## Output Files

The project can generate several output files.

### Transcript Outputs

* `.json`
* `.pdf`

### Evaluation Outputs

* `.csv`
* `.xlsx`

Example output files:

```text
SUMMARY_WER_CER.csv
SUMMARY_WER_CER.xlsx
ALL_MODEL_RESULTS.csv
ALL_MODEL_RESULTS.xlsx
```

---

## Notes

* Video files are not uploaded to GitHub.
* Hugging Face tokens are not saved in the notebooks.
* Large output files should not be committed unless needed.
* The notebooks are designed mainly for Google Colab.
* Results may change depending on GPU, package versions, preprocessing, and text normalization.
