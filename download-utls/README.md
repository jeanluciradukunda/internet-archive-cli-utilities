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

Install the `internetarchive` Python library and other necessary libraries if you haven't already, and the `tqdm` Python library:

```bash
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

This script downloads all items from a specified collection in Archive.org.

**Usage:**
```bash
python download_archive_collection.py <collection_identifier>
```
- `<collection_identifier>`: The unique identifier for the collection you wish to download.

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

## Example Command
```bash
python download_archive_collection_types.py mycollection pdf,epub --max_workers 10 -o ~/downloads -v
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests to us.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.