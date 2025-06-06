"""Main HTML to Markdown converter orchestrator."""

import re
from pathlib import Path
from tqdm import tqdm

from path_resolver import PathResolver
from image_manager import ImageManager
from preprocessor import HtmlPreprocessor
from markdown_converter import CustomMarkdownConverter
from file_handler import FileSystemHandler
from validator import OutputValidator
from utils import ensure_directory_exists


class HtmlToMarkdownConverter:
    """Main converter class that orchestrates the conversion process."""
    
    def __init__(self, input_dir, output_dir):
        self.input_dir = Path(input_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        
        # Extract project name from output directory
        self.project_name = self.output_dir.name
        
        # Initialize components
        self.path_resolver = PathResolver(self.input_dir, self.output_dir, self.project_name)
        self.image_manager = ImageManager(self.project_name, self.output_dir)
        self.preprocessor = HtmlPreprocessor(self.path_resolver, self.image_manager)
        self.markdown_converter = CustomMarkdownConverter()
        self.file_handler = FileSystemHandler(self.output_dir)
        
        # Validator will be initialized after conversion
        self.validator = None
        
    def convert(self):
        """Run the complete conversion process."""
        print(f"Converting HTML files from {self.input_dir} to {self.output_dir}")
        print(f"Project name: {self.project_name}")
        
        # Phase 1: Setup
        ensure_directory_exists(self.output_dir)
        self.file_handler.create_output_structure(self.input_dir)
        
        # Phase 2: Find all HTML files
        html_files = self.file_handler.find_html_files(self.input_dir)
        print(f"Found {len(html_files)} HTML files to convert")
        
        if not html_files:
            print("No HTML files found!")
            return False
        
        # Phase 3: Process each HTML file
        converted_files = []
        for html_file in tqdm(html_files, desc="Converting files"):
            if self._process_html_file(html_file):
                converted_files.append(html_file)
        
        print(f"\nConverted {len(converted_files)} files successfully")
        
        # Phase 4: Process images
        print("\nProcessing images...")
        self.image_manager.process_images(self.input_dir)
        
        # Get deduplication stats
        stats = self.image_manager.get_deduplication_stats()
        print(f"Image deduplication stats:")
        print(f"  - Total references: {stats['total_references']}")
        print(f"  - Unique images: {stats['unique_images']}")
        print(f"  - Duplicates removed: {stats['duplicates_removed']}")
        print(f"  - Deduplication ratio: {stats['deduplication_ratio']}")
        
        # Phase 4b: Update markdown files with actual image paths
        print("\nUpdating image paths in markdown files...")
        self._update_image_paths_in_markdown(converted_files)
        
        # Phase 5: Copy non-HTML files
        print("\nCopying non-HTML files...")
        self.file_handler.copy_non_html_files(self.input_dir)
        
        # Phase 6: Cleanup
        print("\nCleaning up...")
        self.image_manager.remove_unreferenced_images()
        self.file_handler.cleanup_empty_directories()
        
        print("\nConversion complete!")
        return True
    
    def _process_html_file(self, html_file):
        """Process a single HTML file."""
        # Read the HTML content
        html_content = self.file_handler.read_file(html_file)
        if html_content is None:
            return False
        
        # Extract metadata
        metadata = self.preprocessor.extract_metadata(html_content)
        
        # Preprocess the HTML
        preprocessed_html = self.preprocessor.preprocess(html_content, html_file)
        
        # Convert to markdown
        markdown_content = self.markdown_converter.convert(preprocessed_html)
        
        # Add title from metadata if available
        if metadata.get('title') and not markdown_content.startswith('#'):
            markdown_content = f"# {metadata['title']}\n\n{markdown_content}"
        
        # Clean up the markdown
        markdown_content = self._clean_markdown(markdown_content)
        
        # Get output path
        output_path = self.path_resolver.get_output_path(html_file)
        
        # Write the markdown file
        return self.file_handler.write_file(markdown_content, output_path)
    
    def _clean_markdown(self, content):
        """Clean up the markdown content."""
        # Remove excessive blank lines
        while '\n\n\n' in content:
            content = content.replace('\n\n\n', '\n\n')
        
        # Ensure single blank line between sections
        content = content.strip() + '\n'
        
        return content
    
    def validate(self):
        """Validate the conversion output."""
        # Initialize validator
        # Static folder is adjacent to output_dir parent
        static_dir = self.output_dir.parent.parent / 'static' / 'img' / self.project_name
        self.validator = OutputValidator(self.output_dir, static_dir)
        
        # Run validation
        return self.validator.validate()
    
    def _update_image_paths_in_markdown(self, converted_files):
        """Update image paths in markdown files after image processing."""
        import re
        
        # Pattern to match markdown images
        img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        
        for html_file in converted_files:
            md_file = self.path_resolver.get_output_path(html_file)
            
            if not md_file.exists():
                continue
            
            # Read the markdown content
            content = self.file_handler.read_file(md_file)
            if not content:
                continue
            
            # Function to replace image paths
            def replace_image_path(match):
                alt_text = match.group(1)
                img_path = match.group(2)
                
                # Skip external images
                if img_path.startswith(('http://', 'https://')):
                    return match.group(0)
                
                # Extract the filename from the path
                filename = Path(img_path).name
                
                # Look up the new path from image manager
                new_path = self.image_manager.get_new_image_path_by_filename(filename)
                if new_path and new_path != img_path:
                    return f'![{alt_text}]({new_path})'
                
                return match.group(0)
            
            # Replace all image paths
            updated_content = re.sub(img_pattern, replace_image_path, content)
            
            # Write back if updated
            if updated_content != content:
                self.file_handler.write_file(updated_content, md_file)