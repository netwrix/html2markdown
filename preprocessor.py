"""HTML preprocessing for better markdown conversion."""

from bs4 import BeautifulSoup, NavigableString
from pathlib import Path


class HtmlPreprocessor:
    """Preprocesses HTML for optimal markdown conversion."""
    
    def __init__(self, path_resolver, image_manager):
        self.path_resolver = path_resolver
        self.image_manager = image_manager
    
    def preprocess(self, html_content, source_file):
        """Preprocess HTML content before markdown conversion."""
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Extract only the main content
        main_content = soup.find('div', {'role': 'main'})
        if main_content:
            # Create a new soup with just the main content
            new_soup = BeautifulSoup('<html><body></body></html>', 'lxml')
            new_soup.body.append(main_content)
            soup = new_soup
        else:
            # If no main content div found, try to find the body content
            # and remove common navigation elements
            for nav_element in soup.find_all(['nav', 'header', 'footer']):
                nav_element.decompose()
            
            # Remove elements with specific classes or ids that are typically navigation
            for selector in ['.navigation', '.nav', '.header', '.footer', '#navigation', '#nav', '#header', '#footer']:
                for element in soup.select(selector):
                    element.decompose()
        
        # Process all images
        self._process_images(soup, source_file)
        
        # Process all links
        self._process_links(soup, source_file)
        
        # Process code blocks
        self._process_code_blocks(soup)
        
        # Clean up empty elements
        self._clean_empty_elements(soup)
        
        return str(soup)
    
    def _process_images(self, soup, source_file):
        """Process all image tags to update paths."""
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if not src:
                continue
            
            # Skip external images
            if src.startswith(('http://', 'https://')):
                continue
            
            # Add to image manager for tracking with the source file
            self.image_manager.add_image_reference(src, source_file)
            
            # For now, set a placeholder path that will be updated after image processing
            # The actual filename will be determined after deduplication
            filename = Path(src).name
            normalized_filename = filename.lower().replace(' ', '_')
            output_dirname = self.path_resolver.output_dir.name
            placeholder_path = f"/static/img/{output_dirname}/{normalized_filename}"
            
            # Store the original src as a data attribute for later processing
            img['data-original-src'] = src
            img['src'] = placeholder_path
    
    def _process_links(self, soup, source_file):
        """Process all anchor tags to update paths."""
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if not href:
                continue
            
            # Skip external URLs and special links
            if href.startswith(('http://', 'https://', 'mailto:', '#', 'javascript:')):
                continue
            
            # Resolve the path
            resolved_path = self.path_resolver.resolve_path(
                source_file, href, path_type='document'
            )
            
            # Update the href attribute
            link['href'] = resolved_path
    
    def _process_code_blocks(self, soup):
        """Process code blocks for better markdown conversion."""
        # Find all <code> tags
        for code in soup.find_all('code'):
            # Check if it's inside a <pre> tag (already a code block)
            if code.parent and code.parent.name == 'pre':
                continue
            
            # For inline code, we need to ensure proper handling
            # Add a custom attribute to help with conversion
            code['data-inline'] = 'true'
            
        # Process <pre> tags that might contain code
        for pre in soup.find_all('pre'):
            # If pre contains a code tag, it's already properly structured
            if pre.find('code'):
                continue
            
            # Wrap content in code tag for consistent handling
            code_tag = soup.new_tag('code')
            code_tag.string = pre.get_text()
            pre.clear()
            pre.append(code_tag)
    
    def _clean_empty_elements(self, soup):
        """Remove empty elements that could cause issues."""
        # Remove empty paragraphs
        for p in soup.find_all('p'):
            if not p.get_text(strip=True) and not p.find_all(['img', 'a']):
                p.decompose()
        
        # Remove multiple consecutive br tags
        for br in soup.find_all('br'):
            next_sibling = br.next_sibling
            if next_sibling and isinstance(next_sibling, NavigableString):
                if not next_sibling.strip():
                    next_sibling = next_sibling.next_sibling
            
            if next_sibling and next_sibling.name == 'br':
                br.decompose()
    
    def extract_metadata(self, html_content):
        """Extract metadata from HTML if available."""
        soup = BeautifulSoup(html_content, 'lxml')
        metadata = {}
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text(strip=True)
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name', '')
            content = meta.get('content', '')
            if name and content:
                metadata[name] = content
        
        return metadata