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
        # Check if it's inside a <pre> tag (already a code block)
        if el.parent and el.parent.name == 'pre':
            # This is a pre > code block, handle it as a code block
            lang = el.get('class', '')
            if lang and lang.startswith('language-'):
                lang = lang.replace('language-', '')
            else:
                lang = ''
            return f"```{lang}\n{text}\n```"
        else:
            # All other code tags should be converted to code blocks with triple backticks
            # Even if they're inline in the HTML, convert to code blocks as requested
            return f"```{text}```" if text else ""
    
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
        # Split the text into lines
        lines = text.strip().split('\n')
        if not lines:
            return text
        
        # First, determine the expected number of columns from the header row
        header_cells = lines[0].count('|')
        expected_cols = header_cells - 1 if header_cells > 0 else 0
        
        # Process each line to ensure proper column count
        fixed_lines = []
        for i, line in enumerate(lines):
            if line.strip() == '':
                continue
                
            # Count cells in this line
            cells = line.split('|')
            # Remove empty cells at start and end (markdown table format)
            if cells and cells[0].strip() == '':
                cells = cells[1:]
            if cells and cells[-1].strip() == '':
                cells = cells[:-1]
            
            current_cols = len(cells)
            
            # Check if this is a separator line
            is_separator = all(cell.strip() == '---' or cell.strip() == '' for cell in cells)
            
            if is_separator:
                # Ensure separator has correct number of columns
                if current_cols != expected_cols:
                    separator = '|' + '|'.join(['---'] * expected_cols) + '|'
                    fixed_lines.append(separator)
                else:
                    fixed_lines.append(line)
            else:
                # Regular row - ensure it has the correct number of columns
                if current_cols < expected_cols:
                    # Pad with empty cells
                    cells.extend([''] * (expected_cols - current_cols))
                
                # Reconstruct the line
                fixed_line = '|' + '|'.join(f' {cell.strip()} ' for cell in cells) + '|'
                fixed_lines.append(fixed_line)
        
        # Ensure there's a separator after the header
        if len(fixed_lines) > 1:
            # Check if second line is a separator
            second_line = fixed_lines[1] if len(fixed_lines) > 1 else ''
            cells = second_line.split('|')[1:-1] if '|' in second_line else []
            is_separator = all(cell.strip() == '---' for cell in cells)
            
            if not is_separator:
                # Insert separator after header
                separator = '|' + '|'.join(['---'] * expected_cols) + '|'
                fixed_lines.insert(1, separator)
        
        return '\n' + '\n'.join(fixed_lines) + '\n'
    
    
    def convert_br(self, el, text, parent_tags):
        """Convert br elements."""
        # Use two spaces before newline for markdown line break
        return "  \n"