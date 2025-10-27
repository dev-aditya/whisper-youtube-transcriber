"""
YouTube to Whisper Transcription UI
A Gradio-based application for downloading YouTube audio and transcribing with Whisper
"""

import gradio as gr
import whisper
import yt_dlp
import os
import tempfile
from pathlib import Path
import json
from datetime import datetime


class WhisperTranscriber:
    def __init__(self):
        self.model = None
        self.model_name = None
        # use Python yt_dlp from the active environment
        self.yt_dlp = yt_dlp

    def load_model(self, model_name):
        """Load Whisper model if not already loaded or if different model requested"""
        if self.model is None or self.model_name != model_name:
            self.model = whisper.load_model(model_name)
            self.model_name = model_name
            return f"✓ Model '{model_name}' loaded successfully"
        return f"✓ Model '{model_name}' already loaded"

    def get_video_title(self, url):
        """Get YouTube video title for folder naming"""
        try:
            ydl_opts = {"quiet": True, "no_warnings": True}
            with self.yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            title = info.get("title") or info.get("id")
            # Clean title for use as folder name (remove invalid characters)
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                title = title.replace(char, "")
            # Limit length to avoid path issues
            if len(title) > 100:
                title = title[:100]
            return title
        except Exception:
            # Fallback to timestamp if title fetch fails
            return f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def download_youtube_audio(self, url, progress=gr.Progress()):
        """Download highest quality audio from YouTube URL"""
        try:
            progress(0, desc="Getting video info...")

            # Get video title for folder name
            video_title = self.get_video_title(url)

            # Create transcriptions directory structure
            base_dir = Path(__file__).parent / "transcriptions"
            video_dir = base_dir / video_title
            video_dir.mkdir(parents=True, exist_ok=True)

            output_template = str(video_dir / "audio.%(ext)s")

            # Use yt-dlp Python API to download best audio and extract to mp3
            def progress_hook(d):
                status = d.get("status")
                if status == "downloading":
                    # show progress line
                    filename = d.get("filename")
                    downloaded = d.get("downloaded_bytes")
                    total = d.get("total_bytes") or d.get("total_bytes_estimate")
                    if total:
                        pct = downloaded / total * 100 if downloaded and total else 0
                        print(f"[download] {filename} {pct:0.1f}% ({downloaded}/{total} bytes)")
                    else:
                        print(f"[download] {filename} bytes={downloaded}")
                elif status == "finished":
                    print(f"[download] Finished downloading: {d.get('filename')}")

            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": output_template,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "0",
                    }
                ],
                "progress_hooks": [progress_hook],
                "quiet": True,
                "no_warnings": True,
            }

            progress(0.3, desc="Downloading audio from YouTube...")
            print(f"\n{'='*60}")
            print(f"📥 Downloading: {video_title}")
            print(f"{'='*60}")

            with self.yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            print(f"{'='*60}")
            print(f"✅ Download complete!")
            print(f"{'='*60}\n")

            # Find the downloaded file (should be audio.mp3 after extraction)
            audio_file = None
            for file in os.listdir(video_dir):
                if file.startswith("audio"):
                    audio_file = str(video_dir / file)
                    break

            if audio_file and os.path.exists(audio_file):
                progress(1.0, desc="Download complete!")
                return audio_file, video_dir, None
            else:
                return None, None, "Failed to find downloaded audio file"

        except Exception as e:
            return None, None, f"Download failed: {str(e)}"

    def transcribe_audio(
        self, audio_path, model_name, language, task, progress=gr.Progress()
    ):
        """Transcribe audio file using Whisper"""
        try:
            progress(0, desc="Loading model...")
            print(f"\n{'='*60}")
            print(f"🎙️ Loading Whisper model: {model_name}")
            print(f"{'='*60}")
            self.load_model(model_name)

            progress(0.2, desc="Transcribing audio...")
            print(f"🔄 Transcribing audio...")
            print(f"   Language: {language if language != 'auto' else 'Auto-detect'}")
            print(f"   Task: {task}")
            print(f"{'='*60}")

            # Transcription options
            options = {
                "task": task,
                "verbose": True,
            }  # Changed to True for terminal output

            if language != "auto":
                options["language"] = language

            # Transcribe
            result = self.model.transcribe(audio_path, **options)

            progress(1.0, desc="Transcription complete!")
            print(f"{'='*60}")
            print(f"✅ Transcription complete!")
            print(f"   Detected language: {result.get('language', 'Unknown')}")
            print(f"   Segments: {len(result['segments'])}")
            print(f"{'='*60}\n")

            return result

        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")

    def process_youtube_url(
        self, url, model_name, language, task, include_timestamps, export_formats
    ):
        """Complete pipeline: download from YouTube and transcribe"""

        if not url:
            return "Please enter a YouTube URL", None, None, None, None

        # Download audio
        yield "📥 Downloading audio from YouTube...", None, None, None, None
        audio_path, video_dir, error = self.download_youtube_audio(url)

        if error:
            yield f"❌ Download Error: {error}", None, None, None, None
            return

        yield f"✓ Audio downloaded\n🎙️ Transcribing with Whisper ({model_name})...", audio_path, None, None, None

        # Transcribe
        try:
            result = self.transcribe_audio(audio_path, model_name, language, task)

            # Format output
            text_output = result["text"].strip()

            # Generate detailed output with timestamps if requested
            detailed_output = ""
            if include_timestamps:
                detailed_output = self.format_with_timestamps(result["segments"])

            # Save transcript as text file in the same folder
            transcript_file = video_dir / "transcript.txt"
            with open(transcript_file, "w", encoding="utf-8") as f:
                f.write(text_output)

            # Save detailed transcript with timestamps if requested
            if include_timestamps:
                detailed_file = video_dir / "transcript_with_timestamps.txt"
                with open(detailed_file, "w", encoding="utf-8") as f:
                    f.write(detailed_output)

            # Prepare export files and save to video folder
            exports = {}
            if export_formats:
                if "srt" in export_formats:
                    srt_content = self.format_srt(result["segments"])
                    srt_file = video_dir / "transcript.srt"
                    with open(srt_file, "w", encoding="utf-8") as f:
                        f.write(srt_content)
                    exports["srt"] = srt_content
                if "vtt" in export_formats:
                    vtt_content = self.format_vtt(result["segments"])
                    vtt_file = video_dir / "transcript.vtt"
                    with open(vtt_file, "w", encoding="utf-8") as f:
                        f.write(vtt_content)
                    exports["vtt"] = vtt_content
                if "json" in export_formats:
                    json_content = json.dumps(result, indent=2)
                    json_file = video_dir / "transcript.json"
                    with open(json_file, "w", encoding="utf-8") as f:
                        f.write(json_content)
                    exports["json"] = json_content

            status = f"✅ Transcription Complete!\n\n"
            status += f"Language: {result.get('language', 'Unknown')}\n"
            status += f"Duration: ~{len(result['segments'])} segments\n"
            status += f"📁 Saved to: {video_dir}"

            yield (
                status,
                audio_path,
                text_output,
                detailed_output,
                self.create_export_files(exports) if exports else None,
            )

        except Exception as e:
            yield f"❌ Transcription Error: {str(e)}", audio_path, None, None, None

    def process_file_upload(
        self, audio_file, model_name, language, task, include_timestamps, export_formats
    ):
        """Process uploaded audio file"""

        if audio_file is None:
            return "Please upload an audio file", None, None, None

        yield f"🎙️ Transcribing with Whisper ({model_name})...", None, None, None

        try:
            result = self.transcribe_audio(audio_file, model_name, language, task)

            # Format output
            text_output = result["text"].strip()

            # Generate detailed output with timestamps if requested
            detailed_output = ""
            if include_timestamps:
                detailed_output = self.format_with_timestamps(result["segments"])

            # Prepare export files
            exports = {}
            if export_formats:
                if "txt" in export_formats:
                    exports["txt"] = text_output
                if "srt" in export_formats:
                    exports["srt"] = self.format_srt(result["segments"])
                if "vtt" in export_formats:
                    exports["vtt"] = self.format_vtt(result["segments"])
                if "json" in export_formats:
                    exports["json"] = json.dumps(result, indent=2)

            status = f"✅ Transcription Complete!\n\n"
            status += f"Language: {result.get('language', 'Unknown')}\n"
            status += f"Duration: ~{len(result['segments'])} segments"

            yield (
                status,
                text_output,
                detailed_output,
                self.create_export_files(exports) if exports else None,
            )

        except Exception as e:
            yield f"❌ Transcription Error: {str(e)}", None, None, None

    def format_with_timestamps(self, segments):
        """Format transcript with timestamps"""
        output = []
        for segment in segments:
            start = self.format_timestamp(segment["start"])
            end = self.format_timestamp(segment["end"])
            text = segment["text"].strip()
            output.append(f"[{start} -> {end}] {text}")
        return "\n".join(output)

    def format_timestamp(self, seconds):
        """Format seconds to HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def format_srt(self, segments):
        """Format transcript as SRT subtitle file"""
        output = []
        for i, segment in enumerate(segments, 1):
            start = self.format_srt_timestamp(segment["start"])
            end = self.format_srt_timestamp(segment["end"])
            text = segment["text"].strip()
            output.append(f"{i}\n{start} --> {end}\n{text}\n")
        return "\n".join(output)

    def format_srt_timestamp(self, seconds):
        """Format seconds to SRT timestamp format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def format_vtt(self, segments):
        """Format transcript as WebVTT file"""
        output = ["WEBVTT\n"]
        for segment in segments:
            start = self.format_vtt_timestamp(segment["start"])
            end = self.format_vtt_timestamp(segment["end"])
            text = segment["text"].strip()
            output.append(f"{start} --> {end}\n{text}\n")
        return "\n".join(output)

    def format_vtt_timestamp(self, seconds):
        """Format seconds to WebVTT timestamp format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

    def create_export_files(self, exports):
        """Create export files and return file paths"""
        files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for format_type, content in exports.items():
            filename = f"transcript_{timestamp}.{format_type}"
            filepath = os.path.join(tempfile.gettempdir(), filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            files.append(filepath)

        return files if files else None


# Create transcriber instance
transcriber = WhisperTranscriber()

# Define Gradio UI
with gr.Blocks(title="YouTube to Whisper Transcription", theme=gr.themes.Soft()) as app:
    gr.Markdown(
        """
        # 🎙️ YouTube to Whisper Transcription
        Download audio from YouTube and transcribe it using OpenAI's Whisper model.
        """
    )

    with gr.Tabs():
        # Tab 1: YouTube URL
        with gr.Tab("📺 YouTube URL"):
            with gr.Row():
                with gr.Column():
                    youtube_url = gr.Textbox(
                        label="YouTube URL",
                        placeholder="https://www.youtube.com/watch?v=...",
                        lines=1,
                    )

                    with gr.Row():
                        yt_model = gr.Dropdown(
                            choices=["tiny", "base", "small", "medium", "large"],
                            value="base",
                            label="Whisper Model",
                            info="Larger models are more accurate but slower",
                        )

                        yt_language = gr.Dropdown(
                            choices=[
                                "auto",
                                "en",
                                "es",
                                "fr",
                                "de",
                                "it",
                                "pt",
                                "ru",
                                "ja",
                                "ko",
                                "zh",
                            ],
                            value="auto",
                            label="Language",
                            info="Set to 'auto' for automatic detection",
                        )

                    with gr.Row():
                        yt_task = gr.Radio(
                            choices=["transcribe", "translate"],
                            value="transcribe",
                            label="Task",
                            info="Translate will convert to English",
                        )

                        yt_timestamps = gr.Checkbox(
                            label="Include Timestamps", value=True
                        )

                    yt_export = gr.CheckboxGroup(
                        choices=["txt", "srt", "vtt", "json"],
                        label="Export Formats",
                        info="Select formats to export",
                    )

                    yt_button = gr.Button(
                        "🚀 Download & Transcribe", variant="primary", size="lg"
                    )

                with gr.Column():
                    yt_status = gr.Textbox(label="Status", lines=4)
                    yt_audio = gr.Audio(label="Downloaded Audio", type="filepath")
                    yt_transcript = gr.Textbox(label="Transcript", lines=10)
                    yt_detailed = gr.Textbox(
                        label="Detailed Transcript (with timestamps)", lines=10
                    )
                    yt_files = gr.File(label="Export Files", file_count="multiple")

            yt_button.click(
                fn=transcriber.process_youtube_url,
                inputs=[
                    youtube_url,
                    yt_model,
                    yt_language,
                    yt_task,
                    yt_timestamps,
                    yt_export,
                ],
                outputs=[yt_status, yt_audio, yt_transcript, yt_detailed, yt_files],
            )

        # Tab 2: File Upload
        with gr.Tab("📁 Upload Audio File"):
            with gr.Row():
                with gr.Column():
                    audio_file = gr.Audio(label="Upload Audio File", type="filepath")

                    with gr.Row():
                        file_model = gr.Dropdown(
                            choices=["tiny", "base", "small", "medium", "large"],
                            value="base",
                            label="Whisper Model",
                            info="Larger models are more accurate but slower",
                        )

                        file_language = gr.Dropdown(
                            choices=[
                                "auto",
                                "en",
                                "es",
                                "fr",
                                "de",
                                "it",
                                "pt",
                                "ru",
                                "ja",
                                "ko",
                                "zh",
                            ],
                            value="auto",
                            label="Language",
                            info="Set to 'auto' for automatic detection",
                        )

                    with gr.Row():
                        file_task = gr.Radio(
                            choices=["transcribe", "translate"],
                            value="transcribe",
                            label="Task",
                            info="Translate will convert to English",
                        )

                        file_timestamps = gr.Checkbox(
                            label="Include Timestamps", value=True
                        )

                    file_export = gr.CheckboxGroup(
                        choices=["txt", "srt", "vtt", "json"],
                        label="Export Formats",
                        info="Select formats to export",
                    )

                    file_button = gr.Button(
                        "🚀 Transcribe", variant="primary", size="lg"
                    )

                with gr.Column():
                    file_status = gr.Textbox(label="Status", lines=4)
                    file_transcript = gr.Textbox(label="Transcript", lines=10)
                    file_detailed = gr.Textbox(
                        label="Detailed Transcript (with timestamps)", lines=10
                    )
                    file_files = gr.File(label="Export Files", file_count="multiple")

            file_button.click(
                fn=transcriber.process_file_upload,
                inputs=[
                    audio_file,
                    file_model,
                    file_language,
                    file_task,
                    file_timestamps,
                    file_export,
                ],
                outputs=[file_status, file_transcript, file_detailed, file_files],
            )

    gr.Markdown(
        """
        ---
        ### 📝 Model Information
        - **tiny**: Fastest, least accurate (~1GB RAM)
        - **base**: Good balance of speed and accuracy (~1GB RAM)
        - **small**: Better accuracy (~2GB RAM)
        - **medium**: High accuracy (~5GB RAM)
        - **large**: Best accuracy, slowest (~10GB RAM)
        
        ### 💡 Tips
        - First transcription with a model will take longer as it downloads the model
        - YouTube downloads get the highest quality audio automatically
        - Use "translate" task to convert any language to English
        - Export to SRT/VTT for subtitle files
        """
    )

# Launch the app
if __name__ == "__main__":
    print("🚀 Starting Whisper Transcription UI...")
    print("📍 Your yt-dlp.exe will be used for YouTube downloads")
    app.launch(share=False, inbrowser=True, server_name="127.0.0.1", server_port=7860)
