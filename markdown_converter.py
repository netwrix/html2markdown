"""Custom markdown converter with specific rules."""

from markdownify import MarkdownConverter as BaseConverter
from markdownify import UNDERSCORE


class CustomMarkdownConverter(BaseConverter):
    """Custom markdown converter with specific conversion rules."""
    
    def __init__(self, **options):
        # Set default options
        options.setdefault('heading_style', 'atx')
        options.setdefault('bullets', '-')
        options.setdefault('strong_em_symbol', UNDERSCORE)
        options.setdefault('code_language', '')
        
        super().__init__(**options)
    
    def convert_code(self, el, text, parent_tags):
        """Convert code elements with triple backticks."""
        # Check if this should be inline based on parent tags
        convert_as_inline = 'p' in parent_tags or 'li' in parent_tags
        
        if el.get('data-inline') == 'true' or convert_as_inline:
            # Inline code with single backticks
            return f"`{text}`" if text else ""
        else:
            # Code block with triple backticks
            # Check if there's a language specified
            lang = el.get('class', '')
            if lang and lang.startswith('language-'):
                lang = lang.replace('language-', '')
            else:
                lang = ''
            
            # Use triple backticks for code blocks
            if '\n' in text or len(text) > 60:
                return f"\n```{lang}\n{text}\n```\n"
            else:
                # Short code without newlines can be inline
                return f"`{text}`"
    
    def convert_pre(self, el, text, parent_tags):
        """Convert pre elements."""
        # If it contains a code element, it will be handled by convert_code
        code_el = el.find('code')
        if code_el:
            # The code element will handle the conversion
            return text
        else:
            # Treat as code block
            return f"\n```\n{text}\n```\n"
    
    def convert_img(self, el, text, parent_tags):
        """Convert image elements."""
        alt = el.get('alt', '')
        src = el.get('src', '')
        title = el.get('title', '')
        
        # Clean up alt text
        if not alt and title:
            alt = title
        elif not alt:
            # Use filename as alt text if nothing else is available
            alt = src.split('/')[-1].split('.')[0] if src else 'image'
        
        # Build the markdown image syntax without title attribute
        return f'![{alt}]({src})'
    
    def convert_a(self, el, text, parent_tags):
        """Convert anchor elements."""
        href = el.get('href', '')
        title = el.get('title', '')
        
        # Handle empty links
        if not href:
            return text
        
        # Handle anchor links - need to generate proper markdown anchors
        if '#' in href:
            # Split the href into path and anchor parts
            if href.startswith('#'):
                # Anchor-only link - generate anchor from link text
                anchor = self._generate_markdown_anchor(text)
                href = f'#{anchor}'
            else:
                # Link with anchor - generate anchor from link text
                path_part, _ = href.split('#', 1)
                anchor = self._generate_markdown_anchor(text)
                href = f'{path_part}#{anchor}'
        
        # Build the markdown link syntax without title attribute
        return f'[{text}]({href})'
    
    def _generate_markdown_anchor(self, text):
        """Generate a markdown-compatible anchor from text."""
        # Convert to lowercase and replace spaces with hyphens
        anchor = text.strip().replace(' ', '-')
        # Remove special characters except hyphens and underscores
        anchor = ''.join(c for c in anchor if c.isalnum() or c in '-_')
        # Remove multiple consecutive hyphens
        while '--' in anchor:
            anchor = anchor.replace('--', '-')
        # Remove leading/trailing hyphens
        anchor = anchor.strip('-')
        return anchor
    
    def convert_table(self, el, text, parent_tags):
        """Convert table elements with proper formatting."""
        # Count columns from the first row
        first_row = el.find('tr')
        if not first_row:
            return text
        
        cols = len(first_row.find_all(['td', 'th']))
        if cols == 0:
            return text
        
        # Create header separator
        header_separator = '|' + '|'.join(['---'] * cols) + '|'
        
        # Process the table content
        lines = text.strip().split('\n')
        if len(lines) > 0:
            # Insert header separator after first row
            lines.insert(1, header_separator)
        
        return '\n' + '\n'.join(lines) + '\n'
    
    def convert_li(self, el, text, parent_tags):
        """Convert list item elements."""
        # Handle nested lists properly
        parent = el.parent
        if parent and parent.name == 'ol':
            # Ordered list - find the item number
            index = 1
            for i, sibling in enumerate(parent.find_all('li')):
                if sibling == el:
                    index = i + 1
                    break
            return f"{index}. {text.strip()}\n"
        else:
            # Unordered list
            return f"- {text.strip()}\n"
    
    def convert_br(self, el, text, parent_tags):
        """Convert br elements."""
        # Use two spaces before newline for markdown line break
        return "  \n"