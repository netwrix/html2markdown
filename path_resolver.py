"""Path resolution and normalization for HTML to Markdown converter."""

import os
from pathlib import Path
from urllib.parse import unquote
from utils import is_external_url, is_special_link, normalize_path, extract_anchor


class PathResolver:
    """Handles path resolution and normalization."""
    
    def __init__(self, input_dir, output_dir, project_name):
        self.input_dir = Path(input_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.project_name = project_name
        # Use output directory name for static path
        output_dirname = self.output_dir.name
        self.static_dir = self.output_dir.parent / 'static' / 'img' / output_dirname
        
        # Cache for resolved paths
        self.path_cache = {}
        
    def resolve_path(self, current_file, target_path, path_type='document'):
        """Resolve a path from current file to target, converting to new structure."""
        # Create cache key
        cache_key = (str(current_file), target_path, path_type)
        if cache_key in self.path_cache:
            return self.path_cache[cache_key]
        
        # Handle external URLs and special links
        if is_external_url(target_path) or is_special_link(target_path):
            self.path_cache[cache_key] = target_path
            return target_path
        
        # Decode URL-encoded paths
        target_path = unquote(target_path)
        
        # Extract anchor if present
        path_part, anchor = extract_anchor(target_path)
        
        # For images, we need to resolve the actual file path first
        # This will be done later by the image manager
        if path_type == 'image':
            # Just return a placeholder path that will be resolved after image processing
            result = self._get_placeholder_image_path(path_part)
        else:
            # Resolve relative path to absolute for documents
            if path_part.startswith('/'):
                # Already absolute from input root
                absolute_path = self.input_dir / path_part.lstrip('/')
            else:
                # Relative path
                current_dir = Path(current_file).parent
                absolute_path = (current_dir / path_part).resolve()
            
            # Normalize the path
            try:
                relative_to_input = absolute_path.relative_to(self.input_dir)
            except ValueError:
                # Path is outside input directory
                print(f"Warning: Path {absolute_path} is outside input directory")
                relative_to_input = Path(path_part)
            
            normalized_path = normalize_path(relative_to_input)
            result = self._convert_to_document_path(normalized_path) + anchor
        
        # Cache the result
        self.path_cache[cache_key] = result
        return result
    
    def _convert_to_static_path(self, normalized_path):
        """Convert a normalized path to static image path."""
        # Remove any directory structure and just use the filename
        filename = normalized_path.name
        output_dirname = self.output_dir.name
        return f"./static/img/{output_dirname}/{filename}"
    
    def _get_placeholder_image_path(self, original_path):
        """Get a placeholder path for an image that will be resolved later."""
        # Extract just the filename from the path
        filename = Path(original_path).name
        normalized_filename = normalize_path(filename)
        output_dirname = self.output_dir.name
        return f"./static/img/{output_dirname}/{normalized_filename}"
    
    def _convert_to_document_path(self, normalized_path):
        """Convert a normalized path to document path."""
        # Change extension from .htm/.html to .md
        path_str = str(normalized_path)
        if path_str.endswith('.htm'):
            path_str = path_str[:-4] + '.md'
        elif path_str.endswith('.html'):
            path_str = path_str[:-5] + '.md'
        
        # Apply the same duplicate removal logic as in get_output_path
        path_parts = list(Path(path_str).parts)
        
        if path_parts:
            input_name = self.input_dir.name.lower()
            # If we're processing a single product (e.g., product_docs/1Secure)
            # and the first part of the path is the same product name, skip it
            if path_parts[0].lower() == input_name:
                # This handles the 1Secure/1Secure case
                path_parts = path_parts[1:] if len(path_parts) > 1 else []
            # Also check for consecutive duplicates
            elif len(path_parts) >= 2 and path_parts[0].lower() == path_parts[1].lower():
                path_parts = path_parts[1:]
        
        path_str = str(Path(*path_parts)) if path_parts else ''
        
        # Return as absolute path from output root
        output_dir_name = self.output_dir.name
        return f"/{output_dir_name}/{path_str}"
    
    def get_output_path(self, input_file):
        """Get the output path for a given input file."""
        try:
            relative_path = Path(input_file).relative_to(self.input_dir)
        except ValueError:
            raise ValueError(f"Input file {input_file} is not within input directory {self.input_dir}")
        
        # Normalize the path
        normalized = normalize_path(relative_path)
        
        # Check for duplicate directory names in path
        # Handle the common pattern where products have Product/Product/... structure
        path_parts = list(normalized.parts)
        
        if path_parts:
            input_name = self.input_dir.name.lower()
            # If we're processing a single product (e.g., product_docs/1Secure)
            # and the first part of the path is the same product name, skip it
            if path_parts[0].lower() == input_name:
                # This handles the 1Secure/1Secure case
                path_parts = path_parts[1:] if len(path_parts) > 1 else []
            # Also check for consecutive duplicates
            elif len(path_parts) >= 2 and path_parts[0].lower() == path_parts[1].lower():
                path_parts = path_parts[1:]
        
        normalized = Path(*path_parts) if path_parts else Path('.')
        
        # Change extension
        path_str = str(normalized)
        if path_str.endswith('.htm'):
            path_str = path_str[:-4] + '.md'
        elif path_str.endswith('.html'):
            path_str = path_str[:-5] + '.md'
        
        return self.output_dir / path_str
    
    def get_static_image_path(self, image_filename):
        """Get the full static path for an image file."""
        return self.static_dir / image_filename