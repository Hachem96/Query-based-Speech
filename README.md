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
