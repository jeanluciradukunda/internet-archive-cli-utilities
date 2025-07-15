#!/usr/bin/env python3
"""
Unit tests for download_archive_collection.py

This module contains unit tests for the Internet Archive collection downloader.
The tests focus on the business logic and error handling capabilities.
"""

import unittest
from unittest.mock import Mock, patch, call
import subprocess
import tempfile
import os
import sys

# Add the current directory to the path so we can import the module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from download_archive_collection import (
    InternetArchiveDownloader,
    DependencyError,
    DownloadError,
    setup_logging,
    create_argument_parser
)


class TestInternetArchiveDownloader(unittest.TestCase):
    """Test cases for the InternetArchiveDownloader class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.downloader = InternetArchiveDownloader(
            max_workers=2,
            rate_limit=0.1,
            max_retries=1
        )

    @patch('download_archive_collection.shutil.which')
    def test_check_dependencies_ia_missing(self, mock_which):
        """Test that DependencyError is raised when 'ia' command is missing."""
        mock_which.return_value = None
        
        with self.assertRaises(DependencyError) as context:
            self.downloader._check_dependencies()
        
        self.assertIn("'ia' command is not available", str(context.exception))

    @patch('download_archive_collection.shutil.which')
    def test_check_dependencies_ia_present(self, mock_which):
        """Test that no error is raised when 'ia' command is present."""
        mock_which.return_value = '/usr/bin/ia'
        
        # Should not raise any exception
        try:
            self.downloader._check_dependencies()
        except DependencyError:
            self.fail("_check_dependencies() raised DependencyError unexpectedly")

    @patch('download_archive_collection.subprocess.run')
    def test_fetch_collection_items_success(self, mock_run):
        """Test successful fetching of collection items."""
        mock_run.return_value = Mock(
            stdout="item1\nitem2\nitem3\n",
            stderr="",
            returncode=0
        )
        
        items = self.downloader._fetch_collection_items("test_collection")
        
        self.assertEqual(items, ["item1", "item2", "item3"])
        mock_run.assert_called_once_with(
            ['ia', 'search', 'collection:test_collection', '--itemlist'],
            capture_output=True,
            text=True,
            check=True,
            timeout=60
        )

    @patch('download_archive_collection.subprocess.run')
    def test_fetch_collection_items_failure(self, mock_run):
        """Test handling of collection fetch failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'ia', stderr="Collection not found")
        
        with self.assertRaises(DownloadError) as context:
            self.downloader._fetch_collection_items("nonexistent_collection")
        
        self.assertIn("Failed to fetch collection items", str(context.exception))

    @patch('download_archive_collection.subprocess.run')
    @patch('download_archive_collection.time.sleep')
    def test_download_item_with_retry_success(self, mock_sleep, mock_run):
        """Test successful item download."""
        mock_run.return_value = Mock(returncode=0, stderr="")
        
        item_id, success = self.downloader._download_item_with_retry("test_item")
        
        self.assertEqual(item_id, "test_item")
        self.assertTrue(success)
        mock_run.assert_called_once_with(
            ['ia', 'download', 'test_item'],
            capture_output=True,
            text=True,
            check=True,
            timeout=300
        )

    @patch('download_archive_collection.subprocess.run')
    @patch('download_archive_collection.time.sleep')
    def test_download_item_with_retry_failure(self, mock_sleep, mock_run):
        """Test item download failure with retries."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'ia', stderr="Download failed")
        
        item_id, success = self.downloader._download_item_with_retry("test_item")
        
        self.assertEqual(item_id, "test_item")
        self.assertFalse(success)
        # Should be called max_retries + 1 times (1 + 1 = 2 in this case)
        self.assertEqual(mock_run.call_count, 2)

    def test_statistics_tracking(self):
        """Test that statistics are properly tracked."""
        self.assertEqual(self.downloader.success_count, 0)
        self.assertEqual(self.downloader.failure_count, 0)
        self.assertEqual(self.downloader.total_items, 0)


class TestUtilityFunctions(unittest.TestCase):
    """Test cases for utility functions."""

    def test_create_argument_parser(self):
        """Test argument parser creation and default values."""
        parser = create_argument_parser()
        
        # Test with minimal arguments
        args = parser.parse_args(['test_collection'])
        self.assertEqual(args.collection_identifier, 'test_collection')
        self.assertEqual(args.max_workers, 5)
        self.assertEqual(args.rate_limit, 1.0)
        self.assertEqual(args.max_retries, 3)
        self.assertFalse(args.verbose)

    def test_create_argument_parser_with_options(self):
        """Test argument parser with all options."""
        parser = create_argument_parser()
        
        args = parser.parse_args([
            'test_collection',
            '--max-workers', '10',
            '--rate-limit', '0.5',
            '--max-retries', '5',
            '--verbose'
        ])
        
        self.assertEqual(args.collection_identifier, 'test_collection')
        self.assertEqual(args.max_workers, 10)
        self.assertEqual(args.rate_limit, 0.5)
        self.assertEqual(args.max_retries, 5)
        self.assertTrue(args.verbose)

    @patch('download_archive_collection.logging.basicConfig')
    def test_setup_logging(self, mock_basic_config):
        """Test logging setup."""
        setup_logging(verbose=True)
        mock_basic_config.assert_called_once()


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow."""

    @patch('download_archive_collection.shutil.which')
    @patch('download_archive_collection.subprocess.run')
    def test_download_collection_integration(self, mock_run, mock_which):
        """Test the complete download collection workflow."""
        # Setup mocks
        mock_which.return_value = '/usr/bin/ia'
        
        # Mock collection search
        search_mock = Mock(stdout="item1\nitem2\n", stderr="", returncode=0)
        # Mock successful downloads
        download_mock = Mock(returncode=0, stderr="")
        
        mock_run.side_effect = [search_mock, download_mock, download_mock]
        
        downloader = InternetArchiveDownloader(max_workers=1, rate_limit=0.0, max_retries=1)
        
        # This should complete without raising exceptions
        downloader.download_collection("test_collection")
        
        # Verify statistics
        self.assertEqual(downloader.total_items, 2)
        self.assertEqual(downloader.success_count, 2)
        self.assertEqual(downloader.failure_count, 0)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)