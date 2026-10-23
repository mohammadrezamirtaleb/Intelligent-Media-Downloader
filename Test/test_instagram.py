import copy
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from rich.console import Console
from yt_dlp import YoutubeDL
from yt_dlp.extractor.instagram import InstagramIE
from yt_dlp.utils import DownloadError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import youtube_downloader as downloader


class TestInstagramLinks(unittest.TestCase):
    def test_copied_reel_links_reach_instagram_extractor(self):
        for url in (
            ' https://www.instagram.com/reel/AbC_123-xy/?igsh=tracking#fragment ',
            'https://instagram.com/reels/AbC_123-xy',
            'http://m.instagram.com/reel/AbC_123-xy/',
            'https://www.instagram.com/some.user/reel/AbC_123-xy/',
            'instagram.com/reel/AbC_123-xy/',
            'www.instagram.com/reels/AbC_123-xy/?utm_source=share',
        ):
            with self.subTest(url=url):
                normalized = downloader.normalize_media_url(url)
                self.assertEqual(normalized, 'https://www.instagram.com/reel/AbC_123-xy/')
                self.assertTrue(downloader.is_instagram_reel_url(normalized))
                self.assertTrue(InstagramIE.suitable(normalized))

    def test_other_urls_are_not_routed_as_reels(self):
        for url in (
            'https://youtu.be/example?list=playlist',
            'https://www.instagram.com/p/AbC_123/',
            'https://www.instagram.com/some.user/reels/',
            'https://www.instagram.com/reels/audio/12345/',
            'https://www.instagram.com/share/reel/token/',
            'https://www.instagram.com/share/token/',
            'https://www.instagram.com/reel/',
            'https://instagram.com.example.com/reel/AbC_123/',
            'https://example.com/?url=https://instagram.com/reel/AbC_123/',
            'ftp://www.instagram.com/reel/AbC_123/',
        ):
            with self.subTest(url=url):
                self.assertEqual(downloader.normalize_media_url(url), url)
                self.assertFalse(downloader.is_instagram_reel_url(url))


class TestInstagramCookies(unittest.TestCase):
    def test_cookies_are_opt_in(self):
        for source in ('', 'none', ' NONE '):
            self.assertEqual(downloader.cookie_options(source), {})
        self.assertEqual(downloader.cookie_options('firefox'), {'cookiesfrombrowser': ('firefox',)})

    def test_explicit_cookie_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'instagram cookies.txt'
            path.write_text('# Netscape HTTP Cookie File\n', encoding='utf-8')
            self.assertEqual(downloader.cookie_options(f'"{path}"'), {'cookiefile': str(path)})

    def test_missing_cookie_file_is_not_treated_as_browser(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'Cookie file not found'):
                downloader.cookie_options(str(Path(directory) / 'missing.txt'))

    def test_windows_browser_profile_path(self):
        profile = r'C:\Users\Example\Firefox Profile'
        self.assertEqual(downloader.cookie_options(f'firefox:{profile}'), {
            'cookiesfrombrowser': ('firefox', profile),
        })


