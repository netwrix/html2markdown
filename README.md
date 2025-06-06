# HTML to Markdown Converter

A Python application that converts HTML documentation files to Markdown format while preserving directory structure and managing assets intelligently.

## Features

- **Directory Structure Preservation**: Maintains the original folder hierarchy while normalizing paths
- **Smart Image Management**: 
  - Moves all images to a centralized `static/img/project_name` folder
  - Deduplicates images based on content using SHA256 hashing
  - Removes unreferenced images automatically
- **Path Normalization**:
  - Converts all paths to lowercase
  - Replaces spaces with underscores
  - Uses absolute paths for all references
- **Content Extraction**: Extracts only the main content (div role="main"), excluding navigation elements
- **Markdown Enhancement**:
  - Converts HTML code blocks to proper markdown with triple backticks
  - Generates proper markdown-style anchor links
  - Excludes HTML title attributes from links and images

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd html2markdown
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python3 main.py --input /path/to/html/docs --output /path/to/output/docs
```

### Options

- `--input, -i`: Input directory containing HTML files (required)
- `--output, -o`: Output directory for markdown files (required)
- `--validate`: Run validation after conversion to check paths and naming
- `--force`: Overwrite output directory if it exists

### Example

```bash
python3 main.py --input ../product_docs/1secure --output ../output_docs/1secure --force --validate
```

## Output Structure

Given an input structure like:
```
product_docs/
└── ProjectName/
    ├── index.html
    ├── guide/
    │   └── setup.html
    └── images/
        └── screenshot.png
```

The converter produces:
```
output_docs/
└── projectname/
    ├── index.md
    └── guide/
        └── setup.md

static/
└── img/
    └── projectname/
        └── screenshot.png
```

## How It Works

1. **Preprocessing**: HTML files are parsed and only the main content is extracted
2. **Path Resolution**: All links and image references are resolved to absolute paths
3. **Conversion**: HTML is converted to Markdown using customized conversion rules
4. **Image Processing**: Images are deduplicated and moved to the static folder
5. **Path Updates**: All image references in Markdown files are updated to point to the new locations
6. **Cleanup**: Empty directories and unreferenced images are removed

## Architecture

- `main.py`: CLI entry point
- `converter.py`: Main orchestrator for the conversion process
- `preprocessor.py`: HTML preprocessing and content extraction
- `markdown_converter.py`: Custom Markdown conversion rules
- `image_manager.py`: Image deduplication and management
- `path_resolver.py`: Path resolution and normalization
- `file_handler.py`: File system operations
- `validator.py`: Output validation
- `utils.py`: Utility functions

## Requirements

- Python 3.6+
- Dependencies listed in `requirements.txt`:
  - markdownify>=0.11.6
  - beautifulsoup4>=4.12.0
  - lxml>=4.9.0
  - click>=8.1.0
  - tqdm>=4.65.0
  - pathlib2>=2.3.7