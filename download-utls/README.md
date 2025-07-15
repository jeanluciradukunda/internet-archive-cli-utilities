# Archive.org Collection Downloader

This repository contains two Python scripts for downloading items from collections on Archive.org. The first script downloads an entire collection without filtering by format, while the second script offers more advanced features, including format filtering, logging, and command-line options for enhanced usability.

## Setup Instructions

### Prerequisites

- Python 3.x
- pip (Python package installer)

### Creating a Virtual Environment

Before installing the dependencies, it's recommended to create a Python virtual environment. This isolates your project dependencies from other Python projects. Here's how you can set it up:

```bash
# Create a virtual environment (replace 'env' with the name of your environment)
python -m venv env

# Activate the virtual environment
# On Windows
env\Scripts\activate
# On MacOS/Linux
source env/bin/activate
```

### Library Installation

Install the required Python libraries using pip. You can install them individually or use the requirements file:

```bash
# Install from requirements file (recommended)
pip install -r requirements.txt

# Or install individually
pip install internetarchive tqdm
```

### Configure Internet Archive Access

You might need to configure access to your Internet Archive account for some functionalities, like downloading restricted files. You can do this by running:

```bash
ia configure
```

Follow the prompts to enter your Archive.org email and password. This will save your credentials locally and allow the script to access the site as you.

## Scripts Overview

### 1. `download_archive_collection.py`

This script downloads all items from a specified collection in Archive.org with advanced features including retry logic, configurable concurrency, rate limiting, and comprehensive logging.

**Usage:**
```bash
python download_archive_collection.py <collection_identifier> [options]
```

**Parameters:**
- `collection_identifier`: The unique identifier for the collection you wish to download.

**Options:**
- `--max-workers MAX_WORKERS`: Maximum number of concurrent download threads (default: 5)
- `--rate-limit RATE_LIMIT`: Delay between downloads in seconds for rate limiting (default: 1.0)
- `--max-retries MAX_RETRIES`: Maximum number of retry attempts for failed downloads (default: 3)
- `--verbose, -v`: Enable verbose logging output

**Features:**
- Automatic dependency checking (verifies 'ia' command and tqdm library)
- Retry logic with exponential backoff for failed downloads
- Progress reporting with success/failure counts
- Comprehensive logging to both console and file
- Rate limiting to respect Archive.org servers
- Configurable concurrency levels
- Robust error handling with specific exception types

**Examples:**
```bash
# Basic usage
python download_archive_collection.py my_collection

# With custom settings
python download_archive_collection.py my_collection --max-workers 10 --rate-limit 0.5

# Verbose mode with more retries
python download_archive_collection.py my_collection --verbose --max-retries 5
```

### 2. `download_archive_collection_types.py`

This script offers more control over the download process, allowing you to specify file formats and other parameters.

**Usage:**
```bash
python download_archive_collection_types.py <collection_id> <formats> [options]
```

**Parameters:**
- `collection_id`: Identifier of the collection to download. This is the unique handle on Archive.org for the collection.
- `formats`: Comma-separated list of preferred formats to download (e.g., pdf, epub).

**Options:**
- `--max_workers`: Maximum number of concurrent downloads; default is 5.
- `-o`, `--output`: Specify the directory where downloaded files should be saved; default is `./downloads`.
- `-v`, `--verbose`: Enable verbose output to increase logging detail, helpful for debugging.

## Testing

Unit tests are provided for the `download_archive_collection.py` script to ensure reliability and proper error handling.

**Running Tests:**
```bash
# Run all tests
python test_download_archive_collection.py

# Run tests with verbose output
python test_download_archive_collection.py -v
```

**Test Coverage:**
- Dependency checking and error handling
- Collection fetching with success and failure scenarios
- Item download retry logic with exponential backoff
- Statistics tracking and progress reporting
- Command-line argument parsing
- Logging configuration

## Example Command
```bash
python download_archive_collection_types.py mycollection pdf,epub --max_workers 10 -o ~/downloads -v
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests to us.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.