class TestInstagramDownloadFlow(unittest.TestCase):
    def run_downloader(self, url, choice='1', cookies='none', result='video', error=None):
        """Exercise the CLI through extraction, replacing only external I/O."""
        output = io.StringIO()
        selected = {}

        def answer(prompt, **kwargs):
            if 'Please enter' in prompt:
                return url
            if 'Enter your choice' in prompt:
                return choice
            if '4. Cookies' in prompt:
                return cookies
            return kwargs.get('default', '')

        def capture_options(options):
            selected.update(options)
            return fake_ydl

        fake_ydl = MagicMock()
        fake_ydl.__enter__.return_value = fake_ydl
        fake_ydl.extract_info.return_value = None if result is None else {
            'id': 'AbC_123', 'title': 'Video by example', 'description': 'A Reel',
        }
        fake_ydl.extract_info.side_effect = error
        fake_ydl.prepare_filename.return_value = 'Downloads/Video by example [AbC_123].mp4'
        with (
            patch.object(downloader, 'console', Console(file=output, width=180)),
            patch.object(downloader, 'clear_screen'),
            patch.object(downloader, 'get_clipboard_text', return_value=''),
            patch.object(downloader, 'get_ollama_models', return_value=[]),
            patch.object(downloader.shutil, 'which', return_value=None),
            patch.object(downloader.os.path, 'isfile', return_value=False),
            patch.object(downloader.os.path, 'exists', return_value=False),
            patch.object(downloader.os, 'makedirs'),
            patch.object(downloader.Prompt, 'ask', side_effect=answer),
            patch.object(downloader.yt_dlp, 'YoutubeDL', side_effect=capture_options),
        ):
            downloader.main()
        return selected, fake_ydl, output.getvalue()

    def test_reel_defaults_and_download_invocation(self):
        options, ydl, output = self.run_downloader('instagram.com/reels/AbC_123/?igsh=tracking')
        ydl.extract_info.assert_called_once_with('https://www.instagram.com/reel/AbC_123/', download=True)
        self.assertTrue(options['noplaylist'])
        self.assertNotIn('cookiefile', options)
        self.assertNotIn('cookiesfrombrowser', options)
        self.assertEqual(options['postprocessors'], [])  # No FFmpeg installed.
        self.assertIn('completed successfully', output)

        # Render with real yt-dlp to prove equal titles produce distinct filenames.
        with YoutubeDL({'outtmpl': options['outtmpl'], 'quiet': True}) as real_ydl:
            names = [real_ydl.prepare_filename({
                'id': media_id, 'title': 'Video by example', 'ext': 'mp4',
            }) for media_id in ('AbC_123', 'Other_456')]
        self.assertNotEqual(*names)

    def test_all_video_modes_select_muxed_instagram_video(self):
        # Instagram can supply one MP4 containing both video and audio.
        info = {
            'id': 'AbC_123', 'title': 'Video by example',
            'formats': [{
                'format_id': 'mp4', 'url': 'https://example.com/reel.mp4',
                'ext': 'mp4', 'height': 720, 'width': 405,
                'vcodec': 'h264', 'acodec': 'aac',
            }],
        }
        for choice in ('1', '2', '3', '6'):
            with self.subTest(choice=choice):
                options, _, _ = self.run_downloader('https://instagram.com/reel/AbC_123/', choice)
                # Use the installed yt-dlp selector rather than mocking format handling.
                options['cachedir'] = False
                with YoutubeDL(options) as real_ydl:
                    processed = real_ydl.process_ie_result(copy.deepcopy(info), download=False)
                self.assertEqual(processed['format_id'], 'mp4')
                self.assertNotIn('requested_formats', processed)

    def test_audio_modes_use_ffmpeg_extraction(self):
        for choice, codec in (('4', 'mp3'), ('5', 'flac')):
            with self.subTest(choice=choice):
                options, _, _ = self.run_downloader('https://instagram.com/reel/AbC_123/', choice)
                self.assertEqual(options['postprocessors'][0]['key'], 'FFmpegExtractAudio')
                self.assertEqual(options['postprocessors'][0]['preferredcodec'], codec)

    def test_instagram_cookies_reach_downloader(self):
        options, _, _ = self.run_downloader('https://instagram.com/reel/AbC_123/', cookies='firefox')
        self.assertEqual(options['cookiesfrombrowser'], ('firefox',))

    def test_archive_skip_is_reported_without_attribute_error(self):
        _, _, output = self.run_downloader('https://instagram.com/reel/AbC_123/', result=None)
        self.assertIn('No new media to download', output)
        self.assertNotIn('completed successfully', output)
        self.assertNotIn('download failed', output)

    def test_instagram_failure_explains_login_and_rate_limits(self):
        _, _, output = self.run_downloader(
            'https://instagram.com/reel/AbC_123/', error=DownloadError('HTTP Error 429: Too Many Requests'),
        )
        self.assertIn('Wait before retrying', output)
        self.assertIn('sign in to Instagram in Firefox', output)
        self.assertNotIn('completed successfully', output)

    def test_youtube_retains_existing_defaults(self):
        url = 'https://youtu.be/example?list=playlist'
        options, ydl, _ = self.run_downloader(url)
        ydl.extract_info.assert_called_once_with(url, download=True)
        self.assertNotIn('noplaylist', options)
        self.assertEqual(options['outtmpl'], 'Downloads/%(title)s.%(ext)s')
        self.assertTrue(options['writethumbnail'])


if __name__ == '__main__':
    unittest.main()
