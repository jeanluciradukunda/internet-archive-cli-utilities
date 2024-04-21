import sys
import time
import logging
from internetarchive import search_items, get_item
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import argparse
import os

# Configure Argument Parser
parser = argparse.ArgumentParser(description='Download items from a collection at archive.org')
parser.add_argument('collection_id', help='Identifier of the collection to download')
parser.add_argument('formats', help='Comma-separated list of preferred formats to download')
parser.add_argument('--max_workers', type=int, default=5, help='Maximum number of concurrent downloads')
parser.add_argument('-o', '--output', default='./downloads', help='Directory to save downloaded files')
parser.add_argument('-v', '--verbose', action='store_true', help='Increase output verbosity')
args = parser.parse_args()

# Setup logging
log_level = logging.DEBUG if args.verbose else logging.INFO
logging.basicConfig(filename='download.log', level=log_level, format='%(asctime)s %(levelname)s:%(message)s')

def validate_formats(formats):
    valid_formats = {'pdf', 'epub', 'txt', 'jpeg', 'mp3'}  # Example set of valid formats
    return [fmt for fmt in formats if fmt in valid_formats]

def download_item(item_id, formats, output_dir):
    item = get_item(item_id)
    for file_format in formats:
        files = item.get_files(glob_pattern=f"*.{file_format}")  # Updated to use glob_pattern
        if files:
            # Attempt to download the files; handle exceptions to capture download errors.
            try:
                for f in files:
                    if not os.path.exists(os.path.join(output_dir, f.name)):  # Check if file already exists to mimic ignore_existing
                        f.download(destdir=output_dir)
                        logging.info(f"Downloaded {f.name} ({f.size} bytes)")
                return item_id, file_format, True
            except Exception as e:
                logging.error(f"Download failed for {item_id} in format {file_format}. Error: {str(e)}")
    return item_id, None, False

def download_collection():
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    formats = validate_formats(args.formats.split(','))
    items = search_items(f'collection:{args.collection_id}')
    item_identifiers = [item['identifier'] for item in items]
    
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {executor.submit(download_item, item_id, formats, args.output): item_id for item_id in item_identifiers}
        progress = tqdm(as_completed(futures), total=len(item_identifiers), desc="Downloading", unit="item")
        results = [(future.result(), future) for future in progress]

    logging.info(f"Download session completed. Results summarized in download.log.")

if __name__ == "__main__":
    download_collection()

