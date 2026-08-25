# 🎬 YouD: Super Pro YouTube Downloader & AI Summarizer

**YouD** is a powerful, interactive, and beautifully designed Command-Line interface (CLI) tool for downloading YouTube videos, audio, and playlists. Built with Python, it leverages `yt-dlp` for state-of-the-art downloading capabilities, `FFmpeg` for media manipulation, `Rich` for a stunning terminal UI, and integrates **Local AI (Ollama)** to automatically generate video summaries based on subtitles!

---

## 🌟 Features

*   **📋 Auto-Clipboard:** Instantly detects YouTube/Media URLs from your clipboard to save time.
*   **⚡ Turbo Speed:** Integrated with `Aria2c` to split downloads into 16 parallel connections for ultra-fast speeds!
*   **✂️ Video Trimmer:** Download specific parts of a video (e.g., from 01:20 to 05:30) instead of the whole file.
*   **♾️ Universal Downloader:** Works perfectly with YouTube, Instagram, Spotify, Twitter, and hundreds of other sites.
*   **🤖 Local AI Summarization:** Automatically detects local Ollama instances and generates video summaries.
*   **🎬 Advanced Format Selection:** Download in up to 4K/8K resolution, 1080p, 720p, or just a single merged file.
*   **🎧 Audiophile Quality:** Extract high-quality MP3 (320kbps) or Lossless FLAC.
*   **🖼️ Metadata Embedding:** Automatically embeds video thumbnails, artist names, and titles into downloaded files.
*   **📝 Subtitle Support:** Download and attach `en`, `fa`, or all available subtitles in VTT/SRT formats.
*   **🍪 Bypass Restrictions:** Extract browser cookies (Chrome, Firefox, Edge) to bypass age or member restrictions.
*   **🔒 Proxy Support & 📚 Smart History:** Custom proxy routing and playlist tracking to avoid duplicates.

---

## 📂 Project Structure

```
📂 YouD/
│
├── 📂 bin/                       # Contains FFmpeg binaries
│   ├── 📄 aria2c.exe
│   ├── 📄 ffmpeg.exe
│   └── 📄 ffprobe.exe
│
├── 📂 src/                       # Source code directory
│   └── 📄 youtube_downloader.py  # The main application script
│
├── 📂 Test/                      # Automated Test Scripts
│   └── 📄 test_utils.py          # Unit tests for helper functions
│
├── 📄 run.ps1                    # Auto-setup and launcher script
├── 📄 requirements.txt           # Python dependencies
├── 📄 .gitignore                 # Git ignore rules
└── 📄 README.md                  # Project documentation
```

### 🎥 About the `bin/` Directory
For the script to work flawlessly with advanced features, both binary files in the `bin/` directory are absolutely essential:
*   **`ffprobe.exe` (The Analyzer):** Used by `yt-dlp` to probe and analyze multimedia streams, detecting codecs, resolutions, and available formats *before* downloading.
*   **`ffmpeg.exe` (The Processor):** The core engine used to merge separate high-quality video and audio streams (required for 1080p+), convert files to MP3/FLAC, and embed metadata or thumbnails.

---

## 🚀 Getting Started (Windows)

The easiest way to run this tool is using the provided PowerShell wrapper. It automatically sets up an isolated Python Virtual Environment (`venv`), installs all required dependencies, and launches the app.

**Option 1: The Easy Way**
Simply **Right-Click** on `run.ps1` and select **Run with PowerShell**.

**Option 2: From the Terminal**
1.  Open **PowerShell**.
2.  Navigate to the `YouD` folder:
    ```powershell
    cd path\to\YouD
    ```
3.  Run the launcher script:
    ```powershell
    powershell -ExecutionPolicy Bypass -File .\run.ps1
    ```

### Manual Setup (Cross-Platform)

If you prefer to run it manually or are on Linux/Mac:

1. Create a virtual environment: `python -m venv venv`
2. Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
3. Install dependencies: `pip install -r requirements.txt`
4. Run the app: `python src/youtube_downloader.py`
*(Note: Ensure FFmpeg is either in your system PATH or located in the `bin/` folder).*

---

## 🧠 AI Summarization Setup (Optional)

To use the AI summarization feature:
1. Download and install [Ollama](https://ollama.com/).
2. Run a model locally (e.g., `ollama run llama3` or `ollama run mistral`).
3. Start **YouD**. The script will automatically detect Ollama and ask if you want a summary!

---

## 🛠️ Built With
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The core download engine
- [Rich](https://github.com/Textualize/rich) - For the beautiful terminal UI
- [FFmpeg](https://ffmpeg.org/) - Audio/Video processing
- [Mutagen](https://mutagen.readthedocs.io/en/latest/) - Audio metadata manipulation
- [Ollama](https://ollama.com/) - Local LLM integration

Made with ❤️ using Python.
