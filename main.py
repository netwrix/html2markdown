"""Command-line interface for HTML to Markdown converter."""

import click
import sys
from pathlib import Path
from converter import HtmlToMarkdownConverter


@click.command()
@click.option(
    '--input', '-i',
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help='Input directory containing HTML files'
)
@click.option(
    '--output', '-o',
    required=True,
    type=click.Path(file_okay=False, dir_okay=True),
    help='Output directory for markdown files'
)
@click.option(
    '--validate',
    is_flag=True,
    default=False,
    help='Run validation after conversion'
)
@click.option(
    '--force',
    is_flag=True,
    default=False,
    help='Overwrite output directory if it exists'
)
def convert(input, output, validate, force):
    """Convert HTML documentation to Markdown format.
    
    This tool converts HTML files to Markdown while:
    - Preserving directory structure
    - Moving and deduplicating images
    - Converting all paths to absolute references
    - Applying consistent naming conventions
    """
    # Check if output directory exists
    output_path = Path(output)
    if output_path.exists() and not force:
        click.echo(f"Error: Output directory '{output}' already exists. Use --force to overwrite.")
        sys.exit(1)
    
    # Create converter
    converter = HtmlToMarkdownConverter(input, output)
    
    # Run conversion
    try:
        success = converter.convert()
        if not success:
            click.echo("Conversion failed!")
            sys.exit(1)
    except Exception as e:
        click.echo(f"Error during conversion: {e}")
        sys.exit(1)
    
    # Run validation if requested
    if validate:
        click.echo("\nRunning validation...")
        try:
            valid = converter.validate()
            if not valid:
                click.echo("Validation failed! Check the errors above.")
                sys.exit(1)
            else:
                click.echo("Validation passed!")
        except Exception as e:
            click.echo(f"Error during validation: {e}")
            sys.exit(1)
    
    click.echo("\nConversion completed successfully!")


if __name__ == '__main__':
    convert()