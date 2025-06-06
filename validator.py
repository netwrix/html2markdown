"""Output validation for HTML to Markdown converter."""

import os
import re
from pathlib import Path
from utils import is_external_url, is_special_link


class OutputValidator:
    """Validates the output of the conversion."""
    
    def __init__(self, output_dir, static_dir):
        self.output_dir = Path(output_dir)
        self.static_dir = Path(static_dir)
        self.errors = []
        self.warnings = []
    
    def validate(self):
        """Run all validation checks."""
        print("\nRunning validation...")
        
        # Clear previous results
        self.errors = []
        self.warnings = []
        
        # Run validation checks
        self._validate_naming_conventions()
        self._validate_markdown_files()
        
        # Report results
        self._report_results()
        
        return len(self.errors) == 0
    
    def _validate_naming_conventions(self):
        """Validate that all files and directories follow naming conventions."""
        # Check output directory
        for root, dirs, files in os.walk(self.output_dir):
            # Check directory names
            for dir_name in dirs:
                if dir_name != dir_name.lower():
                    self.errors.append(f"Directory not lowercase: {root}/{dir_name}")
                if ' ' in dir_name:
                    self.errors.append(f"Directory contains spaces: {root}/{dir_name}")
            
            # Check file names
            for file_name in files:
                if file_name != file_name.lower():
                    self.errors.append(f"File not lowercase: {root}/{file_name}")
                if ' ' in file_name:
                    self.errors.append(f"File contains spaces: {root}/{file_name}")
        
        # Check static directory if it exists
        if self.static_dir.exists():
            for root, dirs, files in os.walk(self.static_dir):
                for file_name in files:
                    if file_name != file_name.lower():
                        self.warnings.append(f"Static file not lowercase: {root}/{file_name}")
                    if ' ' in file_name:
                        self.warnings.append(f"Static file contains spaces: {root}/{file_name}")
    
    def _validate_markdown_files(self):
        """Validate content of markdown files."""
        # Find all markdown files
        md_files = list(self.output_dir.rglob('*.md'))
        
        for md_file in md_files:
            self._validate_markdown_file(md_file)
    
    def _validate_markdown_file(self, file_path):
        """Validate a single markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (IOError, OSError) as e:
            self.errors.append(f"Cannot read file {file_path}: {e}")
            return
        
        # Extract all links and images
        links = self._extract_links(content)
        images = self._extract_images(content)
        
        # Validate links
        for link, line_num in links:
            if is_external_url(link) or is_special_link(link):
                continue
            
            if not link.startswith('./'):
                self.errors.append(
                    f"Relative path found in {file_path}:{line_num} - {link}"
                )
            else:
                # Check if referenced file exists
                self._check_link_target(link, file_path, line_num)
        
        # Validate images
        for image, line_num in images:
            if is_external_url(image):
                continue
            
            if not image.startswith('./'):
                self.errors.append(
                    f"Relative image path in {file_path}:{line_num} - {image}"
                )
            else:
                # Check if image exists
                self._check_image_target(image, file_path, line_num)
    
    def _extract_links(self, content):
        """Extract all markdown links from content."""
        links = []
        lines = content.split('\n')
        
        # Match [text](url) pattern
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        
        for i, line in enumerate(lines, 1):
            for match in re.finditer(pattern, line):
                url = match.group(2).split()[0]  # Handle titles in links
                links.append((url, i))
        
        return links
    
    def _extract_images(self, content):
        """Extract all markdown images from content."""
        images = []
        lines = content.split('\n')
        
        # Match ![text](url) pattern
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        
        for i, line in enumerate(lines, 1):
            for match in re.finditer(pattern, line):
                url = match.group(2).split()[0]  # Handle titles in images
                images.append((url, i))
        
        return images
    
    def _check_link_target(self, link, source_file, line_num):
        """Check if a link target exists."""
        # Remove anchor if present
        if '#' in link:
            link = link.split('#')[0]
        
        if not link:  # Just an anchor
            return
        
        # Calculate target path
        if link.startswith('./static/'):
            # Static file
            target = self.output_dir.parent / link[2:]
        else:
            # Relative to output dir
            target = self.output_dir.parent / link[2:]
        
        if not target.exists():
            self.errors.append(
                f"Broken link in {source_file}:{line_num} - {link} (resolved to {target})"
            )
    
    def _check_image_target(self, image_path, source_file, line_num):
        """Check if an image target exists."""
        # Calculate target path
        if image_path.startswith('./static/'):
            target = self.output_dir.parent / image_path[2:]
        else:
            target = self.output_dir.parent / image_path[2:]
        
        if not target.exists():
            self.errors.append(
                f"Missing image in {source_file}:{line_num} - {image_path} (resolved to {target})"
            )
    
    def _report_results(self):
        """Report validation results."""
        print("\nValidation Results:")
        print("-" * 50)
        
        if self.errors:
            print(f"\n❌ Found {len(self.errors)} errors:")
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more errors")
        else:
            print("✅ No errors found!")
        
        if self.warnings:
            print(f"\n⚠️  Found {len(self.warnings)} warnings:")
            for warning in self.warnings[:10]:  # Show first 10 warnings
                print(f"  - {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more warnings")
        
        print("-" * 50)