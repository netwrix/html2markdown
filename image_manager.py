"""Image deduplication and management for HTML to Markdown converter."""

import hashlib
import shutil
from pathlib import Path
from collections import defaultdict
from utils import normalize_path, ensure_directory_exists


class ImageManager:
    """Manages image deduplication, moving, and reference tracking."""
    
    def __init__(self, project_name, output_dir):
        self.project_name = project_name
        self.output_dir = Path(output_dir)
        # Static folder should be at the same level as output_dir
        # If output_dir is /docs/markdown_docs, then static should be /docs/static
        # Use the output directory name for the static path
        output_dirname = self.output_dir.name
        self.static_dir = self.output_dir.parent / 'static' / 'img' / output_dirname
        
        # Track image references: original_path -> [(doc_path, line_num), ...]
        self.image_references = defaultdict(list)
        
        # Track image hashes: original_path -> (hash, new_filename)
        self.image_map = {}
        
        # Track hash to canonical path: hash -> new_path
        self.hash_to_path = {}
        
        # Track all moved images for cleanup
        self.moved_images = set()
        
        # Track which document references which images for directory structure
        self.doc_to_images = defaultdict(list)
        
    def calculate_hash(self, file_path):
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except (IOError, OSError) as e:
            print(f"Error hashing file {file_path}: {e}")
            return None
    
    def add_image_reference(self, original_path, source_doc, resolved_path=None):
        """Add a reference to an image from a document."""
        self.image_references[original_path].append(source_doc)
        if resolved_path:
            self.image_references[resolved_path].append(source_doc)
        # Track which images are referenced by which documents
        self.doc_to_images[source_doc].append(original_path)
    
    def process_images(self, input_dir):
        """Process all referenced images for deduplication and moving."""
        ensure_directory_exists(self.static_dir)
        input_dir = Path(input_dir)
        
        # Process each unique image reference
        processed_images = set()
        
        for original_path, source_docs in self.image_references.items():
            if original_path in processed_images:
                continue
            processed_images.add(original_path)
            
            # Skip external URLs
            if original_path.startswith(('http://', 'https://')):
                continue
            
            # For each source document that references this image
            full_path = None
            referencing_doc = None
            for source_doc in source_docs:
                # Resolve relative path from the HTML file's location
                source_doc_path = Path(source_doc)
                if source_doc_path.is_absolute():
                    source_dir = source_doc_path.parent
                else:
                    source_dir = (input_dir / source_doc).parent
                
                # Try to resolve the image path relative to the HTML file
                try:
                    resolved_path = (source_dir / original_path).resolve()
                    if resolved_path.exists():
                        full_path = resolved_path
                        referencing_doc = source_doc
                        break
                except Exception:
                    continue
            
            if not full_path or not full_path.exists():
                print(f"Warning: Image not found: {original_path}")
                continue
            
            # Calculate hash
            file_hash = self.calculate_hash(full_path)
            if not file_hash:
                continue
            
            # Determine the subdirectory structure based on the referencing document
            if referencing_doc:
                # Get the relative path of the document from input_dir
                try:
                    doc_relative = Path(referencing_doc).relative_to(input_dir)
                except ValueError:
                    doc_relative = Path(referencing_doc)
                
                # Normalize the document path and get its directory structure
                normalized_doc_path = normalize_path(doc_relative)
                doc_subdir = normalized_doc_path.parent
                
                # When project_name is "product_docs", we need special handling
                # The structure is product_docs/Product/Product/... 
                # We want to create static/img/product_docs/Product/... (without the duplicate)
                subdir_parts = list(doc_subdir.parts)
                
                if self.project_name.lower() == "product_docs" and subdir_parts:
                    # For product_docs, check if first two parts after product_docs are duplicates
                    # e.g., 1secure/1secure/admin -> 1secure/admin
                    if len(subdir_parts) >= 2 and subdir_parts[0].lower() == subdir_parts[1].lower():
                        subdir_parts = subdir_parts[1:]
                elif subdir_parts:
                    # For other cases, check if first component matches project name
                    if subdir_parts[0].lower() == self.project_name.lower():
                        subdir_parts = subdir_parts[1:] if len(subdir_parts) > 1 else []
                    # Check for duplicate directories (e.g., 1secure/1secure)
                    elif len(subdir_parts) >= 2 and subdir_parts[0].lower() == subdir_parts[1].lower():
                        subdir_parts = subdir_parts[1:]
                
                doc_subdir = Path(*subdir_parts) if subdir_parts else Path('.')
                
                # Create the subdirectory in static folder
                if str(doc_subdir) != '.':
                    image_subdir = self.static_dir / doc_subdir
                else:
                    image_subdir = self.static_dir
            else:
                image_subdir = self.static_dir
            
            # Check if we've already processed this hash
            if file_hash in self.hash_to_path:
                # Duplicate found, map to existing file
                self.image_map[original_path] = (file_hash, self.hash_to_path[file_hash])
            else:
                # New image, create filename without hash
                original_name = normalize_path(full_path.name)
                new_filename = str(original_name)
                
                # Ensure the subdirectory exists
                ensure_directory_exists(image_subdir)
                
                # Check if a file with this name already exists (different content)
                new_path = image_subdir / new_filename
                if new_path.exists():
                    # Calculate hash of existing file
                    existing_hash = self.calculate_hash(new_path)
                    if existing_hash != file_hash:
                        # Different file with same name - need to handle conflict
                        # Add a number suffix to make it unique
                        name_parts = str(original_name).rsplit('.', 1)
                        if len(name_parts) == 2:
                            base_name, extension = name_parts
                            counter = 1
                            while True:
                                new_filename = f"{base_name}_{counter}.{extension}"
                                new_path = image_subdir / new_filename
                                if not new_path.exists():
                                    break
                                counter += 1
                        else:
                            counter = 1
                            while True:
                                new_filename = f"{original_name}_{counter}"
                                new_path = image_subdir / new_filename
                                if not new_path.exists():
                                    break
                                counter += 1
                        print(f"Warning: Filename conflict for {original_name}, using {new_filename}")
                    else:
                        # Same content, just use existing file
                        relative_path = new_path.relative_to(self.static_dir)
                        self.moved_images.add(str(new_path))
                        self.hash_to_path[file_hash] = str(relative_path)
                        self.image_map[original_path] = (file_hash, str(relative_path))
                        continue
                
                # Copy the image
                try:
                    shutil.copy2(full_path, new_path)
                    relative_path = new_path.relative_to(self.static_dir)
                    self.moved_images.add(str(new_path))
                    self.hash_to_path[file_hash] = str(relative_path)
                    self.image_map[original_path] = (file_hash, str(relative_path))
                    print(f"Copied image: {full_path} -> {new_path}")
                except (IOError, OSError) as e:
                    print(f"Error copying image {full_path}: {e}")
    
    def get_new_image_path(self, original_path):
        """Get the new path for an image after deduplication."""
        if original_path in self.image_map:
            _, new_relative_path = self.image_map[original_path]
            output_dirname = self.output_dir.name
            return f"/static/img/{output_dirname}/{new_relative_path}"
        return original_path
    
    def get_new_image_path_by_filename(self, filename):
        """Get the new path for an image by its filename."""
        # Normalize the filename
        normalized_filename = normalize_path(filename).name
        output_dirname = self.output_dir.name
        
        # Look through all processed images to find a match
        for original_path, (file_hash, new_relative_path) in self.image_map.items():
            # Check if the normalized filename matches
            original_normalized = normalize_path(Path(original_path).name)
            if str(original_normalized) == str(normalized_filename):
                return f"/static/img/{output_dirname}/{new_relative_path}"
        
        # If not found in the map, search recursively in static dir
        if self.static_dir.exists():
            # Search recursively for the file
            for img_file in self.static_dir.rglob(str(normalized_filename)):
                relative_path = img_file.relative_to(self.static_dir)
                return f"/static/img/{output_dirname}/{relative_path}"
            
            # Then try with number suffix (for conflicts)
            if isinstance(normalized_filename, Path):
                pattern = f"{normalized_filename.stem}_*{normalized_filename.suffix}"
            else:
                pattern = f"{Path(normalized_filename).stem}_*{Path(normalized_filename).suffix}"
            
            for img_file in self.static_dir.rglob(pattern):
                relative_path = img_file.relative_to(self.static_dir)
                return f"/static/img/{output_dirname}/{relative_path}"
        
        return None
    
    def remove_unreferenced_images(self):
        """Remove images in static directory that aren't referenced."""
        if not self.static_dir.exists():
            return
        
        # Get all images in static directory (recursively)
        all_images = set()
        for img_file in self.static_dir.rglob('*'):
            if img_file.is_file():
                all_images.add(str(img_file))
        
        # Find unreferenced images
        unreferenced = all_images - self.moved_images
        
        # Remove unreferenced images
        for img_path in unreferenced:
            try:
                Path(img_path).unlink()
                print(f"Removed unreferenced image: {img_path}")
            except (IOError, OSError) as e:
                print(f"Error removing image {img_path}: {e}")
    
    def get_deduplication_stats(self):
        """Get statistics about image deduplication."""
        total_references = len(self.image_references)
        unique_hashes = len(self.hash_to_path)
        space_saved = total_references - unique_hashes
        
        return {
            'total_references': total_references,
            'unique_images': unique_hashes,
            'duplicates_removed': space_saved,
            'deduplication_ratio': f"{(space_saved / total_references * 100):.1f}%" if total_references > 0 else "0%"
        }