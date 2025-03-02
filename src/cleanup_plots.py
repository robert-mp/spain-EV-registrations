#!/usr/bin/env python
"""
Plot Directory Cleanup Script
----------------------------

Ensures plots are organized in year/month directories and removes any plots
that don't follow this structure.
"""
import os
import shutil
import logging
from pathlib import Path
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_plots():
    """
    Clean up plots directory:
    1. Remove any plots not in year/month directories
    2. Ensure proper directory structure
    """
    plots_dir = Path('plots')
    
    # Skip if plots directory doesn't exist
    if not plots_dir.exists():
        logger.info("No plots directory found. Nothing to clean up.")
        return
    
    # Get all PNG files in the plots directory
    png_files = list(plots_dir.glob('*.png'))
    
    if png_files:
        logger.info(f"Found {len(png_files)} PNG files in root plots directory")
        
        # Remove PNG files from root plots directory
        for file in png_files:
            try:
                os.remove(file)
                logger.info(f"Removed {file}")
            except Exception as e:
                logger.error(f"Error removing {file}: {str(e)}")
    
    # Clean up any empty directories
    for root, dirs, files in os.walk(plots_dir, topdown=False):
        for name in dirs:
            try:
                dir_path = os.path.join(root, name)
                if not os.listdir(dir_path):  # if directory is empty
                    os.rmdir(dir_path)
                    logger.info(f"Removed empty directory: {dir_path}")
            except Exception as e:
                logger.error(f"Error removing directory {name}: {str(e)}")

def main():
    logger.info("Starting plots directory cleanup")
    cleanup_plots()
    logger.info("Plots directory cleanup completed")

if __name__ == "__main__":
    main() 