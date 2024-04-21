import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm  # tqdm is a library to show progress bars

def download_item(item_id):
    """Function to download a single item using the `ia` command and include rate-limiting."""
    try:
        time.sleep(1)  # Sleep for 1 second for rate-limiting
        subprocess.run(['ia', 'download', item_id], check=True)
        return item_id, True
    except subprocess.CalledProcessError as e:
        print(f"Failed to download item {item_id}: {e}", file=sys.stderr)
        return item_id, False

def download_collection(collection_identifier):
    """Function to download all items in a collection with progress reporting and rate-limiting."""
    try:
        process = subprocess.run(['ia', 'search', f'collection:{collection_identifier}', '--itemlist'],
                                 capture_output=True, text=True, check=True)
        item_identifiers = process.stdout.strip().split('\n')
    except subprocess.CalledProcessError as e:
        print(f"Failed to fetch collection items: {e}", file=sys.stderr)
        return

    print(f"Starting download of {len(item_identifiers)} items from the collection '{collection_identifier}'.")

    # Use ThreadPoolExecutor to download items in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(download_item, item_id): item_id for item_id in item_identifiers}
        for future in tqdm(as_completed(futures), total=len(item_identifiers), desc="Downloading", unit="item"):
            item_id, success = future.result()
            if success:
                print(f"Successfully downloaded {item_id}.")
            else:
                print(f"Failed to download {item_id}.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download_archive_collection.py <collection_identifier>")
        sys.exit(1)

    collection_id = sys.argv[1]
    download_collection(collection_id)

