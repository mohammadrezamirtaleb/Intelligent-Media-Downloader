import unittest
import sys
import os

# Add the src directory to the python path so we can import the script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from youtube_downloader import time_to_seconds, clean_vtt, sanitize_filename

class TestYoutubeDownloaderUtils(unittest.TestCase):

    def test_time_to_seconds(self):
        self.assertEqual(time_to_seconds("01:20"), 80)
        self.assertEqual(time_to_seconds("00:45"), 45)
        self.assertEqual(time_to_seconds("01:02:03"), 3723)
        self.assertEqual(time_to_seconds("10"), 10)

    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("My Video : 100% Awesome!"), "My Video  100% Awesome!")
        self.assertEqual(sanitize_filename("Path/To\\Invalid*Chars?<>|"), "PathToInvalidChars")
        
    def test_clean_vtt(self):
        sample_vtt = """WEBVTT
Kind: captions
Language: en

00:00:01.000 --> 00:00:03.000
Hello World!

00:00:03.000 --> 00:00:05.000
Welcome to <c.color>YouD</c>!
"""
        cleaned = clean_vtt(sample_vtt)
        self.assertEqual(cleaned, "Hello World! Welcome to YouD!")

if __name__ == '__main__':
    unittest.main()
