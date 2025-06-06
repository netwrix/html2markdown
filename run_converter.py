#!/usr/bin/env python3
"""Run the HTML to Markdown converter."""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the converter
from main import convert

if __name__ == '__main__':
    convert()