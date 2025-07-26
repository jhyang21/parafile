#!/usr/bin/env python3
"""
Main entry point for Parafile application.

Parafile is an AI-powered file organizer that automatically renames and
categorizes documents based on their content. This module provides the
command-line interface for launching either the GUI configuration interface
or the file monitoring system.

Usage:
    python main.py          # Launch GUI (default)
    python main.py gui      # Launch GUI explicitly
    python main.py monitor  # Start verbose file monitoring

The application supports two main modes:
1. GUI mode: Interactive configuration interface for setting up categories,
   variables, and monitoring folders
2. Monitor mode: Background service that watches for new files and
   automatically organizes them using AI analysis
"""

import sys
import os

# Add src directory to Python path to enable imports from our modules
# This allows the application to find our custom modules regardless of
# the current working directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from gui import main as gui_main
from organizer import main as organizer_main


def main():
    """
    Main entry point for the application.

    Parses command-line arguments and launches the appropriate module:
    - No arguments or 'gui': Launch the configuration GUI
    - 'monitor': Start the file monitoring service
    - Invalid arguments: Show usage information and exit
    """
    # Default behavior: launch GUI if no arguments provided
    if len(sys.argv) == 1:
        gui_main()
    elif len(sys.argv) > 1:
        # Parse the first command-line argument
        command = sys.argv[1].lower()

        if command == "gui":
            gui_main()
        elif command == "monitor":
            organizer_main()
        else:
            # Invalid command provided
            print(f"Error: Unknown command '{sys.argv[1]}'")
            print("Usage: python main.py [gui|monitor]")
            print("  gui     - Launch the configuration GUI (default)")
            print("  monitor - Start file monitoring service")
            sys.exit(1)
    else:
        # This should never happen given the logic above, but included for completeness
        print("Usage: python main.py [gui|monitor]")
        print("  gui     - Launch the configuration GUI")
        print("  monitor - Start file monitoring")


if __name__ == "__main__":
    main()
