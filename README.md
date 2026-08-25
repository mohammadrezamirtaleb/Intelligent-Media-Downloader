<div align="center">

# 🎬 Intelligent Media Downloader

<a href="https://github.com/mohammadrezamirtaleb/Intelligent-Media-Downloader">
  <img src="https://readme-typing-svg.herokuapp.com?font=Orbitron&weight=800&size=26&pause=1000&color=00E5FF&center=true&vCenter=true&width=800&height=70&lines=🚀+Bypass+YouTube+Anti-Bot+with+Deno+JS;🤖+Summarize+Videos+with+Local+AI+(Ollama);⚡+Turbo+Speed+Downloads+(Aria2c+16x);🎶+Extract+Audiophile-Grade+Lossless+Audio" alt="Typing SVG" />
</a>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-00E5FF?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Powered_by-yt--dlp-FF004D?style=for-the-badge&logo=youtube&logoColor=white" />
  <img src="https://img.shields.io/badge/AI-Ollama_%7C_LLM-000000?style=for-the-badge&logo=openai&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-00FF66?style=for-the-badge" />
</p>

> **The ultimate terminal-based CLI tool** designed to download high-quality videos and audio from YouTube, Instagram, Spotify, Twitter, and hundreds of other platforms, seamlessly integrated with **Local AI**.

</div>

<br/>

## 🧠 The Role of AI (LLMs & VLMs)

What makes this downloader truly *intelligent* is its seamless integration with **Local AI Providers** (specifically **Ollama**). The provider acts as the engine that runs AI models directly on your hardware without needing external APIs or internet connectivity. 

| AI Model Type | What It Does in This Project |
| :--- | :--- |
| 📝 **LLM (Language Models)** | Acts as the "brain". Reads through downloaded video subtitles/transcripts and generates concise, highly accurate text summaries. Grasp a 2-hour tutorial in seconds! |
| 👁️ **VLM (Vision Models)** | Acts as the "eyes". Analyzes video frames or downloaded thumbnails to extract visual context, perform OCR on slides, or describe the visual elements of the media. |
| ⚡ **The Provider (Ollama)** | Probes `127.0.0.1:11434`. Fetches installed models dynamically. Manages heavy GPU/CPU loads and provides a simple API for text/vision inferences on the fly. |

<br/>

## ✨ Core Features

* 🛡️ **Anti-Bot Bypass:** Uses **Deno JS Runtime** and `EJS` components to flawlessly solve YouTube's latest PO Token & JavaScript challenges.
* ⚡ **Turbo Download (Aria2c):** Splits downloads into up to 16 concurrent connections for maximum speed.
* ✂️ **Smart Trimmer:** Download only the parts of a video you need (e.g., `01:20-05:30`).
* 🎬 **Premium Quality:** Download up to 4K/8K video, or extract audiophile-grade 320kbps MP3 / Lossless FLAC.
* 🏷️ **Metadata Embedding:** Automatically embeds video thumbnails, artist names, and titles into the final file.
* 📋 **Auto-Clipboard:** Detects URLs directly from your clipboard to save time.
* 🍪 **Advanced Authentication:** Pass `firefox` cookies or a `cookies.txt` file to bypass age/member restrictions seamlessly.

<br/>

## 📂 Project Structure

```text
📁 IntelligentMediaDownloader/
 ├── 📁 bin/                       # ⚙️ Required Binaries (Add these manually)
 │    ├── 📄 aria2c.exe            # ⚡ Download Accelerator
 │    ├── 📄 ffmpeg.exe            # 🎬 Video & Audio Processor
 │    └── 📄 ffprobe.exe           # 🔍 Media Analyzer
 │
 ├── 📁 src/                       # 💻 Source Code
 │    └── 📄 youtube_downloader.py # 🐍 Main Application Script
 │
 ├── 📁 Test/                      # 🧪 Testing Directory
 │    ├── 📄 test_utils.py         # 🛠️ Unit tests
 │    └── 📄 inputs.txt            # 📝 Test inputs
 │
 ├── 📄 run.ps1                    # 🚀 Auto-Setup & Launcher Script
 ├── 📄 start.bat                  # 🖱️ 1-Click execution script
 └── 📄 README.md                  # 📖 Project Documentation
```

<br/>

## ⚙️ Prerequisites & Required Binaries

> [!WARNING]
> **IMPORTANT NOTE ON BINARIES:** 
> To keep this repository lightweight, the heavy executable files (`ffmpeg.exe`, `ffprobe.exe`, and `aria2c.exe`) are **NOT** included in this repository. You must download them manually and place them inside the `bin/` folder for advanced features to work!

<details>
<summary><b>Click to view installation instructions for required dependencies</b></summary>
<br/>

1. **Python 3.8+**
2. **Deno JS Runtime:** Required to bypass YouTube's JS challenges.
   * *Windows:* Run `irm https://deno.land/install.ps1 | iex` in PowerShell.
3. **FFmpeg & FFprobe:** Required for merging audio/video and embedding metadata.
   * Download from [BtbN FFmpeg-Builds (GitHub)](https://github.com/BtbN/FFmpeg-Builds/releases) (Look for `ffmpeg-master-latest-win64-gpl.zip`).
   * Extract `ffmpeg.exe` and `ffprobe.exe` into the `bin/` directory.
4. **Aria2c:** Required for Turbo downloading (16x speed).
   * Download from [Aria2 Releases (GitHub)](https://github.com/aria2/aria2/releases) (Look for `aria2-*-win-64bit-build1.zip`).
   * Extract `aria2c.exe` into the `bin/` directory.
5. **Ollama (Optional but Recommended):** Install [Ollama](https://ollama.com/) to enable the AI features.

</details>

<br/>

## 🚀 Getting Started

### 🟢 The Easy Way (Windows 1-Click)
Simply double-click the **`start.bat`** file! 
*(It will bypass execution policies, create a virtual environment, install dependencies, configure the JS runtime, and launch the UI).*

### 👨‍💻 Terminal Method
1. Open PowerShell in the project directory.
2. Run the launcher:
   ```powershell
   .\run.ps1
   ```

<br/>
<p align="center">
  <i>Powered by Python & Local AI. Made with ❤️.</i>
</p>
