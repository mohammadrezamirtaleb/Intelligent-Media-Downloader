import os
import sys
import re
import shutil
from urllib.parse import urlsplit
import requests
import tkinter as tk
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
import yt_dlp

console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
    banner_text = "[bold cyan]Universal Media Downloader Super Pro[/bold cyan]\n[magenta]YouTube, Instagram Reels, Spotify, Twitter & more![/magenta]\n[yellow]Powered by yt-dlp, FFmpeg, Aria2c, Rich, Mutagen & Local AI[/yellow]"
    console.print(Panel(banner_text, expand=False, border_style="green"))

def get_clipboard_text():
    """Extract text from clipboard without showing a window."""
    try:
        root = tk.Tk()
        root.withdraw()
        text = root.clipboard_get()
        root.destroy()
        return text.strip()
    except Exception:
        return ""

def time_to_seconds(t_str):
    """Convert HH:MM:SS or MM:SS to seconds"""
    parts = [float(p) for p in t_str.strip().split(':')]
    if len(parts) == 3: return parts[0]*3600 + parts[1]*60 + parts[2]
    if len(parts) == 2: return parts[0]*60 + parts[1]
    return parts[0]

def get_ollama_models():
    """Detect local Ollama models"""
    try:
        response = requests.get('http://127.0.0.1:11434/api/tags', timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return [m['name'] for m in models]
    except Exception:
        pass
    return []

def generate_summary(text, model_name):
    """Generate summary using local Ollama model"""
    prompt = f"Please write a comprehensive summary of the following video content in English. Focus on the main points:\n\n{text}"
    try:
        response = requests.post('http://127.0.0.1:11434/api/generate', json={
            'model': model_name,
            'prompt': prompt,
            'stream': False
        }, timeout=300)
        if response.status_code == 200:
            return response.json().get('response', '')
    except Exception as e:
        return f"Error connecting to Ollama: {str(e)}"
    return "Failed to generate summary."

def clean_vtt(text):
    """Clean VTT subtitle format to extract raw text"""
    text = re.sub(r'^WEBVTT.*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'^Kind:.*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'^Language:.*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'[\d:\.]+\s*-->\s*[\d:\.]+[^\n]*\n', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    lines = [line.strip() for line in text.split('\n') if line.strip() and not line.strip().isdigit()]
    dedup = []
    for line in lines:
        if not dedup or dedup[-1] != line:
            dedup.append(line)
    return " ".join(dedup)

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)


def normalize_media_url(url):
    """Canonicalize Reel links copied from Instagram without changing other URLs."""
    url = url.strip()
    candidate = url if '://' in url else f'https://{url}'
    parsed = urlsplit(candidate)
    if parsed.scheme not in ('http', 'https') or parsed.hostname not in (
        'instagram.com', 'www.instagram.com', 'm.instagram.com',
    ):
        return url

    # Instagram also shares /reels/ and /username/reel/ links.
    match = re.fullmatch(
        r'/(?:(?!share/)[A-Za-z0-9_.]+/)?reels?/([A-Za-z0-9_-]+)/?', parsed.path,
    )
    if match and match.group(1) != 'audio':
        return f'https://www.instagram.com/reel/{match.group(1)}/'
    return url


def is_instagram_reel_url(url):
    parsed = urlsplit(normalize_media_url(url))
    return parsed.scheme in ('http', 'https') and parsed.hostname == 'www.instagram.com' and bool(
        re.fullmatch(r'/reel/(?!audio/)[A-Za-z0-9_-]+/', parsed.path)
    )


def cookie_options(source):
    """Build yt-dlp authentication options for a browser or a cookie file."""
    source = source.strip()
    if not source or source.lower() == 'none':
        return {}
    cookie_path = os.path.expanduser(source.strip('\"'))
    if os.path.isfile(cookie_path):
        return {'cookiefile': cookie_path}
    if cookie_path.lower().endswith('.txt'):
        raise ValueError(f'Cookie file not found: {cookie_path}')
    # Split once so Windows drive letters in browser profile paths are preserved.
    return {'cookiesfrombrowser': tuple(source.split(':', 1))}


def main():
    clear_screen()
    show_banner()
    
    # 1. Auto Clipboard Detection
    clip_text = get_clipboard_text()
    url = ""
    if clip_text.startswith("http"):
        console.print(f"\n[bold green]📋 Found URL in clipboard:[/bold green] [cyan]{clip_text}[/cyan]")
        use_clip = Prompt.ask("Use this URL?", choices=["y", "n"], default="y")
        if use_clip == 'y':
            url = clip_text
            
    if not url:
        url = Prompt.ask("\n[bold yellow]📌 Please enter the Media URL (YouTube, Instagram Reel, Spotify, etc.)[/bold yellow]")
    
    if not url.strip():
        console.print("[bold red]URL cannot be empty![/bold red]")
        return

    url = normalize_media_url(url)
    instagram_reel = is_instagram_reel_url(url)
    bin_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bin')
    ffmpeg_exe = os.path.join(bin_path, 'ffmpeg.exe')
    ffmpeg_available = os.path.isfile(ffmpeg_exe) or shutil.which('ffmpeg') is not None
    if instagram_reel:
        console.print("\n[bold magenta]📱 Instagram Reel detected.[/bold magenta]")
        console.print("[cyan]Try public Reels without cookies first. If Instagram requires login, sign in to Instagram in Firefox and select 'firefox', or use a Netscape cookies file.[/cyan]")
        if not ffmpeg_available:
            console.print("[yellow]FFmpeg was not found. Use a single-file video format; audio extraction, trimming and metadata embedding require FFmpeg.[/yellow]")
        
    console.print("\n[bold cyan]🎞️ Select Download Format & Quality:[/bold cyan]")
    console.print("1. [green]Video: Best Available (Up to 4K/8K) + Audio[/green]")
    console.print("2. [green]Video: 1080p + Audio[/green]")
    console.print("3. [green]Video: 720p + Audio[/green]")
    console.print("4. [yellow]Audio: MP3 (Best Quality 320k)[/yellow]")
    console.print("5. [yellow]Audio: FLAC (Lossless)[/yellow]")
    console.print("6. [blue]Video: Single file (No FFmpeg merging needed)[/blue]")
    
    choice = Prompt.ask("\n[bold cyan]Enter your choice[/bold cyan]", choices=["1", "2", "3", "4", "5", "6"], default="1")
    
    console.print("\n[bold cyan]⚙️ Advanced Features (Press Enter to skip / use defaults):[/bold cyan]")
    
    # 2. Trim Video Logic
    trim_video = Prompt.ask("[magenta]✂️ 1. Trim Video? (Enter to skip, 'y' to cut a segment)[/magenta]", choices=["y", "n", ""], default="")
    start_sec, end_sec = None, None
    if trim_video == "y":
        try:
            s_time = Prompt.ask("[magenta]   Start Time (Format MM:SS or seconds)[/magenta]", default="00:00")
            e_time = Prompt.ask("[magenta]   End Time (Format MM:SS or seconds)[/magenta]")
            start_sec = time_to_seconds(s_time)
            end_sec = time_to_seconds(e_time)
        except Exception:
            console.print("[red]Invalid time format. Trimmer ignored.[/red]")
            start_sec, end_sec = None, None
            
    # 3. Channel/Playlist logic
    playlist_limit = Prompt.ask("[magenta]🔢 2. Max items to download? (e.g. 5 for latest 5. Enter to skip)[/magenta]", default="")
    
    use_proxy = Prompt.ask("[magenta]🌐 3. Proxy URL (e.g. socks5://127.0.0.1:10808 or enter to skip)[/magenta]", default="")
    
    default_cookie = "none"
    use_cookies = Prompt.ask("[magenta]🍪 4. Cookies ('none', 'firefox', or path to a cookies.txt file)[/magenta]", default=default_cookie)
    try:
        authentication = cookie_options(use_cookies)
    except ValueError as error:
        console.print(str(error), style="red", markup=False)
        return
    
    embed_default = "n" if instagram_reel and not ffmpeg_available else "y"
    embed_meta = Prompt.ask("[magenta]🏷️ 5. Embed Thumbnail & Metadata into file?[/magenta]", choices=["y", "n"], default=embed_default)
    download_subs = Prompt.ask("[magenta]📝 6. Download Subtitles file? (en, fa, all, none)[/magenta]", default="none")
    
    # AI Summary detection
    models = get_ollama_models()
    summarize_model = None
    if models:
        console.print("\n[bold magenta]🤖 Local AI Detected (Ollama)[/bold magenta]")
        do_summary = Prompt.ask("[white]Generate an English summary of this video?[/white]", choices=["y", "n"], default="y")
        if do_summary == 'y':
            console.print("\n[cyan]Available Models:[/cyan]")
            for i, m in enumerate(models, 1):
                console.print(f"{i}. {m}")
            mod_idx = Prompt.ask("Select a model (number)", default="1")
            try:
                summarize_model = models[int(mod_idx)-1]
            except Exception:
                summarize_model = models[0]
            console.print(f"[green]Selected Model:[/green] {summarize_model}")

    output_dir = "Downloads"
    os.makedirs(output_dir, exist_ok=True)
    
    progress = Progress(
        TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
        BarColumn(bar_width=40),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        DownloadColumn(),
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
        console=console
    )

    task_id = progress.add_task("download", filename="Preparing...", total=None)

    def my_hook(d):
        if d['status'] == 'downloading':
            try:
                filename = os.path.basename(d.get('filename', 'Unknown'))
                if len(filename) > 25:
                    filename = filename[:22] + "..."
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded_bytes = d.get('downloaded_bytes', 0)
                if total_bytes:
                    progress.update(task_id, total=total_bytes, completed=downloaded_bytes, filename=filename)
                else:
                    progress.update(task_id, completed=downloaded_bytes, filename=filename)
            except Exception:
                pass
        elif d['status'] == 'finished':
            progress.update(task_id, filename="[green]Processing / Merging...[/green]")

    ydl_opts = {
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'progress_hooks': [my_hook],
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': ['player_client=web']},
        'remote_components': ['ejs:github'],
        'noprogress': True,
        'download_archive': f'{output_dir}/download_history.txt',
        'postprocessors': [],
        'ffmpeg_location': bin_path if os.path.exists(ffmpeg_exe) else None,
    }

    if instagram_reel:
        ydl_opts.update({
            'noplaylist': True,
            # Different Reels often have the same title (e.g. "Video by user").
            'outtmpl': f'{output_dir}/%(title).150B [%(id)s].%(ext)s',
            'http_headers': {'Referer': 'https://www.instagram.com/'},
        })
    
    # 4. Turbo Speed (Aria2c) Integration
    aria2_exe = os.path.join(bin_path, 'aria2c.exe')
    if os.path.exists(aria2_exe):
        console.print("\n[bold green]⚡ Turbo Speed Enabled (Aria2c Detected!)[/bold green]")
        ydl_opts['external_downloader'] = aria2_exe
        # aria2c args for ultra speed
        ydl_opts['external_downloader_args'] = ['-c', '-j', '16', '-x', '16', '-s', '16', '-k', '1M']
    
    # Apply Trim Logic
    if start_sec is not None and end_sec is not None:
        def make_range(start, end):
            def _download_ranges(info_dict, ydl):
                yield {'start_time': start, 'end_time': end}
            return _download_ranges
        ydl_opts['download_ranges'] = make_range(start_sec, end_sec)
        ydl_opts['force_keyframes_at_cuts'] = True

    # Apply Playlist Limit
    if playlist_limit.isdigit():
        ydl_opts['playlistend'] = int(playlist_limit)
    
    # Advanced Options Processing
    if use_proxy:
        ydl_opts['proxy'] = use_proxy

    ydl_opts.update(authentication)
        
    if embed_meta == 'y':
        ydl_opts['writethumbnail'] = True
        ydl_opts['postprocessors'].append({'key': 'EmbedThumbnail'})
        ydl_opts['postprocessors'].append({'key': 'FFmpegMetadata'})

    if download_subs != "none":
        ydl_opts['writesubtitles'] = True
        if download_subs == "all":
            ydl_opts['subtitleslangs'] = ['all']
        else:
            ydl_opts['subtitleslangs'] = [download_subs]
        ydl_opts['subtitlesformat'] = 'srt/best'
        
    if summarize_model:
        ydl_opts['writesubtitles'] = True
        ydl_opts['writeautomaticsub'] = True
        if 'subtitleslangs' not in ydl_opts:
            ydl_opts['subtitleslangs'] = ['en', 'fa', 'en.*']
        else:
            ydl_opts['subtitleslangs'].extend(['en', 'fa', 'en.*'])
        ydl_opts['writedescription'] = True
    
    # Format Selection
    if choice == "1":
        pass
    elif choice == "2":
        ydl_opts.update({'format': 'bestvideo*[height<=1080]+bestaudio/best[height<=1080]', 'merge_output_format': 'mp4'})
    elif choice == "3":
        ydl_opts.update({'format': 'bestvideo*[height<=720]+bestaudio/best[height<=720]', 'merge_output_format': 'mp4'})
    elif choice == "4":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'].insert(0, {
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        })
    elif choice == "5":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'].insert(0, {
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'flac',
        })
    elif choice == "6":
        ydl_opts['format'] = 'best'
        
    console.print("\n[bold yellow]🚀 Starting download process...[/bold yellow]")
    
    title, description, base_name_no_ext = "", "", ""
    
    try:
        with progress:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info is None:
                    console.print("\n[yellow]No new media to download (the Reel or video may already be in download history).[/yellow]")
                    return
                title = info.get('title', 'video')
                description = info.get('description', '')
                base_filename = ydl.prepare_filename(info)
                base_name_no_ext = os.path.splitext(os.path.basename(base_filename))[0]
                
        console.print(f"\n[bold green]✅ Task completed successfully![/bold green] :tada:")
        
        # AI Summary Generation Process
        if summarize_model:
            console.print("\n[bold yellow]🧠 Extracting text for AI summary...[/bold yellow]")
            vtt_text = ""
            for file in os.listdir(output_dir):
                if file.startswith(base_name_no_ext) and (file.endswith('.vtt') or file.endswith('.srt')):
                    vtt_path = os.path.join(output_dir, file)
                    try:
                        with open(vtt_path, 'r', encoding='utf-8') as f:
                            raw_vtt = f.read()
                            vtt_text = clean_vtt(raw_vtt)
                        break
                    except Exception:
                        pass
            
            summary_content = f"Title: {title}\n\nDescription: {description}\n\n"
            if vtt_text:
                console.print("[cyan]Subtitle transcript found. Using transcript for better context.[/cyan]")
                summary_content += f"Transcript:\n{vtt_text[:15000]}"
            else:
                console.print("[cyan]No subtitles found. Using video title and description instead.[/cyan]")
                
            console.print(f"[bold magenta]Generating summary with {summarize_model}...[/bold magenta]")
            summary_result = generate_summary(summary_content, summarize_model)
            safe_title = sanitize_filename(title)
            summary_file_path = os.path.join(output_dir, f"{safe_title}_summary.txt")
            
            with open(summary_file_path, 'w', encoding='utf-8') as sf:
                sf.write(summary_result)
                
            console.print(f"\n[bold green]📄 Summary saved to: {summary_file_path}[/bold green]")
            preview_len = 1000
            preview = summary_result[:preview_len] + ("..." if len(summary_result) > preview_len else "")
            console.print(Panel(preview, title=f"{summarize_model} Summary Preview", border_style="magenta"))

        console.print(f"\n📂 Files are saved in the [bold cyan]{os.path.abspath(output_dir)}[/bold cyan] directory.")
        
    except Exception as e:
        error_msg = str(e)
        if instagram_reel:
            console.print("\n[bold red]❌ Instagram Reel download failed.[/bold red]")
            console.print(error_msg, markup=False)
            if any(term in error_msg.lower() for term in ('429', 'rate', 'too many requests')):
                console.print("[yellow]Instagram may be limiting requests. Wait before retrying.[/yellow]")
            console.print("[yellow]Open the Reel in your browser to check it is available. If login is required, sign in to Instagram in Firefox and select 'firefox', or provide a Netscape cookies file from that session.[/yellow]")
            console.print("[cyan]If extraction still fails, update yt-dlp: python -m pip install --upgrade yt-dlp[/cyan]")
        elif "DPAPI" in error_msg:
            console.print("\n[bold red]❌ خطای امنیتی مرورگر کروم و ادج (DPAPI)[/bold red]")
            console.print("[yellow]گوگل کروم و ادج در آپدیت جدید اجازه خواندن کوکی‌ها را مسدود کرده‌اند.[/yellow]")
            console.print("[green]راه‌حل قطعی:[/green] از مرورگر [bold]Firefox[/bold] استفاده کنید! فایرفاکس این قفل آزاردهنده را ندارد. کافیست در آن وارد یوتیوب شوید و در برنامه کلمه [bold]firefox[/bold] را تایپ کنید.")
        elif "confirm you’re not a bot" in error_msg or "confirm you're not a bot" in error_msg:
            console.print("\n[bold red]❌ خطای ضد-ربات یوتیوب (Anti-Bot)[/bold red]")
            console.print("[yellow]یوتیوب درخواست شما را مسدود کرد چون فایل cookies.txt فاقد اثر انگشت مرورگر (User-Agent) است.[/yellow]")
            console.print("[green]راه‌حل نهایی و قطعی:[/green] فایل cookies.txt روی سیستم شما جواب نمی‌دهد. تنها راه عبور، استفاده از مرورگر [bold]Firefox[/bold] است. مرورگر فایرفاکس را نصب کنید، در آن وارد یوتیوب شوید و در مرحله کوکی بنویسید: [bold]firefox[/bold]")
        elif "The page needs to be reloaded" in error_msg:
            console.print("\n[bold red]❌ خطای بازنشانی صفحه (Page Reload)[/bold red]")
            console.print("[yellow]یوتیوب موقتاً به دلیل درخواست‌های زیاد یا تغییرات شبکه، صفحه را مسدود کرده است.[/yellow]")
            console.print("[green]راه‌حل قطعی:[/green] کوکی‌های مرورگر فایرفاکس خود را در سایت یوتیوب یک بار پاک کنید، دوباره لاگین کنید، یک ویدیو پخش کنید و سپس برنامه را اجرا کنید.")
        else:
            console.print(f"\n[bold red]❌ An error occurred:[/bold red] {error_msg}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Process cancelled by user.[/bold red]")
        sys.exit(0)
