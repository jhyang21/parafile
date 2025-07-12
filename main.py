#!/usr/bin/env python3
"""
Main entry point for Parafile application.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui import main as gui_main
from organizer import main as organizer_main

def main():
    """Main entry point for the application."""
    if len(sys.argv) > 1:
        if sys.argv[1] == 'gui':
            gui_main()
        elif sys.argv[1] == 'monitor':
            organizer_main()
        else:
            print("Usage: python main.py [gui|monitor]")
            sys.exit(1)
    else:
        print("Usage: python main.py [gui|monitor]")
        print("  gui     - Launch the configuration GUI")
        print("  monitor - Start file monitoring")

if __name__ == "__main__":
    main() 