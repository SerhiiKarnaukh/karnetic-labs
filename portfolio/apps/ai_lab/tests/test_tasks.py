import os
import shutil
import tempfile
from unittest.mock import patch

from django.test import TestCase, override_settings

from ai_lab.tasks.cleanup import delete_generated_media


@override_settings(MEDIA_ROOT=os.path.join(tempfile.gettempdir(), 'ai_lab_cleanup_media'))
class DeleteGeneratedMediaTaskTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp(dir=tempfile.gettempdir())

    def tearDown(self):
        shutil.rmtree(self.media_root, ignore_errors=True)

    @override_settings(MEDIA_ROOT=os.path.join(tempfile.gettempdir(), 'ai_lab_cleanup_media'))
    def test_deletes_files_and_nested_directories(self):
        for folder in ('generated_images', 'generated_voices', 'vision_images'):
            path = os.path.join(self.media_root, folder)
            os.makedirs(os.path.join(path, 'nested'))
            open(os.path.join(path, 'file.txt'), 'w').close()
            open(os.path.join(path, 'nested', 'file.txt'), 'w').close()

        with patch('ai_lab.tasks.cleanup.settings.MEDIA_ROOT', self.media_root):
            delete_generated_media()

        for folder in ('generated_images', 'generated_voices', 'vision_images'):
            self.assertEqual(os.listdir(os.path.join(self.media_root, folder)), [])

    def test_ignores_missing_folders(self):
        with patch('ai_lab.tasks.cleanup.settings.MEDIA_ROOT', self.media_root):
            delete_generated_media()

    def test_prints_error_when_file_removal_fails(self):
        folder = os.path.join(self.media_root, 'generated_images')
        os.makedirs(folder)
        open(os.path.join(folder, 'file.txt'), 'w').close()

        with (
            patch('ai_lab.tasks.cleanup.settings.MEDIA_ROOT', self.media_root),
            patch('ai_lab.tasks.cleanup.os.remove', side_effect=OSError('locked')),
            patch('builtins.print') as mock_print,
        ):
            delete_generated_media()

        mock_print.assert_called_once()
