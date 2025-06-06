"""File system operations for HTML to Markdown converter."""

import os
import shutil
from pathlib import Path
from utils import ensure_directory_exists, normalize_path


class FileSystemHandler:
    """Handles file system operations."""
    
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
    
    def create_output_structure(self, input_dir):
        """Create the output directory structure based on input."""
        input_path = Path(input_dir)
        
        # Walk through input directory
        for root, dirs, files in os.walk(input_path):
            # Calculate relative path from input root
            rel_path = Path(root).relative_to(input_path)
            
            # Normalize the path
            normalized_path = normalize_path(rel_path)
            
            # Create corresponding directory in output
            output_path = self.output_dir / normalized_path
            ensure_directory_exists(output_path)
    
    def write_file(self, content, output_path):
        """Write content to a file."""
        output_path = Path(output_path)
        
        # Ensure directory exists
        ensure_directory_exists(output_path.parent)
        
        # Write the file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except (IOError, OSError) as e:
            print(f"Error writing file {output_path}: {e}")
            return False
    
    def read_file(self, file_path):
        """Read content from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except (IOError, OSError) as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    def find_html_files(self, input_dir):
        """Find all HTML files in the input directory."""
        input_path = Path(input_dir)
        html_files = []
        
        # Walk through directory
        for root, dirs, files in os.walk(input_path):
            for file in files:
                if file.lower().endswith(('.html', '.htm')):
                    html_files.append(Path(root) / file)
        
        return html_files
    
    def cleanup_empty_directories(self):
        """Remove empty directories from output."""
        # Walk through output directory bottom-up
        for root, dirs, files in os.walk(self.output_dir, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    # Try to remove directory (will fail if not empty)
                    dir_path.rmdir()
                    print(f"Removed empty directory: {dir_path}")
                except OSError:
                    # Directory not empty, skip
                    pass
    
    def copy_non_html_files(self, input_dir, exclude_patterns=None):
        """Copy non-HTML files maintaining structure."""
        input_path = Path(input_dir)
        exclude_patterns = exclude_patterns or ['.html', '.htm']
        
        for root, dirs, files in os.walk(input_path):
            rel_path = Path(root).relative_to(input_path)
            normalized_path = normalize_path(rel_path)
            output_path = self.output_dir / normalized_path
            
            for file in files:
                # Skip HTML files
                if any(file.lower().endswith(pattern) for pattern in exclude_patterns):
                    continue
                
                # Skip image files (they'll be handled by ImageManager)
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')):
                    continue
                
                # Copy other files
                src = Path(root) / file
                dst = output_path / normalize_path(file)
                
                try:
                    ensure_directory_exists(dst.parent)
                    shutil.copy2(src, dst)
                    print(f"Copied file: {src} -> {dst}")
                except (IOError, OSError) as e:
                    print(f"Error copying file {src}: {e}")