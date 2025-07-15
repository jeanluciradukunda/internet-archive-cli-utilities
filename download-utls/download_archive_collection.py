#!/usr/bin/env python3
"""
Internet Archive Collection Downloader

A robust script for downloading collections from the Internet Archive with advanced
features including retry logic, configurable concurrency, and comprehensive logging.

Author: Internet Archive CLI Utilities
License: See LICENSE file in the repository
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple, List, Optional

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


class DependencyError(Exception):
    """Raised when a required dependency is missing."""
    pass


class DownloadError(Exception):
    """Raised when a download operation fails."""
    pass


class InternetArchiveDownloader:
    """
    A class to handle downloading collections from the Internet Archive.
    
    This class provides methods to download entire collections with configurable
    retry logic, rate limiting, and progress reporting.
    """

    def __init__(self, max_workers: int = 5, rate_limit: float = 1.0, max_retries: int = 3):
        """
        Initialize the downloader with configuration parameters.
        
        Args:
            max_workers: Maximum number of concurrent download threads
            rate_limit: Delay between downloads in seconds for rate limiting
            max_retries: Maximum number of retry attempts for failed downloads
        """
        self.max_workers = max_workers
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)
        
        # Statistics tracking
        self.success_count = 0
        self.failure_count = 0
        self.total_items = 0

    def _check_dependencies(self) -> None:
        """
        Check for required dependencies and raise DependencyError if missing.
        
        Raises:
            DependencyError: If required dependencies are missing
        """
        # Check for 'ia' command
        if not shutil.which('ia'):
            raise DependencyError(
                "The 'ia' command is not available. Please install the Internet Archive CLI tool.\n"
                "Install with: pip install internetarchive"
            )
        
        # Check for tqdm (optional but recommended)
        if tqdm is None:
            self.logger.warning(
                "tqdm is not installed. Progress bars will not be displayed. "
                "Install with: pip install tqdm"
            )

    def _download_item_with_retry(self, item_id: str) -> Tuple[str, bool]:
        """
        Download a single item with retry logic and exponential backoff.
        
        Args:
            item_id: The identifier of the item to download
            
        Returns:
            Tuple of (item_id, success_boolean)
        """
        for attempt in range(self.max_retries + 1):
            try:
                # Rate limiting
                if self.rate_limit > 0:
                    time.sleep(self.rate_limit)
                
                # Attempt download
                result = subprocess.run(
                    ['ia', 'download', item_id],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=300  # 5 minute timeout per item
                )
                
                self.logger.info(f"Successfully downloaded item: {item_id}")
                return item_id, True
                
            except subprocess.CalledProcessError as e:
                error_msg = f"Download failed for {item_id} (attempt {attempt + 1}/{self.max_retries + 1})"
                if e.stderr:
                    error_msg += f": {e.stderr.strip()}"
                
                if attempt < self.max_retries:
                    # Exponential backoff: 2^attempt seconds
                    backoff_time = 2 ** attempt
                    self.logger.warning(f"{error_msg}. Retrying in {backoff_time} seconds...")
                    time.sleep(backoff_time)
                else:
                    self.logger.error(f"{error_msg}. No more retries.")
                    
            except subprocess.TimeoutExpired:
                error_msg = f"Download timeout for {item_id} (attempt {attempt + 1}/{self.max_retries + 1})"
                if attempt < self.max_retries:
                    backoff_time = 2 ** attempt
                    self.logger.warning(f"{error_msg}. Retrying in {backoff_time} seconds...")
                    time.sleep(backoff_time)
                else:
                    self.logger.error(f"{error_msg}. No more retries.")
                    
            except Exception as e:
                self.logger.error(f"Unexpected error downloading {item_id}: {str(e)}")
                break
        
        return item_id, False

    def _fetch_collection_items(self, collection_identifier: str) -> List[str]:
        """
        Fetch the list of items in a collection.
        
        Args:
            collection_identifier: The identifier of the collection
            
        Returns:
            List of item identifiers in the collection
            
        Raises:
            DownloadError: If fetching collection items fails
        """
        try:
            self.logger.info(f"Fetching items for collection: {collection_identifier}")
            
            process = subprocess.run(
                ['ia', 'search', f'collection:{collection_identifier}', '--itemlist'],
                capture_output=True,
                text=True,
                check=True,
                timeout=60  # 1 minute timeout for search
            )
            
            item_identifiers = [item.strip() for item in process.stdout.strip().split('\n') if item.strip()]
            
            if not item_identifiers:
                raise DownloadError(f"No items found in collection '{collection_identifier}'")
            
            self.logger.info(f"Found {len(item_identifiers)} items in collection")
            return item_identifiers
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to fetch collection items for '{collection_identifier}'"
            if e.stderr:
                error_msg += f": {e.stderr.strip()}"
            raise DownloadError(error_msg)
            
        except subprocess.TimeoutExpired:
            raise DownloadError(f"Timeout while fetching collection items for '{collection_identifier}'")

    def download_collection(self, collection_identifier: str) -> None:
        """
        Download all items in a collection with progress reporting and error handling.
        
        Args:
            collection_identifier: The identifier of the collection to download
            
        Raises:
            DependencyError: If required dependencies are missing
            DownloadError: If the collection cannot be fetched
        """
        # Check dependencies first
        self._check_dependencies()
        
        # Fetch collection items
        item_identifiers = self._fetch_collection_items(collection_identifier)
        self.total_items = len(item_identifiers)
        
        self.logger.info(
            f"Starting download of {self.total_items} items from collection '{collection_identifier}' "
            f"with {self.max_workers} workers"
        )

        # Create progress bar if tqdm is available
        progress_bar = None
        if tqdm is not None:
            progress_bar = tqdm(
                total=self.total_items,
                desc="Downloading",
                unit="item",
                ncols=80
            )

        # Download items using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all download tasks
            futures = {
                executor.submit(self._download_item_with_retry, item_id): item_id 
                for item_id in item_identifiers
            }
            
            # Process completed downloads
            for future in as_completed(futures):
                item_id, success = future.result()
                
                if success:
                    self.success_count += 1
                    self.logger.debug(f"Download successful: {item_id}")
                else:
                    self.failure_count += 1
                    self.logger.error(f"Download failed: {item_id}")
                
                # Update progress bar
                if progress_bar is not None:
                    progress_bar.update(1)
                    progress_bar.set_postfix({
                        'Success': self.success_count,
                        'Failed': self.failure_count
                    })

        # Close progress bar
        if progress_bar is not None:
            progress_bar.close()

        # Log final statistics
        self._log_final_statistics(collection_identifier)

    def _log_final_statistics(self, collection_identifier: str) -> None:
        """Log final download statistics."""
        self.logger.info(
            f"Download completed for collection '{collection_identifier}'. "
            f"Success: {self.success_count}, Failed: {self.failure_count}, "
            f"Total: {self.total_items}"
        )
        
        if self.failure_count > 0:
            self.logger.warning(
                f"{self.failure_count} downloads failed. Check the logs for details."
            )


def setup_logging(verbose: bool) -> None:
    """
    Set up logging configuration.
    
    Args:
        verbose: Enable debug logging if True
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('download_archive_collection.log', mode='a')
        ]
    )


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the command line argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description='Download collections from the Internet Archive',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s my_collection
  %(prog)s my_collection --max-workers 10 --rate-limit 0.5
  %(prog)s my_collection --verbose --max-retries 5
        """
    )
    
    parser.add_argument(
        'collection_identifier',
        help='Identifier of the collection to download'
    )
    
    parser.add_argument(
        '--max-workers',
        type=int,
        default=5,
        help='Maximum number of concurrent download threads (default: 5)'
    )
    
    parser.add_argument(
        '--rate-limit',
        type=float,
        default=1.0,
        help='Delay between downloads in seconds for rate limiting (default: 1.0)'
    )
    
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum number of retry attempts for failed downloads (default: 3)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging output'
    )
    
    return parser


def main() -> int:
    """
    Main entry point for the script.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Parse command line arguments
        parser = create_argument_parser()
        args = parser.parse_args()
        
        # Set up logging
        setup_logging(args.verbose)
        logger = logging.getLogger(__name__)
        
        # Create downloader instance
        downloader = InternetArchiveDownloader(
            max_workers=args.max_workers,
            rate_limit=args.rate_limit,
            max_retries=args.max_retries
        )
        
        # Download the collection
        downloader.download_collection(args.collection_identifier)
        
        # Return exit code based on results
        if downloader.failure_count > 0:
            logger.warning(f"Script completed with {downloader.failure_count} failures")
            return 1
        else:
            logger.info("Script completed successfully")
            return 0
            
    except DependencyError as e:
        print(f"Dependency error: {e}", file=sys.stderr)
        return 2
        
    except DownloadError as e:
        print(f"Download error: {e}", file=sys.stderr)
        return 3
        
    except KeyboardInterrupt:
        print("\nDownload interrupted by user", file=sys.stderr)
        return 130
        
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())

