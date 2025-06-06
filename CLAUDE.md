# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: HTML to Markdown Converter

This repository contains a Python application for converting HTML documentation to Markdown format with intelligent image handling and path resolution.

## Project Structure

The project follows a modular architecture with these key components:
- `converter.py` - Main orchestrator class
- `preprocessor.py` - HTML parsing and preprocessing
- `markdown_converter.py` - Custom markdown conversion logic
- `image_manager.py` - Image deduplication and management
- `path_resolver.py` - Path resolution and normalization
- `validator.py` - Output validation

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the converter
python -m html2markdown --input <input_dir> --output <output_dir>

# Run with validation
python -m html2markdown --input <input_dir> --output <output_dir> --validate

# Run tests (when implemented)
pytest tests/

# Linting (when configured)
flake8 html2markdown/
black html2markdown/
```

## Key Implementation Details

1. **Image Handling**: Images are deduplicated using SHA256 hashing and moved to `./static/img/project_name/`
2. **Path Resolution**: All paths are converted to absolute paths starting with `./`
3. **Naming Convention**: All files and directories use lowercase with underscores instead of spaces
4. **Code Blocks**: HTML code tags are converted to triple backtick markdown code blocks

## Architecture Notes

- Uses `markdownify` with custom extensions for HTML to Markdown conversion
- BeautifulSoup4 for HTML preprocessing and link/image extraction
- Content-based image deduplication prevents duplicate storage
- Two-phase validation ensures output meets all requirements

See `HTML_TO_MARKDOWN_IMPLEMENTATION_PLAN.md` for detailed implementation guidance.