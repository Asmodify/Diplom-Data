import unittest
from content_manager.content_manager import ContentSaver
from pathlib import Path
import shutil
import os

class TestContentSaver(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_data"
        self.saver = ContentSaver(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_post(self):
        post = {"url": "http://facebook.com/testpost", "content": "Test content"}
        result = self.saver.save_post(post, post["url"])
        self.assertTrue(result)
        post_id = post["url"].split("/")[-1]
        file_path = Path(self.test_dir) / "posts" / f"{post_id}.txt"
        self.assertTrue(file_path.exists())

    def test_save_image(self):
        img_bytes = b"fakeimagebytes"
        result = self.saver.save_image(img_bytes, "testimg.jpg")
        self.assertTrue(result)
        file_path = Path(self.test_dir) / "images" / "testimg.jpg"
        self.assertTrue(file_path.exists())

    def test_save_comment(self):
        comment = {"author": "user", "text": "Nice!"}
        result = self.saver.save_comment(comment, "testpost")
        self.assertTrue(result)
        file_path = Path(self.test_dir) / "comments" / "testpost.json"
        self.assertTrue(file_path.exists())

if __name__ == "__main__":
    unittest.main()
