# 🎙️ YouTube to Whisper Transcription UI

A user-friendly web interface to download YouTube audio and transcribe it using OpenAI's Whisper.

## ✨ Features

- **YouTube & File Input**: Transcribe from YouTube URLs or local audio files.
- **Organized Storage**: Automatically saves audio and transcripts to a `transcriptions/` folder, organized by video title.
- **Multiple Whisper Models**: Choose from `tiny`, `base`, `small`, `medium`, or `large` for a balance of speed and accuracy.
- **Language Support**: Auto-detect or manually select from dozens of languages.
- **Translation to English**: Translate any supported language into English.
- **Multiple Export Formats**: Get transcripts as `TXT`, `SRT`, `VTT`, and `JSON`.

## 🚀 Quick Start

### 1. Create the Environment

First, set up the `whisper` conda environment using the provided file. This ensures you have all the correct packages.

```powershell
conda env create -f environment.yml
```

### 2. Run the Application

Once the environment is created, you can start the app.

**Method 1: Batch File (Easiest)**
Simply double-click `run_app.bat`.

**Method 2: Manual Start**
```powershell
conda activate whisper
python app.py
```

The application will open in your browser at **http://127.0.0.1:7860**.

## 📖 How to Use

1.  **Paste a YouTube URL** or **upload an audio file**.
2.  **Select a Whisper Model** (start with `base` for a good balance).
3.  Choose your **Language** (`auto` is usually fine).
4.  Select the **Task** (`transcribe` or `translate`).
5.  Choose any **Export Formats** you need.
6.  Click **"🚀 Download & Transcribe"** or **"🚀 Transcribe"**.

Your files will be saved in the `transcriptions` folder.

## 🛠️ Technical Details

- **Environment**: The conda environment is managed by `environment.yml`.
- **Downloader**: Uses the `yt-dlp` Python package. 
- **File Structure**: All output is saved in `D:\ML\whisper\transcriptions\[Video Title]\`.

## 🔧 Troubleshooting

- _MAY THE AI LORD BE WITH YOU_
---
*This project uses OpenAI's Whisper and the yt-dlp project.*
