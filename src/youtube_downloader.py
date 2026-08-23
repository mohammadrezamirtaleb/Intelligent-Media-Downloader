import os
import sys
import re
import requests
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
import yt_dlp

console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
    banner_text = "[bold cyan]YouTube Downloader Super Pro[/bold cyan]\n[magenta]Powered by yt-dlp, FFmpeg, Rich, Mutagen & Local AI[/magenta]"
    console.print(Panel(banner_text, expand=False, border_style="green"))

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

def main():
    clear_screen()
    show_banner()
    
    url = Prompt.ask("\n[bold yellow]📌 Please enter the YouTube Video or Playlist URL[/bold yellow]")
    
    if not url.strip():
        console.print("[bold red]URL cannot be empty![/bold red]")
        return
        
    console.print("\n[bold cyan]🎞️ Select Download Format & Quality:[/bold cyan]")
    console.print("1. [green]Video: Best Available (Up to 4K/8K) + Audio[/green]")
    console.print("2. [green]Video: 1080p + Audio[/green]")
    console.print("3. [green]Video: 720p + Audio[/green]")
    console.print("4. [yellow]Audio: MP3 (Best Quality 320k)[/yellow]")
    console.print("5. [yellow]Audio: FLAC (Lossless)[/yellow]")
    console.print("6. [blue]Video: Single file (No FFmpeg merging needed)[/blue]")
    
    choice = Prompt.ask("\n[bold cyan]Enter your choice[/bold cyan]", choices=["1", "2", "3", "4", "5", "6"], default="1")
    
    console.print("\n[bold cyan]⚙️ Advanced Features (Press Enter to skip / use defaults):[/bold cyan]")
    use_proxy = Prompt.ask("[magenta]1. Proxy URL (e.g. socks5://127.0.0.1:10808 or enter to skip)[/magenta]", default="")
    use_cookies = Prompt.ask("[magenta]2. Extract cookies to unlock age-restricted/member videos?[/magenta]", choices=["chrome", "firefox", "edge", "none"], default="none")
    embed_meta = Prompt.ask("[magenta]3. Embed Thumbnail, Artist, Title (Metadata) into file?[/magenta]", choices=["y", "n"], default="y")
    download_subs = Prompt.ask("[magenta]4. Download Subtitles file? (en, fa, all, none)[/magenta]", default="none")
    
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
        'noprogress': True,
        'download_archive': f'{output_dir}/download_history.txt',
        'postprocessors': [],
        'ffmpeg_location': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bin'),
    }
    
    # Advanced Options Processing
    if use_proxy:
        ydl_opts['proxy'] = use_proxy

    if use_cookies != "none":
        ydl_opts['cookiesfrombrowser'] = (use_cookies, )
        
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
        # Request subtitles and description for AI summary
        ydl_opts['writesubtitles'] = True
        ydl_opts['writeautomaticsub'] = True
        if 'subtitleslangs' not in ydl_opts:
            ydl_opts['subtitleslangs'] = ['en', 'fa', 'en.*']
        else:
            ydl_opts['subtitleslangs'].extend(['en', 'fa', 'en.*'])
        ydl_opts['writedescription'] = True
    
    # Format Selection
    if choice == "1":
        ydl_opts.update({'format': 'bestvideo+bestaudio/best', 'merge_output_format': 'mp4'})
    elif choice == "2":
        ydl_opts.update({'format': 'bestvideo[height<=1080]+bestaudio/best', 'merge_output_format': 'mp4'})
    elif choice == "3":
        ydl_opts.update({'format': 'bestvideo[height<=720]+bestaudio/best', 'merge_output_format': 'mp4'})
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
    
    title = ""
    description = ""
    base_name_no_ext = ""
    
    try:
        with progress:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'video')
                description = info.get('description', '')
                base_filename = ydl.prepare_filename(info)
                base_name_no_ext = os.path.splitext(os.path.basename(base_filename))[0]
                
        console.print(f"\n[bold green]✅ Download completed successfully![/bold green] :tada:")
        
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
                
            console.print(f"[bold magenta]Generating summary with {summarize_model}... (This might take a minute)[/bold magenta]")
            
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
        console.print(f"\n[bold red]❌ An error occurred:[/bold red] {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Process cancelled by user.[/bold red]")
        sys.exit(0)
